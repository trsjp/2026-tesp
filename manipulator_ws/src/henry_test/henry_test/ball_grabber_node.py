# Copyright 2024 ROBOTIS CO., LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ball_grabber_node: joystick teleop (copied from
# moveit_py_joystick_teleop_ik_guarded.py) plus two automatic pick-and-place
# sequences, "grab" and "dunk", triggered by receiving a target position on a
# topic. Requires `ros2 run joy joy_node` (publishing /joy) and the arm's
# ros2_control bringup (arm_controller + gripper_controller) to be up.
#
# Differences from the base teleop script:
#  - Manual jog (the sticks) is unchanged from the base script: IK is solved
#    for xyz position only (3 variables), orientation left as identity so the
#    wrist is free to take whatever the solver finds easiest.
#  - Automatic moves (grab/dunk legs, rehome, and the CROSS/SQUARE/TRIANGLE
#    test moves) additionally constrain orientation via an end-effector pitch
#    angle (self.ee_angle) on top of the xyz target, so the gripper approaches
#    at a fixed tilt (e.g. down at -45deg to grab, level at 0deg to dunk).
#    Target orientation is yaw-to-face-the-target (atan2 of the candidate xy,
#    same "point radially outward from the base" convention the polar jog
#    uses) combined with that pitch -- see quaternion_from_euler() below.
#    ASSUMPTION: sign/axis convention of "pitch" here is a guess (positive
#    pitch = ? direction) -- verify on hardware and flip GRAB/DUNK_EE_ANGLE_DEG
#    if the gripper tilts the wrong way.
#  - R2 no longer proportionally opens/closes the gripper -- a press now
#    toggles it open<->closed (self.grabber_open).
#  - Receiving a Point on grab_ball_position or dunk_ball_position starts an
#    automatic sequence: publish <kind>_ball_complete=False, ensure the
#    gripper is in the right starting state, move to the received position
#    (xyz + the fixed grab/dunk pitch), actuate the gripper, move back to
#    rest_position, then publish <kind>_ball_complete=True. Teleop jog input
#    is ignored for the duration (see STATE_TELEOP guard in _control_loop).
#  - CIRCLE always rehomes: pressing it immediately aborts whatever is in
#    progress (a grab/dunk sequence or a test move -- the sequence's
#    <kind>_ball_complete stays False, since it never finished) and moves the
#    arm straight to rest_position, regardless of current state.
#  - SQUARE/TRIANGLE run the full grab/dunk protocol (same steps as
#    receiving a message on grab_ball_position/dunk_ball_position) against
#    the saved test_grab_position/test_dunk_position, instead of just moving
#    there -- handy for exercising the whole sequence without a perception
#    stack publishing real ball positions.
#  - Every automatic move in this file -- the grab/dunk legs, "move to rest",
#    and the CROSS test move -- works by nudging the single
#    self.target/self.ee_angle a bounded step per control tick and
#    re-solving IK, same as the base script's jog loop. Nothing jumps
#    straight to a goal or issues a multi-point/action trajectory, so the arm
#    never jerks between positions.
#  - Button/DPAD actions log via warn() rather than info() so they're
#    visible over MoveIt's own very chatty INFO-level kinematics logging
#    (e.g. the KDL plugin logs an INFO line on every position-only IK solve
#    -- i.e. every jog tick during teleop). If warn() still gets lost, raise
#    that specific logger's level, e.g.
#    `--ros-args --log-level moveit_kinematics_kdl_kinematics_plugin:=warn`
#    (name may need adjusting to match what you actually see).
#
# Controls:
#   left stick (x)      -> rotate target about the base (Z axis, yaw)
#   left stick (y)      -> radial (in/out from the base) jog
#   right stick (y)      -> vertical (Z) jog
#   right trigger (R2)  -> toggle gripper open/closed (edge-triggered)
#   circle               -> abort whatever's in progress and rehome
#   dpad x < -0.5        -> save rest_position = current target + ee_angle
#   dpad y < -0.5         -> save test_grab_position = current target + ee_angle
#   dpad x > 0.5          -> save test_dunk_position = current target + ee_angle
#   cross                -> move to rest_position
#   square                -> run the full grab protocol at test_grab_position (if saved)
#   triangle              -> run the full dunk protocol at test_dunk_position (if saved)
#
# NOTE: the exact /joy axes/button indices below follow the ROS 2 `joy`
# package's SDL2 backend standard-gamepad layout, but SDL's mapping can vary
# by controller/driver, and the DPAD "down"/"left"/"up" labels above are
# taken as specified rather than verified against a physical pad. Confirm on
# your hardware with `ros2 topic echo /joy` and adjust the constants/signs
# below if they don't match.

