# Copyright 2016 Open Source Robotics Foundation, Inc.
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

import random

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

MAX_STEP = 0.2  # rad, max change applied to each joint per goal
GOAL_DURATION = 1.0  # seconds allowed to reach each random target

"""# The trajectory for all revolute, continuous or prismatic joints
trajectory_msgs/JointTrajectory trajectory
        std_msgs/Header header
                builtin_interfaces/Time stamp
                        int32 sec
                        uint32 nanosec
                string frame_id
        string[] joint_names
        JointTrajectoryPoint[] points
                float64[] positions
                float64[] velocities
                float64[] accelerations
                float64[] effort
                builtin_interfaces/Duration time_from_start
                        int32 sec
                        uint32 nanosec
# The trajectory for all planar or floating joints (i.e. individual joints with more than one DOF)
trajectory_msgs/MultiDOFJointTrajectory multi_dof_trajectory
        std_msgs/Header header
                builtin_interfaces/Time stamp
                        int32 sec
                        uint32 nanosec
                string frame_id
        string[] joint_names
        MultiDOFJointTrajectoryPoint[] points
                geometry_msgs/Transform[] transforms
                        Vector3 translation
                                float64 x
                                float64 y
                                float64 z
                        Quaternion rotation
                                float64 x 0
                                float64 y 0
                                float64 z 0
                                float64 w 1
                geometry_msgs/Twist[] velocities
                        Vector3  linear
                                float64 x
                                float64 y
                                float64 z
                        Vector3  angular
                                float64 x
                                float64 y
                                float64 z
                geometry_msgs/Twist[] accelerations
                        Vector3  linear
                                float64 x
                                float64 y
                                float64 z
                        Vector3  angular
                                float64 x
                                float64 y
                                float64 z
                builtin_interfaces/Duration time_from_start
                        int32 sec
                        uint32 nanosec

# Tolerances for the trajectory.  If the measured joint values fall
# outside the tolerances the trajectory goal is aborted.  Any
# tolerances that are not specified (by being omitted or set to 0) are
# set to the defaults for the action server (often taken from the
# parameter server).

# Tolerances applied to the joints as the trajectory is executed.  If
# violated, the goal aborts with error_code set to
# PATH_TOLERANCE_VIOLATED.
JointTolerance[] path_tolerance
        #
        string name
        float64 position  #
        float64 velocity  #
        float64 acceleration  #
JointComponentTolerance[] component_path_tolerance
        uint16 X_AXIS=1
        uint16 Y_AXIS=2
        uint16 Z_AXIS=3
        uint16 TRANSLATION=4
        uint16 ROTATION=5
        string joint_name
        uint16 component
        float64 position
        float64 velocity
        float64 acceleration

# To report success, the joints must be within goal_tolerance of the
# final trajectory value.  The goal must be achieved by time the
# trajectory ends plus goal_time_tolerance.  (goal_time_tolerance
# allows some leeway in time, so that the trajectory goal can still
# succeed even if the joints reach the goal some time after the
# precise end time of the trajectory).
#
# If the joints are not within goal_tolerance after "trajectory finish
# time" + goal_time_tolerance, the goal aborts with error_code set to
# GOAL_TOLERANCE_VIOLATED
JointTolerance[] goal_tolerance
        #
        string name
        float64 position  #
        float64 velocity  #
        float64 acceleration  #
JointComponentTolerance[] component_goal_tolerance
        uint16 X_AXIS=1
        uint16 Y_AXIS=2
        uint16 Z_AXIS=3
        uint16 TRANSLATION=4
        uint16 ROTATION=5
        string joint_name
        uint16 component
        float64 position
        float64 velocity
        float64 acceleration
builtin_interfaces/Duration goal_time_tolerance
        int32 sec
        uint32 nanosec

---
int32 error_code
int32 SUCCESSFUL = 0
int32 INVALID_GOAL = -1
int32 INVALID_JOINTS = -2
int32 OLD_HEADER_TIMESTAMP = -3
int32 PATH_TOLERANCE_VIOLATED = -4
int32 GOAL_TOLERANCE_VIOLATED = -5

# Human readable description of the error code. Contains complementary
# information that is especially useful when execution fails, for instance:
# - INVALID_GOAL: The reason for the invalid goal (e.g., the requested
#   trajectory is in the past).
# - INVALID_JOINTS: The mismatch between the expected controller joints
#   and those provided in the goal.
# - PATH_TOLERANCE_VIOLATED and GOAL_TOLERANCE_VIOLATED: Which joint
#   violated which tolerance, and by how much.
string error_string

---
std_msgs/Header header
        builtin_interfaces/Time stamp
                int32 sec
                uint32 nanosec
        string frame_id
string[] joint_names
trajectory_msgs/JointTrajectoryPoint desired
        float64[] positions
        float64[] velocities
        float64[] accelerations
        float64[] effort
        builtin_interfaces/Duration time_from_start
                int32 sec
                uint32 nanosec
trajectory_msgs/JointTrajectoryPoint actual
        float64[] positions
        float64[] velocities
        float64[] accelerations
        float64[] effort
        builtin_interfaces/Duration time_from_start
                int32 sec
                uint32 nanosec
trajectory_msgs/JointTrajectoryPoint error
        float64[] positions
        float64[] velocities
        float64[] accelerations
        float64[] effort
        builtin_interfaces/Duration time_from_start
                int32 sec
                uint32 nanosec

string[] multi_dof_joint_names
trajectory_msgs/MultiDOFJointTrajectoryPoint multi_dof_desired
        geometry_msgs/Transform[] transforms
                Vector3 translation
                        float64 x
                        float64 y
                        float64 z
                Quaternion rotation
                        float64 x 0
                        float64 y 0
                        float64 z 0
                        float64 w 1
        geometry_msgs/Twist[] velocities
                Vector3  linear
                        float64 x
                        float64 y
                        float64 z
                Vector3  angular
                        float64 x
                        float64 y
                        float64 z
        geometry_msgs/Twist[] accelerations
                Vector3  linear
                        float64 x
                        float64 y
                        float64 z
                Vector3  angular
                        float64 x
                        float64 y
                        float64 z
        builtin_interfaces/Duration time_from_start
                int32 sec
                uint32 nanosec
trajectory_msgs/MultiDOFJointTrajectoryPoint multi_dof_actual
        geometry_msgs/Transform[] transforms
                Vector3 translation
                        float64 x
                        float64 y
                        float64 z
                Quaternion rotation
                        float64 x 0
                        float64 y 0
                        float64 z 0
                        float64 w 1
        geometry_msgs/Twist[] velocities
                Vector3  linear
                        float64 x
                        float64 y
                        float64 z
                Vector3  angular
                        float64 x
                        float64 y
                        float64 z
        geometry_msgs/Twist[] accelerations
                Vector3  linear
                        float64 x
                        float64 y
                        float64 z
                Vector3  angular
                        float64 x
                        float64 y
                        float64 z
        builtin_interfaces/Duration time_from_start
                int32 sec
                uint32 nanosec
trajectory_msgs/MultiDOFJointTrajectoryPoint multi_dof_error
        geometry_msgs/Transform[] transforms
                Vector3 translation
                        float64 x
                        float64 y
                        float64 z
                Quaternion rotation
                        float64 x 0
                        float64 y 0
                        float64 z 0
                        float64 w 1
        geometry_msgs/Twist[] velocities
                Vector3  linear
                        float64 x
                        float64 y
                        float64 z
                Vector3  angular
                        float64 x
                        float64 y
                        float64 z
        geometry_msgs/Twist[] accelerations
                Vector3  linear
                        float64 x
                        float64 y
                        float64 z
                Vector3  angular
                        float64 x
                        float64 y
                        float64 z
        builtin_interfaces/Duration time_from_start
                int32 sec
                uint32 nanosec"""



