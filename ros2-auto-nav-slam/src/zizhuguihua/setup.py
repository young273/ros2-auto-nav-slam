from glob import glob
from setuptools import find_packages, setup

package_name = 'zizhuguihua'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/urdf', glob('urdf/*')),
        ('share/' + package_name + '/rviz', glob('rviz/*')),
        ('share/' + package_name + '/worlds', glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='young',
    maintainer_email='user@example.com',
    description='ROS 2 Humble Nav2 autonomous navigation package with LiDAR obstacle avoidance.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'send_target = zizhuguihua.send_target:main',
            'map_receiver = zizhuguihua.map_receiver:main',
        ],
    },
)
