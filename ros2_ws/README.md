# ros2_ws

This is the ROS 2 workspace for the TESP Robot Basketball project.

- External packages (iCart mini, OpenXArm/OpenRoboticX, Gello) go into
  `ros2_ws/src`, cloned there by `scripts/clone_repos.sh`. See
  [../docs/repository_sources.md](../docs/repository_sources.md).
- Build the workspace from `ros2_ws` using colcon:
  ```bash
  rosdep install --from-paths src --ignore-src -r -y
  colcon build --symlink-install
  source install/setup.bash
  ```
  Or use `bash scripts/setup_workspace.sh` from the repository root.
- Do not commit `build/`, `install/`, or `log/` — they are ignored by
  `.gitignore`.
- A future integration package for this project may be added under
  `ros2_ws/src/tesp_robot_basketball`.

# Teleoperation

## Safety package

# Autonoumous operation

## Camera

### Installation

Clone and install packages for Realsense camera and aruco detection into `ros2_ws/src`

```
git clone https://github.com/fictionlab/ros_aruco_opencv --branch jazzy
git clone https://github.com/realsenseai/realsense-ros --branch ros-master
```

Install dependencies

```
rosdep install -i --from-path ros_aruco_opencv --rosdistro jazzy -y
rosdep install -i --from-path realsense-ros --rosdistro jazzy -y
colcon build
```

### Running

Launch the camera topic

```
ros2 launch realsense2_camera rs_launch.py depth_module.depth_profile:=1280x720x30 pointcloud.enable:=true
```

Launch the Aruco detection

```
ros2 run aruco_opencv aruco_tracker_autostart --ros-args -p cam_base_topic:=/camera/camera/color/image_raw -p image_is_rectified:=true -p marker_size:=0.15

```

Info is published on the /aruco_detection topic