class RandomPositionMover(Node):

    def __init__(self):
        super().__init__('minimal_publisher') #run _init__() from Node
        self.joint_names = ['joint1', 'joint2', 'joint3', 'joint4']
        self.current_positions = None
        self.action_client = ActionClient(
            self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, 10)
        timer_period = 2.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback) #execute timer_callback every 5s

    def joint_state_callback(self, msg):
        if not set(self.joint_names).issubset(msg.name):
            return
        self.current_positions = [msg.position[msg.name.index(j)] for j in self.joint_names]

    def timer_callback(self):
        if self.current_positions is None:
            self.get_logger().warn('No joint states received yet, skipping this goal')
            return

        if not self.action_client.server_is_ready():
            self.get_logger().warn('Action server not available yet, skipping this goal')
            return

        positions = [p + random.uniform(-MAX_STEP, MAX_STEP) for p in self.current_positions]

        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start.sec = int(GOAL_DURATION)
        point.time_from_start.nanosec = int((GOAL_DURATION % 1) * 1e9)

        trajectory = JointTrajectory()
        trajectory.joint_names = self.joint_names
        trajectory.points = [point]

        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory = trajectory

        self.get_logger().info('Sending goal: %s' % positions)
        send_goal_future = self.action_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected')
            return
        self.get_logger().info('Goal accepted')


def main(args=None):
    rclpy.init(args=args)

    random_mover = RandomPositionMover()

    rclpy.spin(random_mover)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    random_mover.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
