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
# x_arm_mover: moves the arm to whatever position is published on
# /arm_target_pos, using MoveIt's "arm" planning group (position-only goal,
# orientation left free -- same approach as moveit_py_random_mover.py).
# /arm_move_success is set to False as soon as a new target is accepted, and
# back to True once the resulting plan has been executed.
#
# Planning/execution runs synchronously inside the subscription callback, so
# (as with a single-threaded executor generally) a target published while a
# move is in progress is only picked up once the current move finishes.

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Point
from geometry_msgs.msg import Pose
from moveit.planning import MoveItPy
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_msgs.msg import Constraints
from moveit_msgs.msg import PositionConstraint
import rclpy
from rclpy.node import Node
from shape_msgs.msg import SolidPrimitive
from std_msgs.msg import Bool

POSITION_TOLERANCE = 0.02
END_EFFECTOR_LINK = 'end_effector_link'
PLANNING_FRAME = 'world'
# Ignore a "new" target within this distance (m) of the last one -- a
# republish of the same value shouldn't retrigger a move.
SAME_TARGET_EPSILON = 1e-4


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


def make_position_goal_constraints(x, y, z):
    target_pose = Pose()
    target_pose.position.x = x
    target_pose.position.y = y
    target_pose.position.z = z
    target_pose.orientation.w = 1.0

    bounding_region = SolidPrimitive()
    bounding_region.type = SolidPrimitive.SPHERE
    bounding_region.dimensions = [POSITION_TOLERANCE]

    position_constraint = PositionConstraint()
    position_constraint.header.frame_id = PLANNING_FRAME
    position_constraint.link_name = END_EFFECTOR_LINK
    position_constraint.constraint_region.primitives.append(bounding_region)
    position_constraint.constraint_region.primitive_poses.append(target_pose)
    position_constraint.weight = 1.0

    constraints = Constraints()
    constraints.position_constraints.append(position_constraint)
    return constraints


class XArmMover(Node):

    def __init__(self, moveit_py_instance):
        super().__init__('x_arm_mover')
        self.moveit_py_instance = moveit_py_instance
        self.arm = moveit_py_instance.get_planning_component('arm')
        self.last_target = None

        self.success_pub = self.create_publisher(Bool, '/arm_move_success', 10)
        self.create_subscription(Point, '/arm_target_pos', self._target_callback, 10)

    def _target_callback(self, msg):
        target = (msg.x, msg.y, msg.z)
        if self.last_target is not None and all(
                abs(a - b) < SAME_TARGET_EPSILON for a, b in zip(target, self.last_target)):
            return
        self.last_target = target
        self._move_to(target)

    def _move_to(self, target):
        x, y, z = target
        self.get_logger().info(f'New target: x={x:.3f} y={y:.3f} z={z:.3f}')
        self.success_pub.publish(Bool(data=False))

        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(
            motion_plan_constraints=[make_position_goal_constraints(x, y, z)])

        plan_result = self.arm.plan()
        if not plan_result:
            self.get_logger().warn(
                'Planning failed for target, leaving arm_move_success False')
            return

        self.moveit_py_instance.execute(plan_result.trajectory, controllers=[])
        self.get_logger().info('Move complete')
        self.success_pub.publish(Bool(data=True))


def main():
    rclpy.init()

    moveit_config = build_moveit_config()
    moveit_py_instance = MoveItPy(
        node_name='moveit_py_x_arm_mover', config_dict=moveit_config.to_dict())

    mover_node = XArmMover(moveit_py_instance)
    try:
        rclpy.spin(mover_node)
    except KeyboardInterrupt:
        pass
    finally:
        mover_node.destroy_node()
        # MoveItPy shuts down its own internal rclpy context on SIGINT before
        # this line runs, so calling shutdown() again here would raise.
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
