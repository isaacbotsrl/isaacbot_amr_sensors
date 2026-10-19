# isaacbot_amr_realsense

Intel RealSense **D435i** driver for Ardennes: `realsense2_camera`, configured for the isaacbot,
the depth image as a point cloud (`depth_image_proc`), and a few depth rows as a `LaserScan`
(`depthimage_to_laserscan`, `camera/scan`). Moved here from
`isaacbot_amr_perception_bringup`, so drivers live in `isaacbot_amr_sensors` and perception in
`isaacbot_amr_perception`.

```bash
ros2 launch isaacbot_amr_realsense isaacbot_amr_realsense.launch.py namespace:=isaacbot
```

`isaacbot_amr_sensors.launch.py` includes it when `use_camera` (`ISAACBOT_AMR_SYSTEM_USE_CAMERA`) is true.

## Interfaces

| Direction | Name | Type |
|-----------|------|------|
| pub | `camera/color/image_raw`, `camera/color/camera_info` | 640x480 |
| pub | `camera/depth/image_rect_raw`, `camera/depth/camera_info` | `depth_profile` (default 424x240) |
| pub | `camera/depth/points` | `sensor_msgs/PointCloud2` (only with `use_depth_cloud`) |
| pub | `camera/scan` | `sensor_msgs/LaserScan`, always: frame `<namespace>/camera_depth_frame`, 0.2–4.0 m, `scan_height` 10 rows |
| tf  | `<namespace>/camera_link` → `<namespace>/camera_*_optical_frame` | from the driver |

Consumers: `isaacbot_amr_perception` (AprilTag, YOLO detection, fmoc person tracking), Nav 2's
local costmap when `ISAACBOT_AMR_ORCH_NAV_USE_CAMERA` is set, and `isaacbot_amr_indoor_nav_manager`
(isaacbot_amr_orchestrator), which relays `camera/scan` to SLAM/AMCL when the lidar is lost.

`camera/scan` comes from `depthimage_to_laserscan::DepthImageToLaserScanROS` in its own container,
`camera_scan_container`, fed by `camera/depth/image_rect_raw`.

## Arguments

| Argument | Default | Meaning |
|----------|---------|---------|
| `namespace` | `$ISAACBOT_AMR_SYSTEM_NAMESPACE`, else empty | topics under it; frames prefixed `<namespace>/` |
| `use_depth_cloud` | `$ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_CLOUD`, else `false` | depth → `camera/depth/points` |
| `camera_fps` | `$ISAACBOT_AMR_SENSORS_CAMERA_FPS`, else `15` | colour and depth rate: 6, 15 or 30 |
| `depth_profile` | `$ISAACBOT_AMR_SENSORS_CAMERA_DEPTH_PROFILE`, else `424x240` | depth resolution WxH |
| `use_sim_time` | `false` | for the depth-cloud and camera-scan nodes |

## TF

The URDF (`isaacbot_amr_description`, `ISAACBOT_AMR_SYSTEM_USE_CAMERA`) places `<namespace>/camera_link` on the
body; `robot_state_publisher` prefixes every frame with the namespace. realsense2_camera 4.58
names its frames `tf_prefix` + `camera_name` + `_` + name (`base_frame_id` is `link`). With a
namespace the launch sets `tf_prefix` to `<namespace>/`, so the driver's `<namespace>/camera_link`
→ optical-frame transforms hang off the URDF's link. With a wrong prefix the optical frames form
a separate tree and any TF lookup from the point cloud to `base_link` or `odom` fails (the earlier
`<namespace>/camera_` gave `isaacbot/camera_camera_link`). Check with
`ros2 run tf2_ros tf2_echo isaacbot/base_link isaacbot/camera_depth_optical_frame`.

## WSL

`scripts/attach_camera.sh` (installed to `lib/isaacbot_amr_realsense`) hands the camera to WSL with
`usbipd-win`. Run it before the launch: the driver only sees devices present when it starts.

## Simulation

Not needed. With `ISAACBOT_AMR_SYSTEM_USE_CAMERA=true` the Gazebo depth camera publishes the same
`camera/depth/points` (see `isaacbot_amr_description/urdf/common/depth_camera.urdf.xacro`).
There is no `camera/scan` in Gazebo.
