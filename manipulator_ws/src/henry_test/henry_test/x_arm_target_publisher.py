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
# Test publisher for x_arm_mover.py: publishes a random 3D position to
# /arm_target_pos every PUBLISH_INTERVAL_S seconds.

import random

from geometry_msgs.msg import Point
import rclpy
from rclpy.node import Node

# Reachable workspace bounds (m) for OpenMANIPULATOR-X, centered on the base
# frame -- matches moveit_py_random_mover.py.
MIN_X, MAX_X = 0.12, 0.25
MIN_Y, MAX_Y = -0.15, 0.15
MIN_Z, MAX_Z = 0.05, 0.30
PUBLISH_INTERVAL_S = 5.0


class RandomTargetPublisher(Node):

    def __init__(self):
        super().__init__('x_arm_target_publisher')
        self.pub = self.create_publisher(Point, '/arm_target_pos', 10)
        self.create_timer(PUBLISH_INTERVAL_S, self._publish_random_target)

    def _publish_random_target(self):
        msg = Point()
        msg.x = random.uniform(MIN_X, MAX_X)
        msg.y = random.uniform(MIN_Y, MAX_Y)
        msg.z = random.uniform(MIN_Z, MAX_Z)
        self.get_logger().info(f'Publishing target: x={msg.x:.3f} y={msg.y:.3f} z={msg.z:.3f}')
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = RandomTargetPublisher()
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
