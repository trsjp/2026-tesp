import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist, Vector3

from math import radians, degrees

# use lidar data to stop if going towards obstacles

class TeleopSafety(Node):

    # arguments are Range Of Interest start and end (in degrees), Stop distance (in meters)
    def __init__(self, roi_start, roi_end, stop_dst, min_points):
        super().__init__('teleop_safety')
        # subscribes to the scan topic to read lidarr data
        self.laser_scan = self.create_subscription(
            LaserScan,
            'scan',
            self.lidar_callback,
            10)
        self.laser_scan  # prevent unused variable warning
        # subscribes to the cmd_vel_orig topic to know the angle
        # self.odom = self.create_subscription(
        #     String,
        #     'cmd_vel_orig',
        #     self.cmd_vel_callback,
        #     10)
        # subscribes to the cmd_vel_orig topic to know the original velocity reference
        self.cmd_vel_orig = self.create_subscription(
            Twist,
            'cmd_vel_orig',
            self.cmd_vel_callback,
            10)
        self.cmd_vel_orig  # prevent unused variable warning

        # publishes to the cmd_vel topic
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        self.roi_start_deg = roi_start
        self.roi_end_deg = roi_end
        self.roi_start_rad = radians(self.roi_start_deg)
        self.roi_end_rad = radians(self.roi_end_deg)

        self.stop_dst = stop_dst
        self.min_points = min_points

        self.cmd_vel = None
        self.scan = None

    def lidar_callback(self, msg):
        if self.scan is None:
            self.get_logger().info('# ranges: "%d"' % len(msg.ranges))
            self.get_logger().info(f'angles: "{msg.angle_min}, {msg.angle_max}, {msg.angle_increment}"')

            self.roi_start_idx = (self.roi_start_rad - msg.angle_min) // msg.angle_increment
            self.roi_start_idx = int(self.roi_start_idx)
            self.roi_end_idx = (self.roi_end_rad - msg.angle_min) // msg.angle_increment
            self.roi_end_idx = int(self.roi_end_idx)

            self.get_logger().info(f'idx: "{self.roi_start_idx}, {self.roi_end_idx}"')

        self.scan = msg

        if self.cmd_vel is None:
            self.get_logger().info('No cmd_vel yet')
            return        

        roi = msg.ranges[self.roi_start_idx:self.roi_end_idx]
        self.cmd_vel_modified = self.cmd_vel

        n = 0
        for v in roi:
            # self.get_logger().info(f'{v}')
            if v <= self.stop_dst: n += 1

        if n >= self.min_points and self.cmd_vel.linear.x > 0:
            self.cmd_vel_modified.linear = Vector3()
            self.get_logger().info(f"There's {n} points above threshold level ({self.min_points}): preventing forwards motion.")

        # just pass the message through for now
        self.publisher_.publish(self.cmd_vel_modified)

    def cmd_vel_callback(self, msg):
        self.cmd_vel = msg

def main(args=None):
    rclpy.init(args=args)

    teleop_safety = TeleopSafety(-10, 10, 0.5, 15)

    rclpy.spin(teleop_safety)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()