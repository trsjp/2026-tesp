# Repository Sources

External robot repositories are cloned into `ros2_ws/src` by
`scripts/clone_repos.sh`. This page records what was checked upstream for
each component and why each URL/branch was chosen (or, for iCart, why it
is intentionally left as a TODO).

| Component | Purpose | Target folder | Upstream URL | Notes |
|---|---|---|---|---|
| iCart mini | Mobile base drivers, description, bringup, navigation support | `ros2_ws/src/icart_mini` | **TODO** — see below | No ROS 2 branch exists upstream. Left unset in `clone_repos.sh` on purpose. |
| Gello | Lead-arm teleoperation controller | `ros2_ws/src/gello` | https://github.com/wuphilipp/gello_software (branch: `main`) | Standalone Python project, not a colcon package — see below. |
| ROBOTIS OpenManipulator | Arm description, control, MoveIt config, hardware interface | `ros2_ws/src/open_manipulator` | https://github.com/ROBOTIS-GIT/open_manipulator (branch: `jazzy`) | Official ROS 2 Jazzy support confirmed. MoveIt config bundled. |
| — companion: dynamixel_hardware_interface | `ros2_control` hardware interface plugin for the arm | `ros2_ws/src/dynamixel_hardware_interface` | https://github.com/ROBOTIS-GIT/dynamixel_hardware_interface (branch: `jazzy`) | Required by OpenManipulator. Built from source via colcon. |
| — companion: dynamixel_interfaces | Custom msg/srv interfaces for Dynamixel actuators | `ros2_ws/src/dynamixel_interfaces` | https://github.com/ROBOTIS-GIT/dynamixel_interfaces (branch: `jazzy`) | Required by OpenManipulator. Built from source via colcon. |
| — companion: DynamixelSDK | Dynamixel actuator SDK | `ros2_ws/src/DynamixelSDK` | https://github.com/ROBOTIS-GIT/DynamixelSDK (branch: `jazzy`) | Required by OpenManipulator. Built from source via colcon. |

## iCart mini: no ROS 2 support upstream

`open-rdc/icart` (the iCart mini repository) has **no ROS 2 branch at
all** — every branch (`indigo-devel`, `kinetic-devel`, `melodic-devel`,
`noetic-devel`, etc.) is ROS1/catkin. There is no `jazzy`, `humble`, or
`foxy` branch, and no `ros2` fork maintained by the same org.

An unofficial community port exists at
`https://github.com/haruyama8940/icart_mini_driver_ros2` (branch `main`),
but it is:
- unmaintained (last commit June 2023, developed against Foxy-era ROS 2),
- untested on Jazzy/Ubuntu 24.04,
- incomplete (driver node only — no description or Gazebo packages).

`ICART_MINI_REPO_URL` is left as `TODO` in `scripts/clone_repos.sh` until
the instructor decides how to proceed (evaluate the unofficial port, plan
a ROS1→ROS2 port, or find another upstream source). Do not clone the
ROS1 repo into the ROS2 workspace expecting it to build.

## Gello: standalone Python project, not a colcon package

`gello_software` is installed as a plain Python package (via `uv`/pip),
not built with colcon. Its `requirements.txt` also pulls in SDKs for
several robot arms this project doesn't use (UR, xArm, Franka), a
Pinocchio pin, and expects Python 3.11. Because of this:

- `clone_repos.sh` clones it into `ros2_ws/src/gello` for reference/
  source, but `scripts/setup_workspace.sh`'s `colcon build` will simply
  skip it (there's no `package.xml` at its root).
- Its Python environment is **not** set up by any script in this repo —
  follow `gello_software`'s own README (`uv venv --python 3.11`, `git
  submodule update --init`, etc.) manually once you know which of its
  hardware backends you actually need.
- Its dependencies are deliberately **not** added to the shared
  `Dockerfile` — most are irrelevant hardware SDKs for other robot arms,
  and bundling them risks destabilizing the shared ROS environment for
  everyone.

## Important

- Do not guess URLs — the ones above were checked directly against each
  repository (branches, package.xml, official Dockerfiles) before being
  added here.
- If an upstream repo changes (branch renamed, moved, etc.), update this
  table and the corresponding variable in `scripts/clone_repos.sh`
  together.