import math
import os
import time
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from control_msgs.action import GripperCommand
from geometry_msgs.msg import Point
from geometry_msgs.msg import Pose
from moveit.planning import MoveItPy
from moveit_configs_utils import MoveItConfigsBuilder
import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool
from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

# Linux Joy mapping for wired PS4 controller
# Axes
LEFT_STICK_X_AXIS = 0
LEFT_STICK_Y_AXIS = 1
L2_AXIS = 2
RIGHT_STICK_X_AXIS = 3
RIGHT_STICK_Y_AXIS = 4
R2_AXIS = 5  # analog trigger: SDL2 rests at +1.0 (released), -1.0 (fully pressed)
DPAD_X_AXIS = 6
DPAD_Y_AXIS = 7

# Buttons
CROSS_BUTTON = 0
CIRCLE_BUTTON = 1
TRIANGLE_BUTTON = 2
SQUARE_BUTTON = 3
LEFT_BUMPER = 4
RIGHT_BUMPER = 5

# Push left stick forward (-Y in SDL convention) drives the target radially
# outward (away from the base).
# Push right stick up (-Y in SDL convention) drives +Z (upward).
# Push left stick left/right (X) rotates the target about the base (+yaw).
# Flip these to -1 if a direction feels reversed on your hardware.
FORWARD_AXIS_SIGN = 1
SIDE_AXIS_SIGN = -1
VERTICAL_AXIS_SIGN = 1

STICK_DEADZONE = 0.15
CONTROL_RATE_HZ = 500.0
LINEAR_SPEED = 0.2  # m/s at full stick deflection
Z_SPEED = 0.3  # m/s at full right-stick deflection
ANGULAR_SPEED = 1.5  # rad/s at full left-stick-x deflection, about the base Z axis
TRAJECTORY_TIME_S = 1.5 / CONTROL_RATE_HZ  # > control period so points overlap smoothly

# See moveit_py_joystick_teleop_ik_guarded.py for the rationale behind these
# two -- short IK timeout seeded from the previous tick's solution, and a
# per-tick joint-step cap to reject IK jumping to a different arm
# configuration near a singularity.
IK_TIMEOUT_S = 0.002
MAX_JOINT_STEP_RAD = 0.1

# Exponential moving-average filter applied to jog stick input each tick:
#   filtered += SMOOTHING_ALPHA * (raw - filtered)
SMOOTHING_ALPHA = 0.3

# Speeds used for every *automatic* single-target move (grab/dunk legs, move
# to rest, test moves) -- deliberately slower than the max jog speed above
# since these run unattended with no operator watching for trouble.
AUTO_MOVE_LINEAR_SPEED = 0.15  # m/s
AUTO_MOVE_ANGULAR_SPEED = math.radians(90.0)  # rad/s, for ee_angle

# Fixed end-effector pitch commanded during each pick leg (see the "IK uses
# an extra angle" note at the top of the file for the sign caveat).
GRAB_EE_ANGLE_DEG = -45.0
DUNK_EE_ANGLE_DEG = 0.0
REST_EE_ANGLE_DEG = 0.0  # default rest_position pitch, used before anything is saved over it
GRAB_EE_ANGLE_RAD = math.radians(GRAB_EE_ANGLE_DEG)
DUNK_EE_ANGLE_RAD = math.radians(DUNK_EE_ANGLE_DEG)
REST_EE_ANGLE_RAD = math.radians(REST_EE_ANGLE_DEG)

# How long to hold after commanding the gripper open/closed before moving on
# to the next step of a sequence -- the gripper action isn't awaited for
# completion, just given a fixed settle time.
GRIPPER_ACTUATION_WAIT_S = 0.5

# R2 press fraction (0=released, 1=fully pressed) treated as "pressed" for
# the open/closed toggle.
TRIGGER_TOGGLE_THRESHOLD = 0.5
DPAD_THRESHOLD = 0.5

