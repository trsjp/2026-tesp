from enum import Enum
import rclpy
from rclpy.node import Node
from std_msgs.msg import Header
from geometry_msgs.msg import Point, PoseStamped
from aruco_opencv_msgs.msg import ArucoDetection
from yolo_msgs.msg import DetectionArray
from action_msgs.msg import GoalStatusArray
import time

GOAL_MARKER_ID = 1

class Phase(Enum):
    SEARCHING_BALL = 1
    GOING_TO_BALL = 2
    PICKING_BALL = 3
    GOAL_DETECTED = 5
    GOING_TO_GOAL = 6
    SCORING = 7
    SCORED = 8
    SEARCHING_GOAL = 9

class Frontman (Node):

    def __init__(self):
        super().__init__('frontman')

        self.current_state = Phase.SEARCHING_BALL
        #self.current_state = Phase.GOING_TO_GOAL
        self.subscription_aruco = self.create_subscription(ArucoDetection, '/aruco_detections',  self.aruco_callback, 10)  # type of message and topic, then how many messages to send to the topic until one is sent in the case it is overloaded
        self.subscription_yolo = self.create_subscription(DetectionArray, "/yolo/detections_3d", self.yolo_callback, 10)
        self.subscription_goal = self.create_subscription(GoalStatusArray, '/navigate_to_pose/_action/status',  self.status_callback, 10) 
        self.publisher = self.create_publisher(PoseStamped, '/goal_pose', 10)

        self.get_logger().info("finished init")

    def aruco_callback(self, msg):
         if self.current_state is Phase.GOING_TO_GOAL:

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

                #if self.current_state == Phase.GOAL_DETECTED:
                self.get_logger().info("aruco:" + str(self.current_state))
                #self.current_state = Phase.GOING_TO_GOAL
                self.publisher.publish(goal_msg)


    def yolo_callback(self, msg):

        if self.current_state is Phase.SEARCHING_BALL:  
            self.get_logger().info("yolo:" + str(self.current_state))
            for detection in msg.detections:

                if detection.class_name == "sports ball":
                    self.get_logger().info("yolo: ball detected")
                    # create a pose stamped object
                    goal_msg = PoseStamped()

                    goal_msg.pose = detection.bbox3d.center
                    goal_msg.pose.position.z -= 0.30
                    goal_msg.header = msg.header

                    #self.get_logger().info("yolo:" + str(self.current_state))
                    self.current_state = Phase.GOING_TO_BALL
                    self.get_logger().info("yolo:" + str(self.current_state))
                    self.times = 0
                    self.ball_goal_msg = goal_msg
                    self.timer = self.create_timer(0.1, self.timer_ball_callback)

    def timer_ball_callback(self):
        if self.times < 10:
            self.publisher.publish(self.ball_goal_msg)
            self.times -= 1
            return True
        else:
            return False

    def status_callback(self, msg):
        
        self.get_logger().info(str(msg.status_list[-1].status))

        if msg.status_list[-1].status == 4:

            if self.current_state is Phase.GOING_TO_BALL:
                self.get_logger().info("status: reached ball" )
                self.current_state = Phase.PICKING_BALL
                time.sleep(5)
                self.current_state = Phase.GOING_TO_GOAL
                self.get_logger().info("status:" + str(self.current_state))
            
            elif self.current_state is Phase.GOING_TO_GOAL:
            #elif self.current_state == Phase.GOAL_DETECTED:
                self.current_state = Phase.SCORING
                time.sleep(5)
                self.current_state = Phase.SCORED

                goal_msg = PoseStamped()
                goal_msg.pose.position.x = 0.0
                goal_msg.pose.position.y = 0.0
                goal_msg.pose.position.z = 0.0
                goal_msg.pose.orientation.z = 0.7071068
                goal_msg.pose.orientation.w = 0.7071068
                goal_msg.header.stamp = self.get_clock().now().to_msg()
                goal_msg.header.frame_id = 'base_link'

                #goal_msg = PoseStamped()
                #goal_msg.pose.position.x = 0.0
                #goal_msg.pose.position.y = 0.0
                #goal_msg.pose.position.z = 0.0
                #goal_msg.pose.orientation.z = 0.0
                #goal_msg.header.stamp = self.get_clock().now().to_msg()
                #goal_msg.header.frame_id = 'odom'
                
                self.publisher.publish(goal_msg)

                self.current_state = Phase.SEARCHING_BALL
            
            elif self.current_state is Phase.SEARCHING_BALL:

                goal_msg = PoseStamped()
                goal_msg.pose.position.x = 0.0
                goal_msg.pose.position.y = 0.0
                goal_msg.pose.position.z = 0.0
                goal_msg.pose.orientation.z = 0.7071068
                goal_msg.pose.orientation.w = 0.7071068
                goal_msg.header.stamp = self.get_clock().now().to_msg()
                goal_msg.header.frame_id = 'base_link'
                
                self.publisher.publish(goal_msg)
                self.get_logger().info("status:" + str(self.current_state))


def main(args=None):
    rclpy.init(args=args)
    node = Frontman()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()