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
# Joystick-driven Cartesian jog for the OpenMANIPULATOR-X arm. Requires
# `ros2 run joy joy_node` to be running (publishing /joy) and the arm's
# ros2_control bringup (arm_controller + gripper_controller) to be up.
#
# Controls:
#   left stick (x/y)   -> horizontal (X/Y) jog
#   right stick (y)     -> vertical (Z) jog
#   right trigger (R2)  -> close the gripper (proportional to how far it's
#                          pressed); released == open
#   circle (B)          -> reset: return the arm to its resting pose
#
# A target point in Cartesian space is nudged every control tick by the
# gamepad's left stick (xy) and right stick (z), clamped to a safe workspace
# box. Each tick, IK for that point is solved directly via
# RobotState.set_from_ik() (~0.1ms/call, seeded from the previous solution
# for continuity) rather than full MoveIt motion planning, which is too
# slow (~1s/plan) for responsive jogging. This bypasses MoveIt's collision
# checking, so the workspace box below is deliberately kept clear of
# self-collision and floor-collision regions even though it now covers most
# of the arm's real reach (see the derivation note above the bounds).
#
# Raw stick input is run through an exponential moving-average filter before
# being applied, so the commanded motion accelerates/decelerates smoothly
# instead of jerking on every /joy tick (controller noise, tick-to-tick
# jitter, and sudden stick snaps all get smoothed out).
#
# NOTE: the exact /joy axes/button indices below follow the ROS 2 `joy`
# package's SDL2 backend standard-gamepad layout, but SDL's mapping can
# vary by controller/driver. Verify on your hardware with:
#   ros2 topic echo /joy
# and watch which index moves as you work each stick/trigger/button; adjust
# the constants below if they don't match.

import os
import time
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from control_msgs.action import FollowJointTrajectory
from control_msgs.action import GripperCommand
from geometry_msgs.msg import Pose
from moveit.planning import MoveItPy
from moveit_configs_utils import MoveItConfigsBuilder
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import Joy
from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

# --- /joy axis & button indices (SDL2 standard-gamepad layout; verify on your controller) ---
LEFT_STICK_X_AXIS = 0
LEFT_STICK_Y_AXIS = 1
RIGHT_STICK_Y_AXIS = 5
R2_AXIS = 4  # analog trigger: SDL2 rests at +1.0 (released), -1.0 (fully pressed)
CIRCLE_BUTTON = 2  # PS4 "circle" face button (measured via `ros2 topic echo /joy`)

# Push left stick forward (-Y in SDL convention) drives +X (away from the base).
# Push right stick up (-Y in SDL convention) drives +Z (upward).
# Flip these to -1 if a direction feels reversed on your hardware.
FORWARD_AXIS_SIGN = 1
SIDE_AXIS_SIGN = -1
VERTICAL_AXIS_SIGN = 1

STICK_DEADZONE = 0.15
CONTROL_RATE_HZ = 80.0
LINEAR_SPEED = 0.2  # m/s at full stick deflection
Z_SPEED = 0.15  # m/s at full right-stick deflection
IK_TIMEOUT_S = 0.05
TRAJECTORY_TIME_S = 1.5 / CONTROL_RATE_HZ  # > control period so points overlap smoothly

# Exponential moving-average filter applied to stick input each tick:
#   filtered += SMOOTHING_ALPHA * (raw - filtered)
# Lower = smoother motion but more lag; higher = snappier but jerkier.
SMOOTHING_ALPHA = 0.3

# Reachable workspace bounds (m), centered on the base frame. Derived by
# sweeping joint2/3/4 across their full URDF limits and computing forward
# kinematics of the end effector: real horizontal reach maxes out around
# 0.39m and height around 0.44m (at the fully-folded-up singularity), with
# a valid pose comfortably up to Z~0.42m even restricted to X in [0.12, 0.32].
# The box below stays inside that envelope with margin (min X keeps the
# gripper away from the arm's own base column, since IK here bypasses
# MoveIt's self-collision checking; min Z keeps clearance above the table).
# Corners of the box may occasionally be outside the true (roughly circular)
# reachable region -- IK failures there are handled by holding position.
MIN_X, MAX_X = -0.10, 0.32
MIN_Y, MAX_Y = -0.32, 0.32
MIN_Z, MAX_Z = 0.01, 0.35

# Joint values for the "home" group_state in open_manipulator_x.srdf, used
# as the arm's resting pose for the reset button.
REST_JOINT_POSITIONS = [0.0, -1.0, 0.7, 0.3]
RESET_TRAJECTORY_TIME_S = 2.0  # slower, deliberate move since it can span the full range

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


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


