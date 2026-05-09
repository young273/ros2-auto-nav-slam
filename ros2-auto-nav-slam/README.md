# zizhuguihua (自主规划与实时建图模块)

## 一、项目简介

`zizhuguihua` 是本系统中负责底盘运动控制、环境感知、自主导航以及实时建图（SLAM）的核心基础模块。

该模块深度集成了 ROS2 Humble 的 **Nav2 (Navigation2)** 协议栈以及 **slam_toolbox**，实现了机器人在未知或者已知环境下的连续自主运行。由于模块提供了高度解耦的**程序化接口节点（如目标下发、地图影像实时接收等）**，供上层多智能体决策调度模块（如 Module Three）及外部程序调用。它是连接上层“决策”与真实物理“运动”的关键枢纽。

---

## 二、核心功能特性

| 功能模块 | 描述说明 |
| :--- | :--- |
| **1. 实时同步建图 (Online SLAM)** | 使用 `slam_toolbox` 在机器人运动过程中边走边建图，利用单线激光雷达（`/scan`）数据实时感知识别障碍物，并动态生成 2D 栅格地图（`/map`）。 |
| **2. 动态激光避障与导航** | 基于 **Nav2** 协议栈，结合自定义的代价地图与 `amcl` 蒙特卡洛定位，实现在复杂地形和动态障碍物环境下的稳定自主跟线与避障。 |
| **3. 实时地图影像转换服务** | 自动提取后台枯燥的 ROS 网格数组数据，并以高频率转换映射为直观灰阶图像（`live_map.png`），供非 ROS 系统或外部 UI 实时监视当前的建图进度。 |
| **4. OOP目标点派发器** | 面向对象（OOP）封装了与 Nav2 核心的 Action 通信，允许外部决策代码快速地直接发送航向坐标控制底盘，并获得详细距离与任务状态反馈。 |

---

## 三、目录空间结构

经过标准化的 ROS 2 Payload 封装后，本模块具有独立干净的结构：

```text
zizhuguihua/
├── package.xml
├── setup.py
├── setup.cfg
├── README.md                      # 本说明文档
├── config/
│   └── nav2_params.yaml           # Nav2算法及SLAM核心参数配置文件（雷达匹配速率、避障阈值等）
├── launch/
│   └── auto_nav.launch.py         # 核心集成启动文件（Gazebo仿真+模型加载+SLAM+Nav2+RViz）
├── urdf/
│   └── zizhuguihua.urdf.xacro     # 机器人物理模型与传感器挂载定义文件
├── rviz/
│   └── nav2_sim.rviz              # RViz2 可视化UI页面预配置树
├── worlds/
│   └── nav_test.world             # 仿真测试物理场景（包含边界与预设障碍物）
└── zizhuguihua/
    ├── __init__.py
    ├── send_target.py             # 向 Nav2 发送目标动作客户端 (可被外部从 package 引入复用)
    └── map_receiver.py            # 实时地图图像化订阅节点
```

---

## 四、核心节点代码与作用介绍

### 1. 核心导航与仿真架构 (`auto_nav.launch.py`)
这不是一个简单脚本，而是系统的“核心骨架”。它的作用是按顺序一键拉起整个复杂的 ROS 2 机器人运动栈：
- 加载 `gazebo` 并在测试物理世界 (`nav_test.world`) 中生成你的机器人（基于 `zizhuguihua.urdf.xacro`）。
- 读取并挂载本包 `config/nav2_params.yaml` 中配置好的各项导航、速度、雷达阈值参数。
- 启动 `slam_toolbox` 和 `Nav2` 进行底层建图与寻路服务计算。
- 打开包含预设样式的 `rviz2` 可视化调试面板。

### 2. 地图影像接管节点 (`map_receiver.py`)
- **角色**：建图数据转换器。
- **作用**：实时订阅名为 `/map`（`nav_msgs/OccupancyGrid`格式）的话题。将后台的数据流（-1表示未知、0表示空闲、100表示障碍）用 `numpy` 和 `cv2` 库重构为常规图片像素数据（灰度图），同时考虑到原点偏差进行了坐标轴翻转，并将实时渲染的结果以 `live_map.png` 保存在本地用于 UI 调取或者结果展示。

### 3. OOP控制枢纽节点 (`send_target.py`)
- **角色**：动作执行派遣桥梁。
- **作用**：以高度封装的 `TargetSender` 类实现了 `BasicNavigator` 的连接工作逻辑。不仅可单独执行测试发送 `(2.0, 1.0, 0.0)` 的航路点指令给底层 Nav2 追踪，还能高频获取并打印“距离目标点剩余X米”等反馈结果。
- **封装优势**：外部决策节点只需 `from zizhuguihua.send_target import TargetSender` 即可脱离复杂的 Action Client 建立过程，直接调用其内嵌的 `send_target(x, y, yaw)`。

---

