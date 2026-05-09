import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.exceptions import ParameterAlreadyDeclaredException
from rclpy.parameter import Parameter


class TargetSender:
    """封装发送目标点给Nav2的类"""

    def __init__(self):
        self.navigator = BasicNavigator()
        try:
            self.navigator.declare_parameter('use_sim_time', True)
        except ParameterAlreadyDeclaredException:
            self.navigator.set_parameters([
                Parameter('use_sim_time', value=True)
            ])

    def quaternion_from_yaw(self, yaw: float) -> Quaternion:
        """将平面朝向角 yaw 转成四元数。"""
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw * 0.5)
        q.w = math.cos(yaw * 0.5)
        return q

    def build_goal(self, x: float, y: float, yaw: float = 0.0) -> PoseStamped:
        """构建目标点消息。"""
        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = 0.0
        goal.pose.orientation = self.quaternion_from_yaw(yaw)
        return goal

    def send_target(self, x: float, y: float, yaw: float = 0.0):
        """发送目标点并等待执行结果。"""
        print('等待 Nav2 系统就绪...')
        self.navigator.waitUntilNav2Active(localizer='bt_navigator')
        print(f'Nav2 已就绪，开始发送目标点：(x={x}, y={y}, yaw={yaw})')

        goal_pose = self.build_goal(x, y, yaw)
        goal_pose.header.stamp = self.navigator.get_clock().now().to_msg()
        self.navigator.goToPose(goal_pose)

        last_reported_distance = None
        while not self.navigator.isTaskComplete():
            rclpy.spin_once(self.navigator, timeout_sec=0.1)
            feedback = self.navigator.getFeedback()
            if feedback is not None:
                remaining = float(feedback.distance_remaining)
                # 避免每次循环重复打印同一个数值，仍保持持续输出
                if last_reported_distance is None or abs(remaining - last_reported_distance) >= 0.01:
                    print(f'距离目标点剩余：{remaining:.2f} m')
                    last_reported_distance = remaining
            time.sleep(0.1)

        result = self.navigator.getResult()
        self._handle_result(result)

    def _handle_result(self, result):
        """处理任务返回结果。"""
        if result == TaskResult.SUCCEEDED:
            print('目标点到达成功。')
        elif result == TaskResult.CANCELED:
            print('导航任务已取消。')
        elif result == TaskResult.FAILED:
            print('导航任务失败。')
        else:
            print(f'导航结束，但结果未知：{result}')

    def destroy(self):
        """销毁节点资源。"""
        self.navigator.destroy_node()


import sys

def main():
    rclpy.init()
    target_sender = TargetSender()
    
    # 设置默认目标值
    target_x = 2.0
    target_y = 1.0
    target_yaw = 0.0
    
    # 尝试从命令行参数获取目标点
    # 过滤掉 ROS 隐式传入的额外系统参数，提取出纯数字参数
    user_args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    
    if len(user_args) >= 2:
        try:
            target_x = float(user_args[0])
            target_y = float(user_args[1])
            if len(user_args) >= 3:
                target_yaw = float(user_args[2])
        except ValueError:
            print("参数格式错误，将使用默认坐标。请输入如: 3.0 2.0 0.0")

    try:
        print(f"====== 开始自动前往新目标: x={target_x}, y={target_y}, yaw={target_yaw} ======")
        target_sender.send_target(x=target_x, y=target_y, yaw=target_yaw)
    finally:
        target_sender.destroy()
        rclpy.shutdown()


if __name__ == '__main__':
    main()