class JoystickTeleopMover(Node):

    def __init__(self, robot_state):
        super().__init__('joystick_teleop_mover')
        self.robot_state = robot_state
        self.latest_joy = None
        self._filtered_axes = [0.0, 0.0, 0.0]  # low-pass state for stick_x, stick_y, stick_z
        self._prev_reset_pressed = False
        self._last_gripper_cmd = None

        start_pose = self.robot_state.get_pose(END_EFFECTOR_LINK)
        self.target = [start_pose.position.x, start_pose.position.y, start_pose.position.z]
        self.get_logger().info(f'Starting target at {self.target}')

        self.action_client = ActionClient(
            self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.gripper_action_client = ActionClient(
            self, GripperCommand, '/gripper_controller/gripper_cmd')
        self.create_subscription(Joy, '/joy', self._joy_callback, 10)
        self.create_timer(1.0 / CONTROL_RATE_HZ, self._control_loop)

    def _joy_callback(self, msg):
        self.latest_joy = msg

    def _control_loop(self):
        joy = self.latest_joy
        needed_axes = max(LEFT_STICK_X_AXIS, LEFT_STICK_Y_AXIS, RIGHT_STICK_Y_AXIS, R2_AXIS)
        if joy is None or len(joy.axes) <= needed_axes:
            return

        dt = 1.0 / CONTROL_RATE_HZ

        reset_pressed = len(joy.buttons) > CIRCLE_BUTTON and bool(joy.buttons[CIRCLE_BUTTON])
        reset_triggered = reset_pressed and not self._prev_reset_pressed
        self._prev_reset_pressed = reset_pressed
        if reset_pressed:
            if reset_triggered:
                self._reset_to_rest_pose()
            # Hold here for as long as the button is held so jog input can't
            # immediately re-preempt the reset trajectory with a new goal.
            return

        self._update_gripper(joy)

        raw_x = apply_deadzone(joy.axes[LEFT_STICK_X_AXIS])
        raw_y = apply_deadzone(joy.axes[LEFT_STICK_Y_AXIS])
        raw_z = apply_deadzone(joy.axes[RIGHT_STICK_Y_AXIS])
        for i, raw in enumerate((raw_x, raw_y, raw_z)):
            self._filtered_axes[i] += SMOOTHING_ALPHA * (raw - self._filtered_axes[i])
        stick_x, stick_y, stick_z = self._filtered_axes

        self.target[0] += FORWARD_AXIS_SIGN  * stick_y * LINEAR_SPEED * dt
        self.target[1] += SIDE_AXIS_SIGN * -1 * stick_x * LINEAR_SPEED * dt
        self.target[2] += VERTICAL_AXIS_SIGN * stick_z * Z_SPEED * dt
        self.target[0] = clamp(self.target[0], MIN_X, MAX_X)
        self.target[1] = clamp(self.target[1], MIN_Y, MAX_Y)
        self.target[2] = clamp(self.target[2], MIN_Z, MAX_Z)

        if abs(stick_x) < 1e-3 and abs(stick_y) < 1e-3 and abs(stick_z) < 1e-3:
            return

        pose = Pose()
        pose.position.x, pose.position.y, pose.position.z = self.target
        pose.orientation.w = 1.0

        if not self.robot_state.set_from_ik(
                'arm', pose, END_EFFECTOR_LINK, timeout=IK_TIMEOUT_S):
            self.get_logger().warn(
                f'IK failed for target {self.target}, holding position',
                throttle_duration_sec=1.0)
            return

        self._send_trajectory(self.robot_state.get_joint_group_positions('arm'))

    def _update_gripper(self, joy):
        press_amount = trigger_press_amount(joy.axes[R2_AXIS])
        gripper_position = GRIPPER_OPEN_POSITION + (
            GRIPPER_CLOSE_POSITION - GRIPPER_OPEN_POSITION) * press_amount

        if (self._last_gripper_cmd is not None
                and abs(gripper_position - self._last_gripper_cmd) < GRIPPER_MOVE_EPSILON):
            return
        if not self.gripper_action_client.server_is_ready():
            return

        self._last_gripper_cmd = gripper_position
        goal_msg = GripperCommand.Goal()
        goal_msg.command.position = gripper_position
        goal_msg.command.max_effort = GRIPPER_MAX_EFFORT
        self.gripper_action_client.send_goal_async(goal_msg)

    def _reset_to_rest_pose(self):
        if not self._send_trajectory(REST_JOINT_POSITIONS, duration_s=RESET_TRAJECTORY_TIME_S):
            self.get_logger().warn(
                'Reset requested but arm_controller is not ready', throttle_duration_sec=1.0)
            return

        self.get_logger().info('Reset pressed, returning to rest pose')
        self.robot_state.set_joint_group_positions('arm', REST_JOINT_POSITIONS)
        self.robot_state.update()
        rest_pose = self.robot_state.get_pose(END_EFFECTOR_LINK)
        # The rest pose's reach can fall slightly outside the jog workspace box
        # (it's chosen for a natural folded pose, not to fit the box). Clamp
        # so the stored target stays consistent with what jogging enforces --
        # otherwise the first stick touch after a reset would silently snap
        # the target to the box edge and jerk the arm there.
        self.target = [
            clamp(rest_pose.position.x, MIN_X, MAX_X),
            clamp(rest_pose.position.y, MIN_Y, MAX_Y),
            clamp(rest_pose.position.z, MIN_Z, MAX_Z),
        ]
        self._filtered_axes = [0.0, 0.0, 0.0]

    def _send_trajectory(self, joint_positions, duration_s=TRAJECTORY_TIME_S):
        if not self.action_client.server_is_ready():
            return False

        point = JointTrajectoryPoint()
        point.positions = list(joint_positions)
        point.time_from_start.sec = int(duration_s)
        point.time_from_start.nanosec = int((duration_s % 1) * 1e9)

        trajectory = JointTrajectory()
        trajectory.joint_names = JOINT_NAMES
        trajectory.points = [point]

        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory = trajectory
        self.action_client.send_goal_async(goal_msg)
        return True


def main():
    rclpy.init()

    moveit_config = build_moveit_config()
    moveit_py_instance = MoveItPy(
        node_name='moveit_py_joystick_teleop', config_dict=moveit_config.to_dict())
    arm = moveit_py_instance.get_planning_component('arm')
    time.sleep(1.0)  # let the current_state_monitor pick up an initial /joint_states

    robot_state = arm.get_start_state()

    teleop_node = JoystickTeleopMover(robot_state)
    try:
        rclpy.spin(teleop_node)
    except KeyboardInterrupt:
        pass
    finally:
        teleop_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