## 五、如何启动与运行？

> **开发编译前提**:
> 请确保当前位于你的工作空间根目录（例如 `~/project/zizhuguihua`），模块代码位于 `src/zizhuguihua` 下。

首先进行整体编译和环境加载（仅代码变动后需要重构）：
```bash
colcon build --packages-select zizhuguihua
source install/setup.bash
```

接下来，请按照以下步骤依次在**三个独立终端**中启动各个功能组件：

### 步骤 1：拉起仿真世界、SLAM建图与导航核心 (Terminal 1)
```bash
source install/setup.bash
# 启动（默认使用SLAM建图模式以及带有GUI物理界面）
ros2 launch zizhuguihua auto_nav.launch.py
```
> **效果预期**：Gazebo 物理引擎视窗与 RViz2 监控UI将自动弹出。机器人的环境与雷达扫描线将可视化呈现。

### 步骤 2：启动地图影像实时转换接手端 (Terminal 2)
```bash
source install/setup.bash
# 运行建图拦截导出工具
ros2 run zizhuguihua map_receiver
```
> **效果预期**：终端打印 "Map Receiver is waiting..." 数据获取成功后，将会在你运行命令的当前控制台目录下实时不间断更新名为 `live_map.png` 的可见地图图片。

### 步骤 3：让机器人前往指定目标位置 (Terminal 3)
```bash
source install/setup.bash

# 方式一：默认测试，派遣机器人前往预设坐标(2.0, 1.0)
ros2 run zizhuguihua send_target

# 方式二：手动动态传参，例如命令机器人前往坐标 x=3.5, y=-1.5：
ros2 run zizhuguihua send_target 3.5 -1.5

# 方式三：传递包含车头朝向的数据（x, y, yaw），如朝向90度(1.57)
ros2 run zizhuguihua send_target 3.0 2.0 1.57
```
> **效果预期**：终端会打印出你派发的目标坐标，并实时刷新到达目标的剩余距离；同时在 RViz2 中机器人会遵循智能规划的绿色路线向你指定的坐标移动，生成的 `live_map.png` 也会随着沿途雷达扫描逐渐建图并补全。

---

## 六、关键话题 (Topics) 接口摘要

- **输入话题 (Subscriptions)**
  - `/scan` \- 核心激光雷达数据流（雷达层生成，SLAM模块订阅）
  - `/map` \- 实时建立的环境网格数据（`map_receiver` 节点订阅）

- **输出话题 (Publications)**
  - `/cmd_vel` \- Nav2 输出的实际底盘运动控制线速度与角速度
  - 自建地图文件 \- 映射输出至文件系统的 `live_map.png`

---

## 七、真实未知环境（如野外实车）部署指南

本模块天然支持在完全未知的物理环境（如野外）中进行探索与建图。由于本模块核心算法采用的是 Online SLAM（即时定位与建图机制），面对未知环境时**原本就无需任何预设地图**，更不需要向其提供 `.world` 场景文件（`.world` 仅在开发阶段供电脑里的虚拟仿真引擎使用）。

若要将代码直接丢到真车并在真实的野外环境运行建图，您只需要针对感知的数据流进行以下几点简单的调整置换：

### 1. 剥离虚拟仿真代码
打开 `launch/auto_nav.launch.py`，**注释或删除**启动虚拟仿真的相关的节点模块，真车不需要在电脑里再模拟出一个自己：
- `gzserver` 和 `gzclient` (取消启动 Gazebo 物理引擎本体)
- `spawn_entity` (取消执行实体在虚拟环境中的生成代码)

### 2. 接入真车硬件传感器流
在野外没有参数虚拟生成的数据，因此需要实体物理硬件接管数据的发布：
- **开启真实雷达驱动**：运行厂商提供的雷达包（如镭神、思岚等激光雷达节点），确保其硬件开启并始终能向系统发布实时的 `/scan` 雷达点云话题。
- **开启底盘驱动**：运行嵌入式下位机的底盘通信节点。该硬件节点负责吞入上接算法下发的 `/cmd_vel` 进而控制真实车轮，同时也负责把真实物理电机位移估算的 `/odom`（里程计）和 TF 坐标变换树返回给系统。

### 3. 如何开始建图探索？
当你确保真实的 `/scan` 和 `/odom` 数据流都存在后，核心层的 SLAM 与 Nav2 算法机制无需做任何内部修改，直接用与之前相同的命令启动核心：
```bash
source install/setup.bash
ros2 launch zizhuguihua auto_nav.launch.py
```
> **效果预期**：随着真实 LiDAR 通电并开始扫描野外的树丛与石头，你的系统就像置身于迷雾中心，会自动依据雷达感知向四周延展出真实的防碰撞地图网格。此时无论你是自动通过 `send_target` 派发移动命令，还是用真车手柄控制它转转，它都会高精度地补全真实世界的实时地图！