# Gripper positions (m) matching the "open"/"close" group_states in
# open_manipulator_x.srdf (joint limits are -0.011 to 0.02).
GRIPPER_OPEN_POSITION = 0.019
GRIPPER_CLOSE_POSITION = -0.01
# NOTE: placeholder effort -- not verified against the real OpenMANIPULATOR-X
# gripper's torque spec. Confirm before gripping anything fragile.
GRIPPER_MAX_EFFORT = 5.0
GRIPPER_MOVE_EPSILON = 0.001  # skip re-sending near-identical gripper goals

END_EFFECTOR_LINK = 'end_effector_link'
JOINT_NAMES = ['joint1', 'joint2', 'joint3', 'joint4']

GRAB_BALL_POSITION_TOPIC = 'grab_ball_position'
DUNK_BALL_POSITION_TOPIC = 'dunk_ball_position'
GRAB_BALL_COMPLETE_TOPIC = 'grab_ball_complete'
DUNK_BALL_COMPLETE_TOPIC = 'dunk_ball_complete'
# The arm_controller's live joint-trajectory command topic -- this is the
# "arm_trajectory" output named in the node spec, published the same way
# (streamed single-point trajectories) as the base teleop script.
ARM_TRAJECTORY_TOPIC = '/arm_controller/joint_trajectory'

STATE_TELEOP = 'teleop'
STATE_WAIT_GRIPPER = 'wait_gripper'
STATE_MOVING = 'moving'


def build_moveit_config():
    return (
        MoveItConfigsBuilder(
            'open_manipulator_x', package_name='open_manipulator_moveit_config')
        .robot_description_semantic(
            str(Path('config') / 'open_manipulator_x' / 'open_manipulator_x.srdf'))
        .joint_limits(str(Path('config') / 'open_manipulator_x' / 'joint_limits.yaml'))
        .trajectory_execution(
            str(Path('config') / 'open_manipulator_x' / 'moveit_controllers.yaml'))
        .robot_description_kinematics(
            str(Path('config') / 'open_manipulator_x' / 'kinematics.yaml'))
        .planning_pipelines(pipelines=['ompl'])
        .moveit_cpp(
            file_path=os.path.join(
                get_package_share_directory('henry_test'), 'config', 'moveit_cpp.yaml'))
        .to_moveit_configs()
    )


def apply_deadzone(value, deadzone=STICK_DEADZONE):
    if abs(value) < deadzone:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - deadzone) / (1.0 - deadzone)


def trigger_press_amount(axis_value):
    return max(0.0, min(1.0, (1.0 - axis_value) / 2.0))


