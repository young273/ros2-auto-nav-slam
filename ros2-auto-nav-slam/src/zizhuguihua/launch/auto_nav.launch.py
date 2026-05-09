from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # 默认开启 SLAM：机器人一边扫描一边建图
    use_slam_arg = DeclareLaunchArgument(
        'use_slam',
        default_value='true',
        description='Use slam_toolbox to build a map online'
    )

    # 是否启动 Gazebo GUI
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Start Gazebo GUI client'
    )

    # 如果不使用 SLAM，则需要传入静态地图 yaml 的绝对路径
    map_arg = DeclareLaunchArgument(
        'map',
        default_value='',
        description='Full path to the static map yaml file'
    )

    # Gazebo 世界文件（默认使用本包测试场景，非空世界）
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=PathJoinSubstitution([
            FindPackageShare('zizhuguihua'),
            'worlds',
            'nav_test.world',
        ]),
        description='Full path to Gazebo world file'
    )

    # RViz 配置，默认使用 Nav2 官方视图配置
    rviz_arg = DeclareLaunchArgument(
        'rviz_config',
        default_value=PathJoinSubstitution([
            FindPackageShare('zizhuguihua'),
            'rviz',
            'nav2_sim.rviz',
        ]),
        description='Full path to RViz config file'
    )

    # 本包自带的 Nav2 参数文件
    params_file = PathJoinSubstitution([
        FindPackageShare('zizhuguihua'),
        'config',
        'nav2_params.yaml',
    ])

    rviz_config = LaunchConfiguration('rviz_config')

    # 机器人模型 xacro
    robot_xacro = PathJoinSubstitution([
        FindPackageShare('zizhuguihua'),
        'urdf',
        'zizhuguihua.urdf.xacro',
    ])

    # 机器人描述，供 robot_state_publisher 和 spawn_entity 使用
    robot_description = Command([
        FindExecutable(name='xacro'),
        ' ',
        robot_xacro,
    ])

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_description,
        }],
    )

    gazebo_world = LaunchConfiguration('world')

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gzserver.launch.py',
            ])
        ),
        launch_arguments={
            'world': gazebo_world,
            'verbose': 'false',
        }.items(),
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gzclient.launch.py',
            ])
        ),
        launch_arguments={
            'verbose': 'false',
        }.items(),
        condition=IfCondition(LaunchConfiguration('gui')),
    )

    # 先等 Gazebo 启动，再把机器人实体插入到世界中
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'zizhuguihua',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.10',
        ],
    )

    delayed_spawn = TimerAction(
        period=4.0,
        actions=[spawn_entity],
    )

    # Nav2 bringup：SLAM 模式用于未知地图；静态地图模式作为备用
    nav2_bringup_launch = PathJoinSubstitution([
        FindPackageShare('nav2_bringup'),
        'launch',
        'bringup_launch.py',
    ])

    slam_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_bringup_launch),
        launch_arguments={
            'slam': 'True',
            'map': '',
            'params_file': params_file,
            'autostart': 'true',
            'use_sim_time': 'true',
        }.items(),
        condition=IfCondition(LaunchConfiguration('use_slam')),
    )

    static_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_bringup_launch),
        launch_arguments={
            'slam': 'False',
            'map': LaunchConfiguration('map'),
            'params_file': params_file,
            'autostart': 'true',
            'use_sim_time': 'true',
        }.items(),
        condition=UnlessCondition(LaunchConfiguration('use_slam')),
    )

    start_nav2_and_rviz = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                slam_bringup,
                static_bringup,
                TimerAction(
                    period=5.0,
                    actions=[
                        Node(
                            package='rviz2',
                            executable='rviz2',
                            output='screen',
                            arguments=['-d', rviz_config],
                            parameters=[{'use_sim_time': True}],
                        )
                    ],
                ),
            ],
        )
    )

    return LaunchDescription([
        use_slam_arg,
        gui_arg,
        map_arg,
        world_arg,
        rviz_arg,
        robot_state_publisher,
        gzserver,
        gzclient,
        delayed_spawn,
        start_nav2_and_rviz,
    ])