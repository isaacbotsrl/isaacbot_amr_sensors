# isaacbot_amr_sensors_bringup

Starts the Ardennes sensor payload. `rover-a1-sensors` (`rover_docker`) runs it in its
`start.sh`.

```bash
ros2 launch isaacbot_amr_sensors_bringup isaacbot_amr_sensors.launch.py
```

| Argument | Default | Starts |
|----------|---------|--------|
| `use_gps` | `$ISAACBOT_AMR_SYSTEM_USE_GPS`, else `false` | `isaacbot_amr_gps` (`isaacbot_amr_gps_driver` + `isaacbot_amr_gps_node`) |
| `use_lidar` | `$ISAACBOT_AMR_SYSTEM_USE_LIDAR`, else `false` | `isaacbot_amr_rs16_lidar` (`isaacbot_amr_rs16_lidar_node`) |
| `use_camera` | `$ISAACBOT_AMR_SYSTEM_USE_CAMERA`, else `false` | `isaacbot_amr_realsense` (RealSense D435i + depth cloud); also gates the camera-based perception nodes |
| `namespace` | `$ISAACBOT_AMR_SYSTEM_NAMESPACE`, else empty | passed to every driver |
| `common_dir_path` | empty | passed to every driver |
| `log_level` | `INFO` | passed to every driver |

It always includes `isaacbot_amr_perception_bringup/isaacbot_amr_perception.launch.py`, which decides from its
own switches (AprilTag, detection, person tracking) what to run. See the repo `README.md` for
the topic contract.
