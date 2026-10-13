<p align="center">
  <img src="icons/Logo-Arm-WhiteOrange-372x372-1.png" alt="Mechatronics Academy" width="140">
</p>

# isaacbot_amr_sensors

Mechatronics Academy's Ardennes sensor payload: drivers for the sensors that differ between
isaacbots and missions, running in their own container (`rover-a1-sensors`).

- [`isaacbot_amr_gps`](isaacbot_amr_gps/README.md) - RUTX11 NMEA-over-UDP GNSS driver (`isaacbot_amr_gps_driver`,
  lifecycle) and GPS fix health diagnostics (`isaacbot_amr_gps_node`).
- [`isaacbot_amr_rs16_lidar`](isaacbot_amr_rs16_lidar/README.md) - RoboSense RS16 lidar in one lifecycle
  node: point cloud, `scan` projection and stream health, with `rs_driver` vendored.
- [`isaacbot_amr_realsense`](isaacbot_amr_realsense/README.md) - Intel RealSense D435i: colour and depth
  images, and the depth point cloud, with frames under the isaacbot's TF prefix.
- [`isaacbot_amr_sensors_bringup`](isaacbot_amr_sensors_bringup/README.md) - `isaacbot_amr_sensors.launch.py`,
  starts the drivers selected by `ISAACBOT_AMR_SYSTEM_USE_GPS` / `ISAACBOT_AMR_SYSTEM_USE_LIDAR` / `ISAACBOT_AMR_SYSTEM_USE_CAMERA`,
  then the perception on top of them (`isaacbot_amr_perception`).

The GNSS heading alignment that GPS localization needs is not here. It needs `odom`, so it
lives in `isaacbot_amr_ros/isaacbot_amr_gps_heading`.

## Quick start

### Create workspace

```bash
mkdir -p ~/ros2_ws/rover_a1
cd ~/ros2_ws/rover_a1
git clone -b master https://github.com/isaacbotsrl/isaacbot_amr_sensors.git src/isaacbot_amr_sensors
```

No package here builds against `isaacbot_amr_ros`. The platform is only needed at runtime: its URDF
defines the `<namespace>/gps_link`, `<namespace>/lidar_link` and `<namespace>/camera_link`
frames the drivers stamp.

`isaacbot_amr_sensors_bringup` also starts the perception layer, so the container clones
[`isaacbot_amr_perception`](https://github.com/isaacbotsrl/isaacbot_amr_perception) next to this repo, and
`isaacbot_amr_ros/isaacbot_amr_msgs` for its message types.

### Setup environment variables

```bash
export ROS_DISTRO=lyrical

# Must match the platform, otherwise the drivers publish outside the isaacbot's namespace.
export ISAACBOT_AMR_SYSTEM_NAMESPACE=isaacbot

# Which drivers to start. All default to false.
export ISAACBOT_AMR_SYSTEM_USE_GPS=true
export ISAACBOT_AMR_SYSTEM_USE_LIDAR=true
export ISAACBOT_AMR_SYSTEM_USE_CAMERA=true
```

### Clone dependency

```bash
vcs import src < src/isaacbot_amr_sensors/sensors_deps.repos
```

The list is currently empty: `rs_driver` is vendored in `isaacbot_amr_rs16_lidar/3rdparty`, the
GNSS driver is in-tree, and `realsense2_camera` comes from apt (rosdep).

### Build

```bash
sudo rosdep init
rosdep update --rosdistro $ROS_DISTRO
rosdep install --from-paths src -y -i

source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install --packages-up-to isaacbot_amr_sensors_bringup

source install/setup.bash
```

### Running

#### Real isaacbot:

```bash
ros2 launch isaacbot_amr_sensors_bringup isaacbot_amr_sensors.launch.py use_gps:=true use_lidar:=true
```

#### Simulated isaacbot:

Not needed. `isaacbot_amr_gazebo` publishes the same `<namespace>/scan`, `rslidar_points`, `gps/fix`
and (with `ISAACBOT_AMR_SYSTEM_USE_CAMERA`) `camera/depth/points` from simulated sensors. Perception can still
run on them: `ros2 launch isaacbot_amr_perception_bringup isaacbot_amr_perception.launch.py`.

### Testing

```bash
colcon test --packages-select isaacbot_amr_gps isaacbot_amr_rs16_lidar --parallel-workers 1
colcon test-result --all
```

Run node tests one at a time: parallel workers make them flaky under the zenoh middleware.

## Related repositories

A complete isaacbot is three repositories, one per container:

- [`isaacbot_amr_ros`](https://github.com/isaacbotsrl/isaacbot_amr_ros) - the platform
  (`rover-a1-platform`).
- [`isaacbot_amr_sensors`](https://github.com/isaacbotsrl/isaacbot_amr_sensors) - this one, the sensor
  payload: GNSS, lidar and camera drivers, plus `isaacbot_amr_perception` on top
  (`rover-a1-sensors`).
- [`isaacbot_amr_orchestrator`](https://github.com/isaacbotsrl/isaacbot_amr_orchestrator) - the autonomy
  stack, Nav 2 and mission supervision (`rover-a1-orchestrator`).
