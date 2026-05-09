import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import numpy as np
import cv2

class MapReceiver(Node):
    def __init__(self):
        super().__init__('map_receiver')
        self.subscription = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10)
        self.get_logger().info("Map Receiver is waiting for /map messages...")
        
    def map_callback(self, msg):
        self.get_logger().info("Received updated map!")
        width = msg.info.width
        height = msg.info.height
        data = np.array(msg.data).reshape((height, width))
        
        # -1 = unknown (grey), 0 = free (white), 100 = occupied (black)
        img = np.full((height, width), 127, dtype=np.uint8)
        img[data == 0] = 255
        img[data == 100] = 0
        
        # Map origin is normally bottom-left, but image origin is top-left
        img = cv2.flip(img, 0)
        
        cv2.imwrite('live_map.png', img)
        self.get_logger().info("Saved real-time map image to live_map.png")

def main(args=None):
    rclpy.init(args=args)
    node = MapReceiver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
