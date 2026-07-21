from enum import Enum
import rclpy
import tf2
from rclpy.node import Node
from std_msgs.msg import Header
from geometry_msgs.msg import Point, PoseStamped
from aruco_opencv_msgs.msg import ArucoDetection

GOAL_MARKER_ID = 1

class Phase(Enum):
    IDLE
    GOING_TO_BALL
    PICKING_BALL
    GOING_TO_GOAL
    SCORING

class Frontman (Node):

    def __init__(self):
        super().__init__('frontman')

        self.subscription = self.create_subscription(ArucoDetection, '/aruco_detections',  self.aruco_callback, 10)  # type of message and topic, then how many messages to send to the topic until one is sent in the case it is overloaded
        self.publisher = self.create_publisher(PoseStamped, '/goal_pose', 10)

    def aruco_callback(self, msg):
        goal_msg = PoseStamped()

        # self.get_logger().info(f"found {len(msg.markers)} markers")
        for marker in msg.markers:
            if marker.marker_id != GOAL_MARKER_ID: continue

            # create a pose stamped object
            goal_msg = PoseStamped()

            # the pose is the one extracted from the camera
            goal_msg.pose = marker.pose
            # mark current time and reference frame (camera)
            goal_msg.header.stamp = self.get_clock().now().to_msg()
            goal_msg.header.frame_id = 'camera' 
            # TODO: will the transformation to a goal_pose in the odom reference frame be automatically handled by the navigation module?

            # if not, uncomment this line
            goal_msg = tf.transformPose("odom", goal_msg)
            self.publisher.publish(goal_msg)

        
        #goal_msg.header.stamp = self.get_clock().now().to_msg()
        #goal_msg.header.frame_id = 'odom' 
        #goal_msg.pose.position.x = msg.x
        #goal_msg.pose.position.y = msg.y
        #goal_msg.pose.position.z = 0.0
        #goal_msg.pose.orientation.w = 0.0
        
        #self.publisher.publish(goal_msg)


def main(args=None):
    rclpy.init(args=args)
    node = Cam_To_Goal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
