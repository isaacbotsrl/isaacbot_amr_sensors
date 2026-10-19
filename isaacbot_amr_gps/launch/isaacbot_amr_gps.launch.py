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

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.actions.lifecycle_node import LifecycleNode
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    common_dir_path = LaunchConfiguration("common_dir_path")
    declare_common_dir_path_arg = DeclareLaunchArgument(
        "common_dir_path",
        default_value="",
        description="Path to the common configuration directory.",
    )

    log_level = LaunchConfiguration("log_level")
    declare_log_level_arg = DeclareLaunchArgument(
        "log_level",
        default_value="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"],
        description="Logging level",
    )

    namespace = LaunchConfiguration("namespace")
    declare_namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value=EnvironmentVariable("ISAACBOT_AMR_SYSTEM_NAMESPACE", default_value=""),
        description="Add namespace to all launched nodes",
    )

    isaacbot_amr_gps_common_dir = PythonExpression(
        [
            "'",
            common_dir_path,
            "/isaacbot_amr_gps' if '",
            common_dir_path,
            "' else '",
            FindPackageShare("isaacbot_amr_gps"),
            "'",
        ]
    )

    isaacbot_amr_gps_config_path = LaunchConfiguration("isaacbot_amr_gps_config_path")
    declare_isaacbot_amr_gps_config_path_arg = DeclareLaunchArgument(
        "isaacbot_amr_gps_config_path",
        default_value=PathJoinSubstitution(
            [isaacbot_amr_gps_common_dir, "config", "isaacbot_amr_gps.yaml"]
        ),
        description="Specify the path to the isaacbot GPS configuration file.",
    )

    # GPS faults (poor accuracy, no data, data timeout) are only errors when something localizes
    # on GPS, and nothing does: isaacbot_amr_indoor_nav_manager localizes on the lidar or the
    # camera (or odometry). The isaacbot is usually indoors, where tens of metres of error are
    # normal and the GPS may be switched off - reporting that as ERROR would turn the whole
    # isaacbot red for nothing.
    gps_required = LaunchConfiguration("gps_required")
    declare_gps_required_arg = DeclareLaunchArgument(
        "gps_required",
        default_value="false",
        description="Report missing GPS data and poor GNSS accuracy as errors (true) or "
        "warnings (false, default: nothing localizes on GPS).",
    )

    # Lifecycle node, brought straight to active: it owns the UDP socket, so deactivating it
    # frees port 10110 for debugging (see README) without killing the process.
    isaacbot_amr_gps_driver_node = LifecycleNode(
        package="isaacbot_amr_gps",
        executable="isaacbot_amr_gps_driver_node",
        name="isaacbot_amr_gps_driver",
        namespace=namespace,
        parameters=[isaacbot_amr_gps_config_path, {"tf_prefix": namespace}],
        remappings=[
            ("fix", "gps/fix"),
            ("vel", "gps/vel"),
            ("heading", "gps/heading"),
            ("time_reference", "gps/time_reference"),
        ],
        autostart=True,
        arguments=[
            "--ros-args",
            "--log-level",
            log_level,
        ],
        emulate_tty=True,
    )

    isaacbot_amr_gps_node = Node(
        package="isaacbot_amr_gps",
        executable="isaacbot_amr_gps_node",
        name="isaacbot_amr_gps_node",
        namespace=namespace,
        parameters=[
            isaacbot_amr_gps_config_path,
            {"gps_required": ParameterValue(gps_required, value_type=bool)},
        ],
        remappings=[("/diagnostics", "diagnostics")],
        arguments=[
            "--ros-args",
            "--log-level",
            log_level,
        ],
        emulate_tty=True,
    )

    actions = [
        declare_common_dir_path_arg,
        declare_log_level_arg,
        declare_namespace_arg,
        declare_isaacbot_amr_gps_config_path_arg,
        declare_gps_required_arg,
        isaacbot_amr_gps_driver_node,
        isaacbot_amr_gps_node,
    ]

    return LaunchDescription(actions)