def max_abs_diff(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def step_vector_toward(current, destination, max_step):
    diff = [d - c for c, d in zip(current, destination)]
    dist = math.sqrt(sum(d * d for d in diff))
    if dist <= max_step or dist < 1e-9:
        return list(destination), True
    scale = max_step / dist
    return [c + d * scale for c, d in zip(current, diff)], False


def step_scalar_toward(current, destination, max_step):
    diff = destination - current
    if abs(diff) <= max_step:
        return destination, True
    return current + math.copysign(max_step, diff), False


def quaternion_from_euler(roll, pitch, yaw):
    # Standard ZYX intrinsic Euler -> quaternion (x, y, z, w), same convention as tf's default.
    cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return x, y, z, w


class BallGrabberNode(Node):

    def __init__(self, robot_state):
        super().__init__('ball_grabber_node')
        self.robot_state = robot_state
        self.latest_joy = None
        self._filtered_axes = [0.0, 0.0, 0.0]  # low-pass state for stick_x, stick_y, stick_z
        self._last_gripper_cmd = None
        self.grabber_open = True  # assumes the gripper starts open -- verify against hardware

        self._prev_r2_pressed = False
        self._prev_circle_pressed = False
        self._prev_cross_pressed = False
        self._prev_square_pressed = False
        self._prev_triangle_pressed = False
        self._prev_dpad_y_down = False
        self._prev_dpad_y_up = False
        self._prev_dpad_x_left = False

        start_pose = self.robot_state.get_pose(END_EFFECTOR_LINK)
        self.target = [start_pose.position.x, start_pose.position.y, start_pose.position.z]
        self.ee_angle = REST_EE_ANGLE_RAD
        # Extra variables from the spec -- rest_position defaults to the
        # arm's initial position/angle; the test positions start unset.
        self.rest_position = list(self.target) + [self.ee_angle]
        self.test_grab_position = None
        self.test_dunk_position = None
        self.get_logger().info(
            f'Starting target at {self.target}, rest_position={self.rest_position}')

        self.state = STATE_TELEOP
        self._move_destination = None
        self._move_destination_angle = None
        self._on_move_complete = None
        self._wait_until = None
        self._on_wait_complete = None

        self.gripper_action_client = ActionClient(
            self, GripperCommand, '/gripper_controller/gripper_cmd')
        # Every move (jog and automatic) streams single-point trajectories to
        # the controller's command topic at control-loop rate -- see the
        # module docstring for why this replaces action-goal-based moves.
        self.trajectory_pub = self.create_publisher(JointTrajectory, ARM_TRAJECTORY_TOPIC, 10)
        self.grab_ball_complete_pub = self.create_publisher(Bool, GRAB_BALL_COMPLETE_TOPIC, 10)
        self.dunk_ball_complete_pub = self.create_publisher(Bool, DUNK_BALL_COMPLETE_TOPIC, 10)

        self.create_subscription(Joy, '/joy', self._joy_callback, 10)
        self.create_subscription(
            Point, GRAB_BALL_POSITION_TOPIC, self._grab_ball_position_callback, 10)
        self.create_subscription(
            Point, DUNK_BALL_POSITION_TOPIC, self._dunk_ball_position_callback, 10)
        self.create_timer(1.0 / CONTROL_RATE_HZ, self._control_loop)

    def _joy_callback(self, msg):
        self.latest_joy = msg

    # -- Top-level control loop -------------------------------------------------

    def _control_loop(self):
        # Checked unconditionally, ahead of the state dispatch below, so
        # circle rehomes/aborts no matter what's currently running (a
        # grab/dunk sequence, a gripper wait, a test move, or plain teleop).
        self._check_rehome_button()

        if self.state == STATE_TELEOP:
            self._tick_teleop()
        elif self.state == STATE_WAIT_GRIPPER:
            self._tick_wait_gripper()
        elif self.state == STATE_MOVING:
            self._tick_moving()

    def _check_rehome_button(self):
        joy = self.latest_joy
        if joy is None or len(joy.buttons) <= CIRCLE_BUTTON:
            return

        circle_pressed = bool(joy.buttons[CIRCLE_BUTTON])
        if circle_pressed and not self._prev_circle_pressed:
            self._abort_and_rehome()
        self._prev_circle_pressed = circle_pressed

    def _abort_and_rehome(self):
        # Drop any pending gripper-wait/move callback so an in-progress
        # grab/dunk sequence or test move can't resume after this -- its
        # <kind>_ball_complete (if any) is left False, since it never
        # finished.
        # Uses warn() (not info()) so this is visible over MoveIt's own very
        # chatty INFO-level kinematics logging (e.g. the KDL plugin logs an
        # INFO line on every position-only IK solve, i.e. every jog tick).
        self.get_logger().warn('CIRCLE pressed: aborting and rehoming')
        self._on_wait_complete = None
        self._wait_until = None
        self._on_move_complete = None

        def after_rehome():
            self.state = STATE_TELEOP
            self._filtered_axes = [0.0, 0.0, 0.0]

        self._start_move_then(self.rest_position[:3], self.rest_position[3], after_rehome)

    # -- Teleop ------------------------------------------------------------------

    def _tick_teleop(self):
        joy = self.latest_joy
        needed_axes = max(
            LEFT_STICK_X_AXIS, LEFT_STICK_Y_AXIS, RIGHT_STICK_Y_AXIS, R2_AXIS,
            DPAD_X_AXIS, DPAD_Y_AXIS)
        if joy is None or len(joy.axes) <= needed_axes:
            # This should also catch the buttons, so deleted extra button safety
            return

        self._handle_r2_toggle(joy)
        self._handle_dpad_saves(joy)
        if self._handle_test_move_buttons(joy):
            # A test move was just kicked off (state is now STATE_MOVING) --
            # don't also apply this tick's stick input on top of it.
            return

        dt = 1.0 / CONTROL_RATE_HZ

        raw_x = apply_deadzone(joy.axes[LEFT_STICK_X_AXIS])
        # overwrite x if LB or RB:
        if bool(joy.buttons[LEFT_BUMPER]) or bool(joy.buttons[RIGHT_BUMPER]):
            raw_x = joy.buttons[LEFT_BUMPER] + -1 * joy.buttons[RIGHT_BUMPER]

        raw_y = apply_deadzone(joy.axes[LEFT_STICK_Y_AXIS])
        raw_z = apply_deadzone(joy.axes[RIGHT_STICK_Y_AXIS])
        for i, raw in enumerate((raw_x, raw_y, raw_z)):
            self._filtered_axes[i] += SMOOTHING_ALPHA * (raw - self._filtered_axes[i])
        stick_x, stick_y, stick_z = self._filtered_axes

        if abs(stick_x) < 1e-3 and abs(stick_y) < 1e-3 and abs(stick_z) < 1e-3:
            return

        candidate = list(self.target)
        candidate[2] += VERTICAL_AXIS_SIGN * stick_z * Z_SPEED * dt

        x, y = candidate[0], candidate[1]
        radius = math.hypot(x, y)
        dir_x, dir_y = (x / radius, y / radius) if radius > 1e-6 else (1.0, 0.0)
        radius = max(0.0, radius + FORWARD_AXIS_SIGN * stick_y * LINEAR_SPEED * dt)
        x, y = radius * dir_x, radius * dir_y

        d_theta = SIDE_AXIS_SIGN * -1 * stick_x * ANGULAR_SPEED * dt
        cos_t, sin_t = math.cos(d_theta), math.sin(d_theta)
        candidate[0] = cos_t * x - sin_t * y
        candidate[1] = sin_t * x + cos_t * y

        # Manual jog does not constrain orientation at all -- IK is solved
        # for the xyz candidate only (3 variables), same as the base
        # teleop script, leaving the wrist free. ee_angle is not read or
        # updated here; it only matters for the automatic moves below.
        self._try_commit_target(candidate, constrain_orientation=False)

    def _handle_r2_toggle(self, joy):
        r2_pressed = trigger_press_amount(joy.axes[R2_AXIS]) > TRIGGER_TOGGLE_THRESHOLD
        if r2_pressed and not self._prev_r2_pressed:
            new_open = not self.grabber_open
            self.get_logger().warn(
                f'R2 pressed: toggling gripper to {"open" if new_open else "closed"}')
            self._set_gripper(new_open)
        self._prev_r2_pressed = r2_pressed

    def _handle_dpad_saves(self, joy):
        dpad_y_down = joy.axes[DPAD_Y_AXIS] < -DPAD_THRESHOLD
        dpad_y_up = joy.axes[DPAD_Y_AXIS] > DPAD_THRESHOLD
        dpad_x_left = joy.axes[DPAD_X_AXIS] > DPAD_THRESHOLD

        if dpad_y_down and not self._prev_dpad_y_down:
            self.rest_position = list(self.target) + [self.ee_angle]
            self.get_logger().warn(
                f'DPAD-X-down pressed: set rest_position = {self.rest_position}')
        self._prev_dpad_y_down = dpad_y_down

        if dpad_x_left and not self._prev_dpad_x_left:
            self.test_grab_position = list(self.target) + [self.ee_angle]
            self.get_logger().warn(
                f'DPAD-Y-left pressed: set test_grab_position = {self.test_grab_position}')
        self._prev_dpad_x_left = dpad_x_left

        if dpad_y_up and not self._prev_dpad_y_up:
            self.test_dunk_position = list(self.target) + [self.ee_angle]
            self.get_logger().warn(
                f'DPAD-X-up pressed: set test_dunk_position = {self.test_dunk_position}')
        self._prev_dpad_y_up = dpad_y_up

    def _handle_test_move_buttons(self, joy):
        # SQUARE/TRIANGLE run the *entire* grab/dunk protocol (ensure
        # gripper state, move to the saved test position at the fixed
        # grab/dunk pitch, actuate the gripper, return to rest, publish
        # complete) against the saved test position, exactly like a message
        # on grab_ball_position/dunk_ball_position would. CROSS just moves to
        # rest_position, no gripper actions.
        started = False

        cross_pressed = bool(joy.buttons[CROSS_BUTTON])
        if cross_pressed and not self._prev_cross_pressed:
            self.get_logger().warn(f'CROSS pressed: moving to rest_position {self.rest_position}')
            self._start_test_move(self.rest_position)
            started = True
        self._prev_cross_pressed = cross_pressed

        square_pressed = bool(joy.buttons[SQUARE_BUTTON])
        if square_pressed and not self._prev_square_pressed:
            if self.test_grab_position is None:
                self.get_logger().warn(
                    'SQUARE pressed: test_grab_position not saved yet '
                    '(dpad-y-left first), ignoring', throttle_duration_sec=1.0)
            else:
                self.get_logger().warn(
                    f'SQUARE pressed: running full grab protocol at test_grab_position '
                    f'{self.test_grab_position}')
                self._start_pick_sequence('grab', self.test_grab_position[:3])
                started = True
        self._prev_square_pressed = square_pressed

        triangle_pressed = bool(joy.buttons[TRIANGLE_BUTTON])
        if triangle_pressed and not self._prev_triangle_pressed:
            if self.test_dunk_position is None:
                self.get_logger().warn(
                    'TRIANGLE pressed: test_dunk_position not saved yet '
                    '(dpad-x-up first), ignoring', throttle_duration_sec=1.0)
            else:
                self.get_logger().warn(
                    f'TRIANGLE pressed: running full dunk protocol at test_dunk_position '
                    f'{self.test_dunk_position}')
                self._start_pick_sequence('dunk', self.test_dunk_position[:3])
                started = True
        self._prev_triangle_pressed = triangle_pressed

        return started

    def _start_test_move(self, position_and_angle):
        def after():
            self.state = STATE_TELEOP
            self._filtered_axes = [0.0, 0.0, 0.0]

        self._start_move_then(position_and_angle[:3], position_and_angle[3], after)

    # -- Shared IK-guarded target commit ------------------------------------------

    def _try_commit_target(self, candidate, constrain_orientation=True):
        pose = Pose()
        pose.position.x, pose.position.y, pose.position.z = candidate

        if constrain_orientation:
            # Orientation: yaw points the end effector radially outward from
            # the base toward the candidate (same convention the polar jog
            # above uses), pitch is the separately-tracked ee_angle.
            yaw = math.atan2(candidate[1], candidate[0])
            qx, qy, qz, qw = quaternion_from_euler(0.0, self.ee_angle, yaw)
            pose.orientation.x, pose.orientation.y, pose.orientation.z = qx, qy, qz
            pose.orientation.w = qw
        else:
            # Free orientation (3-variable IK, position only) -- used by
            # manual teleop jogging, same as the base script.
            pose.orientation.w = 1.0

        prev_joint_positions = list(self.robot_state.get_joint_group_positions('arm'))

        if not self.robot_state.set_from_ik(
                'arm', pose, END_EFFECTOR_LINK, timeout=IK_TIMEOUT_S):
            self.robot_state.set_joint_group_positions('arm', prev_joint_positions)
            self.robot_state.update()
            self.get_logger().warn(
                f'IK could not reach candidate target {candidate} within '
                f'{IK_TIMEOUT_S * 1000:.1f}ms, holding position',
                throttle_duration_sec=1.0)
            return False

        new_joint_positions = list(self.robot_state.get_joint_group_positions('arm'))
        joint_step = max_abs_diff(new_joint_positions, prev_joint_positions)
        if joint_step > MAX_JOINT_STEP_RAD:
            self.robot_state.set_joint_group_positions('arm', prev_joint_positions)
            self.robot_state.update()
            self.get_logger().warn(
                f'Rejected discontinuous IK solution for candidate target '
                f'{candidate} (max joint step {joint_step:.3f}rad > '
                f'{MAX_JOINT_STEP_RAD}rad, likely a singularity), holding position',
                throttle_duration_sec=1.0)
            return False

        self.target = candidate
        self._publish_jog_trajectory(new_joint_positions)
        return True

    # -- Single-target automatic moves --------------------------------------------

    def _start_move_then(self, destination_xyz, destination_angle, next_callback):
        self._move_destination = list(destination_xyz)
        self._move_destination_angle = destination_angle
        self._on_move_complete = next_callback
        self.state = STATE_MOVING

    def _tick_moving(self):
        dt = 1.0 / CONTROL_RATE_HZ
        candidate, pos_arrived = step_vector_toward(
            self.target, self._move_destination, AUTO_MOVE_LINEAR_SPEED * dt)
        prev_angle = self.ee_angle
        self.ee_angle, angle_arrived = step_scalar_toward(
            self.ee_angle, self._move_destination_angle, AUTO_MOVE_ANGULAR_SPEED * dt)

        if not self._try_commit_target(candidate):
            self.ee_angle = prev_angle  # keep angle/target in sync -- neither committed this tick
            return

        if pos_arrived and angle_arrived:
            callback = self._on_move_complete
            self._on_move_complete = None
            self._move_destination = None
            self._move_destination_angle = None
            callback()

    # -- Gripper -------------------------------------------------------------------

    def _set_gripper(self, open_):
        self.grabber_open = open_
        position = GRIPPER_OPEN_POSITION if open_ else GRIPPER_CLOSE_POSITION

        if (self._last_gripper_cmd is not None
                and abs(position - self._last_gripper_cmd) < GRIPPER_MOVE_EPSILON):
            return
        if not self.gripper_action_client.server_is_ready():
            self.get_logger().warn(
                'Gripper action server not ready, cannot send gripper command',
                throttle_duration_sec=1.0)
            return

        self._last_gripper_cmd = position
        goal_msg = GripperCommand.Goal()
        goal_msg.command.position = position
        goal_msg.command.max_effort = GRIPPER_MAX_EFFORT
        self.gripper_action_client.send_goal_async(goal_msg)

    def _start_gripper_then(self, open_, next_callback):
        self._set_gripper(open_)
        self._wait_until = self.get_clock().now() + Duration(seconds=GRIPPER_ACTUATION_WAIT_S)
        self._on_wait_complete = next_callback
        self.state = STATE_WAIT_GRIPPER

    def _tick_wait_gripper(self):
        if self.get_clock().now() >= self._wait_until:
            callback = self._on_wait_complete
            self._on_wait_complete = None
            self._wait_until = None
            callback()

    # -- grab_ball_position / dunk_ball_position sequences ---------------------------

    def _grab_ball_position_callback(self, msg):
        self._start_pick_sequence('grab', [msg.x, msg.y, msg.z])

    def _dunk_ball_position_callback(self, msg):
        self._start_pick_sequence('dunk', [msg.x, msg.y, msg.z])

    def _start_pick_sequence(self, kind, position_xyz):
        if self.state != STATE_TELEOP:
            self.get_logger().warn(
                f'Ignoring new {kind}_ball_position, still busy with a previous sequence',
                throttle_duration_sec=1.0)
            return

        self.get_logger().warn(f'Starting {kind} sequence, target {position_xyz}')
        complete_pub = (
            self.grab_ball_complete_pub if kind == 'grab' else self.dunk_ball_complete_pub)
        complete_pub.publish(Bool(data=False))

        ee_angle = GRAB_EE_ANGLE_RAD if kind == 'grab' else DUNK_EE_ANGLE_RAD
        # grab starts with the gripper open (ready to close on the ball);
        # dunk starts with it closed (holding the ball, ready to release it).
        ensure_open = (kind == 'grab')

        def after_actuate():
            def after_rest():
                complete_pub.publish(Bool(data=True))
                self.get_logger().warn(f'{kind} sequence complete')
                self.state = STATE_TELEOP
                self._filtered_axes = [0.0, 0.0, 0.0]

            self._start_move_then(self.rest_position[:3], self.rest_position[3], after_rest)

        def after_move_to_target():
            self._start_gripper_then(not ensure_open, after_actuate)

        def after_ensure_gripper():
            self._start_move_then(position_xyz, ee_angle, after_move_to_target)

        self._start_gripper_then(ensure_open, after_ensure_gripper)

    # -- Trajectory publishing -------------------------------------------------------

    def _build_trajectory(self, joint_positions, duration_s):
        point = JointTrajectoryPoint()
        point.positions = list(joint_positions)
        point.time_from_start.sec = int(duration_s)
        point.time_from_start.nanosec = int((duration_s % 1) * 1e9)

        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES
        trajectory.points = [point]
        return trajectory

    def _publish_jog_trajectory(self, joint_positions, duration_s=TRAJECTORY_TIME_S):
        self.trajectory_pub.publish(self._build_trajectory(joint_positions, duration_s))


def main():
    rclpy.init()

    moveit_config = build_moveit_config()
    moveit_py_instance = MoveItPy(
        node_name='ball_grabber_moveit_py', config_dict=moveit_config.to_dict())
    arm = moveit_py_instance.get_planning_component('arm')
    time.sleep(1.0)  # let the current_state_monitor pick up an initial /joint_states

    robot_state = arm.get_start_state()

    node = BallGrabberNode(robot_state)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
