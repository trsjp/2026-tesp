# Repository Sources

External robot repositories are cloned into `ros2_ws/src` by
`scripts/clone_repos.sh`. The upstream URLs below are **not yet confirmed**
and are placeholders only.

| Component | Purpose | Target folder | Upstream URL | Notes |
|---|---|---|---|---|
| iCart mini | Mobile base drivers, description, bringup, navigation support | `ros2_ws/src/icart_mini` | TODO: add official iCart mini ROS 2 repository URL | Confirm ROS 2 branch/version before use |
| OpenXArm / OpenRoboticX arm | Arm description, control, MoveIt configuration, hardware interface | `ros2_ws/src/openxarm_ros2` | TODO: add official OpenXArm/OpenRoboticX repository URL | Confirm package names and MoveIt support |
| Gello | Lead-arm teleoperation controller | `ros2_ws/src/gello` | TODO: add official Gello repository URL | Confirm Python dependencies, serial/USB permissions, and ROS 2 interface |

## Important

- Do not guess URLs.
- Confirm official repository URLs with the instructor before adding them
  here.
- After confirming URLs, update the corresponding variables in
  `scripts/clone_repos.sh`:
  - `ICART_MINI_REPO_URL`
  - `OPENXARM_REPO_URL`
  - `GELLO_REPO_URL`
