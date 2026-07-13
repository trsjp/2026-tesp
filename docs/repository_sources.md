# Repository Sources

External robot repositories are cloned into `ros2_ws/src` by
`scripts/clone_repos.sh`. This page records what was checked upstream for
each component and why each URL/branch was chosen.

| Component | Purpose | Target folder | Upstream URL | Notes |
|---|---|---|---|---|
| iCart mini (`icart-ros2`) | Mobile base drivers, description, ros2_control, Gazebo sim, param/udev setup, YP-Spur bridge | `ros2_ws/src/icart-ros2` | https://github.com/CRG-Tohoku/icart-ros2 (branch: `worktree-ros2-jazzy-migration`) | 6 colcon packages + `ypspur_ros2` git submodule in one repo — see below. |
| Gello | Lead-arm teleoperation controller | `ros2_ws/src/gello` | https://github.com/wuphilipp/gello_software (branch: `main`) | Standalone Python project, not a colcon package — see below. |
| ROBOTIS OpenManipulator | Arm description, control, MoveIt config, hardware interface | `ros2_ws/src/open_manipulator` | https://github.com/ROBOTIS-GIT/open_manipulator (branch: `jazzy`) | Official ROS 2 Jazzy support confirmed. MoveIt config bundled. |
| — companion: dynamixel_hardware_interface | `ros2_control` hardware interface plugin for the arm | `ros2_ws/src/dynamixel_hardware_interface` | https://github.com/ROBOTIS-GIT/dynamixel_hardware_interface (branch: `jazzy`) | Required by OpenManipulator. Built from source via colcon. |
| — companion: dynamixel_interfaces | Custom msg/srv interfaces for Dynamixel actuators | `ros2_ws/src/dynamixel_interfaces` | https://github.com/ROBOTIS-GIT/dynamixel_interfaces (branch: `jazzy`) | Required by OpenManipulator. Built from source via colcon. |
| — companion: DynamixelSDK | Dynamixel actuator SDK | `ros2_ws/src/DynamixelSDK` | https://github.com/ROBOTIS-GIT/DynamixelSDK (branch: `jazzy`) | Required by OpenManipulator. Built from source via colcon. |

## iCart mini: ROS 2 Jazzy migration (CRG-Tohoku fork)

`open-rdc/icart` (the iCart mini repository) has **no ROS 2 branch at
all** — every branch (`indigo-devel`, `kinetic-devel`, `melodic-devel`,
`noetic-devel`, etc.) is ROS1/catkin. There is no `jazzy`, `humble`, or
`foxy` branch, and no `ros2` fork maintained by the same org. An
unofficial community port exists at
`https://github.com/haruyama8940/icart_mini_driver_ros2` (branch `main`),
but it is unmaintained (last commit June 2023, developed against
Foxy-era ROS 2), untested on Jazzy/Ubuntu 24.04, and incomplete (driver
node only — no description or Gazebo packages).

`CRG-Tohoku/icart-ros2` (branch `worktree-ros2-jazzy-migration`) is an
instructor-authored ROS 2 Jazzy migration, forked from `open-rdc/icart`.
**This is an active, in-progress branch, not a pinned stable release** —
if it moves or is renamed, re-verify the package/dependency breakdown
below against the branch before trusting it.

It is a single repo containing 6 colcon packages as subdirectories, plus
one git submodule:

| Package | Role |
|---|---|
| `icart_mini` | Meta package, depends on the other 5 |
| `icart_mini_description` | URDF/xacro robot model |
| `icart_mini_control` | `ros2_control` controller config (diff drive) |
| `icart_mini_driver` | Real-hardware bringup (YP-Spur bridge, lidar, joystick teleop) |
| `icart_mini_gazebo` | Gazebo (`gz-sim`) simulation launch/config |
| `icart_mini_setup` | Parameter/udev-rule generation scripts + tests |
| `ypspur_ros2` (submodule → `CRG-Tohoku/ypspur_ros2`) | ROS 2 bridge to the non-ROS `yp-spur` C motor-controller library. This fork carries Jazzy-specific fixes not present upstream. |

`clone_repos.sh` clones this with `--recurse-submodules` to pull
`ypspur_ros2` along with the main repo. colcon discovers all 6 nested
packages recursively — no per-package clone entries needed.

Two build-time system dependencies fall outside what `rosdep install`
can resolve, and are handled directly in the shared `Dockerfile`:

- **`yp-spur`** — `ypspur_ros2`'s `CMakeLists.txt` does
  `find_package(ypspur 1.20.0 REQUIRED)`; there is no rosdep key for it.
  The Dockerfile builds it from source
  (`openspur/yp-spur` → `./configure && make && make install`).
- **Gazebo simulation support** (`ros-jazzy-ros-gz`,
  `ros-jazzy-gz-ros2-control`) — previously out of scope for this
  image; now installed because `icart_mini_gazebo` needs it.

## Gello: standalone Python project, not a colcon package

`gello_software` is installed as a plain Python package (via `uv`/pip),
not built with colcon. Its `requirements.txt` also pulls in SDKs for
several robot arms this project doesn't use (UR, xArm, Franka), a
Pinocchio pin, and expects Python 3.11. Because of this:

- `clone_repos.sh` clones it into `ros2_ws/src/gello` for reference/
  source. It has no `package.xml`, but colcon's generic Python package
  identification still picks up its bare `setup.py` and tries to build
  it — which fails under `colcon build --symlink-install` specifically:
  symlink-install only symlinks `setup.py` and the top-level `gello/`
  package directory into `ros2_ws/build/gello/`, not the rest of the
  source tree, and `gello_software`'s `setup.py` reads `README.md` via a
  bare relative path (`open("README.md")`), which no longer resolves
  once only those two paths are symlinked in. `clone_repos.sh` places a
  `COLCON_IGNORE` marker file in `ros2_ws/src/gello/` right after
  cloning — colcon's standard mechanism for excluding a directory from
  package discovery entirely — so it's never attempted.
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
