from enum import Enum
import rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from geometry_msgs.msg import Point, PoseStamped
from aruco_opencv_msgs.msg import ArucoDetection
from action_msgs.msg import GoalStatusArray
import time

GOAL_MARKER_ID = 1

class Phase(Enum):
    IDLE = 1
    GOING_TO_BALL = 2
    PICKING_BALL = 3
    GOAL_DETECTED = 5
    GOING_TO_GOAL = 6
    SCORING = 7
    SCORED = 8

class Frontman (Node):

    def __init__(self):
        super().__init__('frontman')

        self.current_state = Phase.GOAL_DETECTED
        self.subscription = self.create_subscription(ArucoDetection, '/aruco_detections',  self.aruco_callback, 10)  # type of message and topic, then how many messages to send to the topic until one is sent in the case it is overloaded
        self.subscription_goal = self.create_subscription(GoalStatusArray, '/navigate_to_pose/_action/status',  self.status_callback, 10) 
        self.publisher = self.create_publisher(PoseStamped, '/goal_pose', 10)

    def aruco_callback(self, msg):
        goal_msg = PoseStamped()

        #self.get_logger().info(f"found {len(msg.markers)} markers")
        for marker in msg.markers:
            if marker.marker_id != GOAL_MARKER_ID: continue

            # create a pose stamped object
            goal_msg = PoseStamped()

            # the pose is the one extracted from the camera
            goal_msg.pose = marker.pose
            goal_msg.pose.position.z -= 0.50
            goal_msg.header = msg.header
            # mark current time and reference frame (camera)
            #goal_msg.header.stamp = self.get_clock().now().to_msg()
            #goal_msg.header.frame_id = 'camera' 
            # TODO: will the transformation to a goal_pose in the odom reference frame be automatically handled by the navigation module?

            # if not, uncomment this line
            #goal_msg = tf.transformPose("odom", goal_msg)

            if self.current_state == Phase.GOAL_DETECTED:
                print(self.current_state)
                #self.current_state = Phase.GOING_TO_GOAL
                self.publisher.publish(goal_msg)

        
        #goal_msg.header.stamp = self.get_clock().now().to_msg()
        #goal_msg.header.frame_id = 'odom' 
        #goal_msg.pose.position.x = msg.x
        #goal_msg.pose.position.y = msg.y
        #goal_msg.pose.position.z = 0.0
        #goal_msg.pose.orientation.w = 0.0
        
        #self.publisher.publish(goal_msg)

    def status_callback(self, msg):
        
        print(str(msg.status_list[-1].status))

        if msg.status_list[-1].status == 4:

            if self.current_state == Phase.GOING_TO_BALL: 
                self.current_state = Phase.PICKING_BALL
                time.sleep(5)
                self.current_state = Phase.GOING_TO_GOAL
            
            #elif self.current_state == Phase.GOING_TO_GOAL:
            elif self.current_state == Phase.GOAL_DETECTED:
                self.current_state = Phase.SCORING
                # timer
                self.current_state = Phase.SCORED

                goal_msg = PoseStamped()
                goal_msg.pose.position.x = 0.0
                goal_msg.pose.position.y = 0.0
                goal_msg.pose.position.z = 0.0
                goal_msg.pose.orientation.w = 0.0
                goal_msg.header.stamp = self.get_clock().now().to_msg()
                goal_msg.header.frame_id = 'odom'
                # TODO: will the transformation to a goal_pose in the odom reference frame be automatically handled by the navigation module?

                self.publisher.publish(goal_msg)

                self.current_state = Phase.IDLE
            
            elif self.current_state == Phase.IDLE:
                self.current_state = Phase.GOING_TO_BALL
                print(self.current_state)



def main(args=None):
    rclpy.init(args=args)
    node = Frontman()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()