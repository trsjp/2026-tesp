# iCart mini: resolve the ROS 2 source TODO

## Context

`docs/repository_sources.md` and `scripts/clone_repos.sh` have carried a
`TODO` for the iCart mini mobile base since the initial workspace
scaffold: the upstream repo (`open-rdc/icart`) has no ROS 2 branch at
all, and the one known community port is unmaintained and incomplete.
The TODO explicitly named "plan a ROS1→ROS2 port" as one option for the
instructor to pursue.

That port now exists: `CRG-Tohoku/icart-ros2` (branch
`worktree-ros2-jazzy-migration`) is an instructor-authored, in-progress
ROS 2 Jazzy migration, forked from `open-rdc/icart`. This spec covers
wiring it into this repo's Docker/clone/build workflow, replacing the
TODO with a working source.

## What the upstream repo actually is

Unlike the other companion repos already handled by `clone_repos.sh`
(each of which is one colcon package per git repo), `icart-ros2` is a
single git repo containing **6 colcon packages as subdirectories**, plus
one **git submodule**:

| Package | Role |
|---|---|
| `icart_mini` | Meta package, depends on the other 5 |
| `icart_mini_description` | URDF/xacro robot model |
| `icart_mini_control` | `ros2_control` controller config (diff drive) |
| `icart_mini_driver` | Real-hardware bringup (YP-Spur bridge, lidar, joystick teleop) |
| `icart_mini_gazebo` | Gazebo (`gz-sim`) simulation launch/config |
| `icart_mini_setup` | Parameter/udev-rule generation scripts + tests |
| `ypspur_ros2` (submodule → `CRG-Tohoku/ypspur_ros2`) | ROS 2 bridge to the non-ROS `yp-spur` C motor-controller library. This fork carries Jazzy-specific fixes not present in `openspur/ypspur_ros2` upstream. |

Verified directly against the branch (package.xml `depend`/`exec_depend`/
`test_depend` tags, `ypspur_ros2`'s `CMakeLists.txt`, and the repo's own
`Dockerfile`/`README.md`) — see the "Verification" section for how to
re-check if this branch moves.

Two build-time system dependencies fall outside what rosdep can resolve
automatically:

1. **`yp-spur`** — a non-ROS C library. `ypspur_ros2`'s `CMakeLists.txt`
   does `find_package(ypspur 1.20.0 REQUIRED)`; there is no rosdep key
   for it. It must be built from source
   (`git clone https://github.com/openspur/yp-spur` →
   `./configure && make && make install && ldconfig`) before `colcon
   build` reaches `ypspur_ros2`.
2. **Gazebo simulation support** (`ros-jazzy-ros-gz`,
   `ros-jazzy-gz-ros2-control`) — this project's `Dockerfile` currently
   documents Gazebo as explicitly out of scope for the default image.
   `icart_mini_gazebo` needs it.

Everything else (`ros-jazzy-controller-manager`, `ros-jazzy-teleop-twist-joy`,
`ros-jazzy-joy`, `ros-jazzy-urg-node`, `ros-jazzy-launch-testing`,
`ros-jazzy-launch-testing-ament-cmake`, `liburdfdom-tools`,
`libboost-all-dev` for `ypspur_ros2`'s Boost dependency) is either a
normal rosdep-resolvable ROS package or a plain apt package, so it's
handled the same way this repo already handles ROS package deps: apt-get
in the shared `Dockerfile`.

## Decisions (confirmed with instructor)

- **Clone target folder:** `ros2_ws/src/icart-ros2` (matches the
  upstream repo name, consistent with how `open_manipulator`,
  `dynamixel_hardware_interface`, `dynamixel_interfaces`, and
  `DynamixelSDK` folders already match their own repo names). colcon
  discovers the 6 nested packages recursively, same as any other
  multi-package source tree already in this workspace.
- **Gazebo simulation deps:** add them to the shared `Dockerfile`. This
  reverses the existing "out of scope" note, since iCart mini simulation
  support is now needed by an in-workspace package, not a hypothetical
  future one.
- **`yp-spur` build:** add it to the shared `Dockerfile`, at image-build
  time, mirroring `icart-ros2`'s own `Dockerfile` exactly (same source,
  same build steps) rather than re-deriving the steps.

