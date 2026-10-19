#!/usr/bin/env python3

# Copyright 2026 IsaacBot
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

"""RealSense D435i driver: colour and depth images, the depth image as a laser scan, and
(optionally) as a point cloud.

Publishes camera/color/image_raw, camera/depth/image_rect_raw, camera/scan and
(ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_CLOUD) camera/depth/points, which isaacbot_amr_perception (AprilTag, YOLO,
fmoc person tracking) and Nav 2's local costmap (ISAACBOT_AMR_ORCH_NAV_USE_CAMERA) consume.
camera/scan lets isaacbot_amr_indoor_nav_manager keep SLAM/AMCL running on the camera alone
when the lidar is lost.

ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_CLOUD    depth -> PointCloud2 camera/depth/points (default false)
ISAACBOT_AMR_SENSORS_CAMERA_FPS            colour and depth frame rate: 6, 15 or 30 (default 15)
ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_PROFILE  depth resolution WxH (default 424x240)

TF: the driver publishes camera_link -> its optical frames. The isaacbot's frames carry the
namespace (robot_state_publisher's frame_prefix), and the URDF places <namespace>/camera_link on
the body, so the driver's frames need the same prefix to hang off that link. realsense2_camera
4.58 names every frame tf_prefix + <camera_name> + "_" + <name> (base_frame_id is "link"), so a
namespace means tf_prefix "<namespace>/": <namespace>/camera_link, ..._depth_optical_frame.
(Verified on the isaacbot 2026-10-10: "<namespace>/camera_" gave isaacbot/camera_camera_link, a tree
of its own.)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def env_flag(value):
    """True for true/1/yes/on (any case): the values usually come straight from balena."""
    return PythonExpression(["'", value, "'.strip().lower() in ('true', '1', 'yes', 'on')"])


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    use_depth_cloud = LaunchConfiguration('use_depth_cloud')
    use_sim_time = LaunchConfiguration('use_sim_time')
    camera_fps = LaunchConfiguration('camera_fps')
    depth_profile = LaunchConfiguration('depth_profile')
    # "<namespace>/" (frames <namespace>/camera_link, ...), or "" (camera_link, ...) without a
    # namespace; the driver adds camera_name itself.
    tf_prefix = PythonExpression(["'", namespace, "'.strip('/') + '/' if '", namespace,
                                  "'.strip('/') else ''"])

    # Depth at 424x240 / 15 Hz is plenty for a 3 m costmap source and keeps USB and CPU load low.
    realsense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare('realsense2_camera'), 'launch', 'rs_launch.py'])),
        launch_arguments={
            'camera_name': 'camera',
            'camera_namespace': namespace,
            'tf_prefix': tf_prefix,
            'depth_module.depth_profile': [depth_profile, 'x', camera_fps],
            'rgb_camera.color_profile': ['640x480x', camera_fps],
            'enable_color': 'true',
            'enable_depth': 'true',
            'enable_infra1': 'false',
            'enable_infra2': 'false',
            'enable_gyro': 'false',
            'enable_accel': 'false',
            'pointcloud.enable': 'false',  # depth_image_proc below does it, only when wanted
            'align_depth.enable': 'false',
        }.items(),
    )

    depth_cloud = ComposableNodeContainer(
        name='depth_cloud_container',
        namespace=namespace,
        package='rclcpp_components',
        executable='component_container',
        condition=IfCondition(env_flag(use_depth_cloud)),
        composable_node_descriptions=[ComposableNode(
            package='depth_image_proc',
            plugin='depth_image_proc::PointCloudXyzNode',
            name='depth_points',
            # A composable node does not inherit its container's namespace.
            namespace=namespace,
            remappings=[
                ('image_rect', 'camera/depth/image_rect_raw'),
                ('camera_info', 'camera/depth/camera_info'),
                ('points', 'camera/depth/points'),
            ],
            parameters=[{'use_sim_time': use_sim_time}],
        )],
        output='screen',
    )

    # A few depth rows around the optical centre as a LaserScan, in the camera's x-forward
    # depth frame (not the optical frame). ~87 deg wide; 4 m is where D435 depth stays usable.
    camera_scan = ComposableNodeContainer(
        name='camera_scan_container',
        namespace=namespace,
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[ComposableNode(
            package='depthimage_to_laserscan',
            plugin='depthimage_to_laserscan::DepthImageToLaserScanROS',
            name='camera_scan',
            namespace=namespace,
            remappings=[
                ('depth', 'camera/depth/image_rect_raw'),
                ('depth_camera_info', 'camera/depth/camera_info'),
                ('scan', 'camera/scan'),
            ],
            parameters=[{
                'use_sim_time': use_sim_time,
                'output_frame': [tf_prefix, 'camera_depth_frame'],
                'range_min': 0.2,
                'range_max': 4.0,
                'scan_height': 10,
            }],
        )],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value=EnvironmentVariable('ISAACBOT_AMR_SYSTEM_NAMESPACE', default_value='')),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'use_depth_cloud',
            default_value=EnvironmentVariable(
                'ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_CLOUD', default_value='false'),
            description='true/false, default from $ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_CLOUD.'),
        DeclareLaunchArgument(
            'camera_fps',
            default_value=EnvironmentVariable('ISAACBOT_AMR_SENSORS_CAMERA_FPS', default_value='15')),
        DeclareLaunchArgument(
            'depth_profile',
            default_value=EnvironmentVariable(
                'ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_PROFILE', default_value='424x240'),
            description='Depth resolution WxH.'),
        realsense,
        camera_scan,
        depth_cloud,
    ])
