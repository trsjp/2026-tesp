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
# Python/moveit_py port of open_manipulator_playground's
# open_manipulator_x_random_mover.cpp: every MOVE_INTERVAL_S seconds, plan
# and execute a move to a random reachable position (position-only goal,
# orientation left free) using MoveIt's "arm" planning group.

import os
import random
import time
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Pose
from moveit.planning import MoveItPy
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_msgs.msg import Constraints
from moveit_msgs.msg import PositionConstraint
import rclpy
from shape_msgs.msg import SolidPrimitive

# Reachable workspace bounds (m) for OpenMANIPULATOR-X, centered on the base frame.
MIN_X, MAX_X = 0.12, 0.25
MIN_Y, MAX_Y = -0.15, 0.15
MIN_Z, MAX_Z = 0.05, 0.30
MOVE_INTERVAL_S = 5.0
POSITION_TOLERANCE = 0.02
END_EFFECTOR_LINK = 'end_effector_link'
PLANNING_FRAME = 'world'


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


def main():
    rclpy.init()
    logger = rclpy.logging.get_logger('random_mover_py')

    moveit_config = build_moveit_config()
    moveit_py_instance = MoveItPy(
        node_name='moveit_py_random_mover', config_dict=moveit_config.to_dict())
    arm = moveit_py_instance.get_planning_component('arm')

    while rclpy.ok():
        x = random.uniform(MIN_X, MAX_X)
        y = random.uniform(MIN_Y, MAX_Y)
        z = random.uniform(MIN_Z, MAX_Z)
        logger.info(f'Target: x={x:.3f} y={y:.3f} z={z:.3f}')

        arm.set_start_state_to_current_state()
        arm.set_goal_state(motion_plan_constraints=[make_position_goal_constraints(x, y, z)])

        plan_result = arm.plan()
        if plan_result:
            moveit_py_instance.execute(plan_result.trajectory, controllers=[])
            logger.info('Move complete')
        else:
            logger.warn('Planning failed for random target, retrying next cycle')

        time.sleep(MOVE_INTERVAL_S)

    # MoveItPy shuts down its own internal rclpy context on SIGINT before this
    # line runs, so calling shutdown() again here would raise.
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