## Changes

### 1. `scripts/clone_repos.sh`

- Replace the `ICART_MINI_REPO_URL="TODO"` block with:
  ```bash
  ICART_ROS2_REPO_URL="https://github.com/CRG-Tohoku/icart-ros2.git"
  ```
  cloned at branch `worktree-ros2-jazzy-migration`.
- Extend `clone_one()` with an optional submodule flag so it can run
  `git clone --recurse-submodules -b <branch> <url> <target>` — needed
  to pull the `ypspur_ros2` submodule on first clone. Keep the existing
  `SKIP: already exists` / `SKIP: TODO` behavior unchanged for the other
  callers.
- New call: `clone_one "icart-ros2" "$ICART_ROS2_REPO_URL" "worktree-ros2-jazzy-migration" --recurse-submodules`

### 2. `Dockerfile`

- Add `libboost-all-dev` to the core tools `apt-get install` block, with
  a one-line comment: needed by `ypspur_ros2` (`find_package(Boost ...
  chrono thread atomic)`).
- Add a new `apt-get install` block (after the existing ROS packages
  block) for packages newly required by iCart mini and not already
  present: `ros-jazzy-ros-gz`, `ros-jazzy-gz-ros2-control`,
  `ros-jazzy-controller-manager`, `ros-jazzy-teleop-twist-joy`,
  `ros-jazzy-joy`, `ros-jazzy-urg-node`, `ros-jazzy-launch-testing`,
  `ros-jazzy-launch-testing-ament-cmake`, `liburdfdom-tools`,
  `python3-pytest`.
- Add a `yp-spur` source-build `RUN` step (before the non-root user
  block): clone `openspur/yp-spur` (shallow), `./configure && make &&
  make install && ldconfig`, then remove the clone — same steps as
  `icart-ros2`'s own `Dockerfile`.
- Update the existing comment (current lines 74-77) that lists Gazebo
  support as "optional/out of scope" — remove that framing; it's
  installed now, for iCart mini.

### 3. `docs/repository_sources.md`

- Replace the iCart mini TODO table row with the resolved entry:
  target folder `ros2_ws/src/icart-ros2`, upstream URL/branch as above,
  a Notes column pointing at the new detail section for the full
  package/submodule breakdown.
- Replace the "iCart mini: no ROS 2 support upstream" section with an
  "iCart mini: ROS 2 Jazzy migration (CRG-Tohoku fork)" section
  covering: why this branch was chosen over the dead upstream and the
  unmaintained community port, the 6-package + submodule structure, the
  two build-time system deps and where they're handled (Dockerfile), and
  a note that this is an active instructor-maintained branch (not a
  pinned release) — re-verify against the branch if it moves.

### 4. `docs/docker_workflow.md`

- Add an "iCart mini (real hardware)" subsection under "Hardware
  access", mirroring the existing "OpenManipulator arm" subsection:
  notes that `icart_mini_driver`'s real-hardware exec deps include a URG
  lidar (`urg_node`) and joystick teleop (`joy`, `teleop_twist_joy`),
  and links back to the safety warning in `docs/setup.md`.

## Verification

1. `bash scripts/docker_build.sh` — image builds cleanly with the new
   apt packages and the `yp-spur` source build.
2. `bash scripts/clone_repos.sh` — clones `icart-ros2` into
   `ros2_ws/src/icart-ros2` with the `ypspur_ros2` submodule populated
   (not an empty directory).
3. Inside the container: `rosdep install --from-paths ros2_ws/src
   --ignore-src -r -y && colcon build --symlink-install` from
   `ros2_ws` — all 6 iCart packages + `ypspur_ros2` build with zero
   failures (this is the actual test of whether `yp-spur` was installed
   correctly and all apt deps were resolved).
4. If the upstream branch has moved since this spec was written,
   re-fetch `package.xml` for all 6 packages plus `ypspur_ros2`'s
   `CMakeLists.txt`/`package.xml` and diff against the dependency list
   in this spec before trusting it.
