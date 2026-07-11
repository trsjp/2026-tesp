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
