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
# ball_position_publisher_example: a REFERENCE node showing how to talk to
# ball_grabber_node.py -- it builds the same geometry_msgs/Point messages a
# real perception node would send to grab_ball_position/dunk_ball_position,
# but by default only logs what it *would* publish (DEMO_MODE below) instead
# of actually sending them, so running this file never moves the real arm.
#
# To wire your own perception/logic in: copy _publish_or_log() and the
# create_publisher() calls in __init__ into your own node, replace the
# hardcoded DUMMY_GRAB_POSITION/DUMMY_DUNK_POSITION below with your real
# computed ball position, and either set DEMO_MODE = False here or just call
# .publish() directly like the DEMO_MODE branch does.
#
# Topic names/types here must match what ball_grabber_node.py subscribes to
# (GRAB_BALL_POSITION_TOPIC/DUNK_BALL_POSITION_TOPIC in that file) --
# they're duplicated as plain strings below rather than imported, so this
# file stays a lightweight, standalone reference that doesn't drag in
# MoveIt/moveit_py just to read two constants.

import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node

# Must match ball_grabber_node.py's GRAB_BALL_POSITION_TOPIC/DUNK_BALL_POSITION_TOPIC.
GRAB_BALL_POSITION_TOPIC = 'grab_ball_position'
DUNK_BALL_POSITION_TOPIC = 'dunk_ball_position'

# When True (the default), this node never actually publishes -- it only
# logs the Point it would have sent. Set to False to have it really publish
# the dummy positions below (e.g. to sanity-check ball_grabber_node end to
# end without a real perception stack).
DEMO_MODE = True

# Placeholder positions (metres, in the arm base frame) -- replace with a
# real perceived ball/hoop position in your own node. These are just
# plausible in-workspace numbers for the OpenMANIPULATOR-X, not measured
# from a real ball or hoop.
DUMMY_GRAB_POSITION = (0.15, 0.05, 0.05)
DUMMY_DUNK_POSITION = (0.15, -0.05, 0.15)

# How long after startup to fire the one-shot demo publish -- gives
# discovery time to match this node's publishers with ball_grabber_node's
# subscriptions before anything is sent.
STARTUP_DELAY_S = 1.0


class BallPositionPublisherExample(Node):

    def __init__(self):
        super().__init__('ball_position_publisher_example')

        self.grab_ball_position_pub = self.create_publisher(
            Point, GRAB_BALL_POSITION_TOPIC, 10)
        self.dunk_ball_position_pub = self.create_publisher(
            Point, DUNK_BALL_POSITION_TOPIC, 10)

        # One-shot: fire once, a moment after startup, then stop -- this is
        # a reference example, not a continuous stream, so it shouldn't keep
        # re-triggering ball_grabber_node's sequences forever if someone
        # flips DEMO_MODE off without reading the rest of this file.
        self._startup_timer = self.create_timer(STARTUP_DELAY_S, self._on_startup_timer)

    def _on_startup_timer(self):
        self._startup_timer.cancel()

        grab_msg = Point(
            x=DUMMY_GRAB_POSITION[0], y=DUMMY_GRAB_POSITION[1], z=DUMMY_GRAB_POSITION[2])
        dunk_msg = Point(
            x=DUMMY_DUNK_POSITION[0], y=DUMMY_DUNK_POSITION[1], z=DUMMY_DUNK_POSITION[2])

        self._publish_or_log(self.grab_ball_position_pub, GRAB_BALL_POSITION_TOPIC, grab_msg)
        self._publish_or_log(self.dunk_ball_position_pub, DUNK_BALL_POSITION_TOPIC, dunk_msg)

    def _publish_or_log(self, publisher, topic_name, msg):
        if DEMO_MODE:
            self.get_logger().info(
                f'[DEMO_MODE] would publish to {topic_name}: '
                f'x={msg.x}, y={msg.y}, z={msg.z} (set DEMO_MODE = False to actually send)')
        else:
            publisher.publish(msg)
            self.get_logger().info(f'Published to {topic_name}: x={msg.x}, y={msg.y}, z={msg.z}')


def main():
    rclpy.init()
    node = BallPositionPublisherExample()
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
