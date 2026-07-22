# iCart mini ROS 2 Source Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the iCart mini `TODO` source with `CRG-Tohoku/icart-ros2` (branch `worktree-ros2-jazzy-migration`), wiring its 6-package + submodule layout into the existing clone/Docker/docs workflow.

**Architecture:** Extend the existing `clone_one()` helper in `scripts/clone_repos.sh` to support `--recurse-submodules`, add the two build-time system deps this repo needs (`yp-spur` C library, Gazebo apt packages) to the shared `Dockerfile`, and update `docs/repository_sources.md` / `docs/docker_workflow.md` to match — following the same patterns already used for the OpenManipulator arm integration.

**Tech Stack:** Bash, Dockerfile (Ubuntu 24.04 / ROS 2 Jazzy), Markdown docs, colcon/rosdep.

## Global Constraints

- Clone target folder: `ros2_ws/src/icart-ros2` (matches upstream repo name — do not use `icart_mini`).
- Source: `https://github.com/CRG-Tohoku/icart-ros2.git`, branch `worktree-ros2-jazzy-migration`.
- Gazebo simulation deps (`ros-jazzy-ros-gz`, `ros-jazzy-gz-ros2-control`) are added to the shared `Dockerfile` — this reverses the prior "out of scope" note.
- `yp-spur` is built from source in the shared `Dockerfile`, mirroring `icart-ros2`'s own `Dockerfile` build steps exactly (`openspur/yp-spur` → `./configure && make && make install && ldconfig`).
- Spec of record: `docs/superpowers/specs/2026-07-12-icart-ros2-integration-design.md`.

---

### Task 1: `scripts/clone_repos.sh` — add iCart mini source + submodule support

**Files:**
- Modify: `scripts/clone_repos.sh:18-25` (TODO block → real source)
- Modify: `scripts/clone_repos.sh:47-72` (`clone_one()` helper)
- Modify: `scripts/clone_repos.sh:74` (call site)

**Interfaces:**
- Produces: `clone_one()` now accepts a 4th optional positional arg, literal string `"--recurse-submodules"`, which makes it pass `--recurse-submodules` to `git clone`. Callers that omit the 4th arg behave exactly as before.
- Produces: on success, `ros2_ws/src/icart-ros2/` exists with a populated `ypspur_ros2/` subdirectory (not empty) — Task 5 depends on this.

- [ ] **Step 1: Replace the iCart mini TODO block**

In `scripts/clone_repos.sh`, replace lines 18-25:

```bash
# --- iCart mini (mobile base) ------------------------------------------
# Intentionally left as TODO: the upstream repo (open-rdc/icart) has no
# ROS 2 branch at all — every branch is ROS1/catkin (confirmed by
# checking all branches). There is an unofficial, unmaintained community
# ROS2 port (haruyama8940/icart_mini_driver_ros2, last updated 2023,
# untested on Jazzy, missing description/gazebo packages) — see
# docs/repository_sources.md if the instructor wants to evaluate it.
ICART_MINI_REPO_URL="TODO"
```

with:

```bash
# --- iCart mini (mobile base) ------------------------------------------
# CRG-Tohoku/icart-ros2 (branch worktree-ros2-jazzy-migration) is an
# instructor-authored ROS 2 Jazzy migration of open-rdc/icart. It is a
# single repo containing 6 colcon packages (icart_mini,
# icart_mini_description, icart_mini_control, icart_mini_driver,
# icart_mini_gazebo, icart_mini_setup) plus the ypspur_ros2 git
# submodule — colcon discovers all 6 packages recursively once cloned.
# See docs/repository_sources.md for the full breakdown and the Docker
# build-time system deps (yp-spur, Gazebo) this repo requires.
ICART_ROS2_REPO_URL="https://github.com/CRG-Tohoku/icart-ros2.git"
```

- [ ] **Step 2: Add submodule support to `clone_one()`**

Replace the whole `clone_one()` function (current lines 47-72):

```bash
clone_one() {
    local name="$1"
    local url="$2"
    local branch="${3:-}"
    local target="$SRC_DIR/$name"

    if [[ "$url" == *TODO* ]]; then
        echo "SKIP: $name — repository URL not set yet."
        echo "      Edit scripts/clone_repos.sh and set the URL for $name."
        echo "      See docs/repository_sources.md for details."
        return
    fi

    if [ -d "$target" ]; then
        echo "SKIP: $name — $target already exists."
        return
    fi

    if [ -n "$branch" ]; then
        echo "Cloning $name (branch: $branch) into $target ..."
        git clone -b "$branch" "$url" "$target"
    else
        echo "Cloning $name into $target ..."
        git clone "$url" "$target"
    fi
}
```

with:

```bash
clone_one() {
    local name="$1"
    local url="$2"
    local branch="${3:-}"
    local submodules="${4:-}"
    local target="$SRC_DIR/$name"

    if [[ "$url" == *TODO* ]]; then
        echo "SKIP: $name — repository URL not set yet."
        echo "      Edit scripts/clone_repos.sh and set the URL for $name."
        echo "      See docs/repository_sources.md for details."
        return
    fi

    if [ -d "$target" ]; then
        echo "SKIP: $name — $target already exists."
        return
    fi

    local clone_args=()
    [ -n "$branch" ] && clone_args+=(-b "$branch")
    [ "$submodules" = "--recurse-submodules" ] && clone_args+=(--recurse-submodules)

    echo "Cloning $name${branch:+ (branch: $branch)} into $target ..."
    git clone "${clone_args[@]}" "$url" "$target"
}
```

- [ ] **Step 3: Update the call site**

Replace (current line 74):

```bash
clone_one "icart_mini" "$ICART_MINI_REPO_URL"
```

with:

```bash
clone_one "icart-ros2" "$ICART_ROS2_REPO_URL" "worktree-ros2-jazzy-migration" "--recurse-submodules"
```

- [ ] **Step 4: Syntax-check the script**

Run: `bash -n scripts/clone_repos.sh`
Expected: no output, exit code 0.

- [ ] **Step 5: Run it for real and verify the submodule populated**

Run:
```bash
bash scripts/clone_repos.sh
ls ros2_ws/src/icart-ros2
ls ros2_ws/src/icart-ros2/ypspur_ros2
```
Expected: first `ls` lists `icart_mini`, `icart_mini_control`, `icart_mini_description`, `icart_mini_driver`, `icart_mini_gazebo`, `icart_mini_setup`, `ypspur_ros2`, plus repo files (`Dockerfile`, `README.md`, etc.). Second `ls` is **non-empty** (submodule contents present, e.g. `CMakeLists.txt`, `package.xml`) — an empty `ypspur_ros2/` means `--recurse-submodules` didn't take effect.

- [ ] **Step 6: Commit**

```bash
git add scripts/clone_repos.sh
git commit -m "$(cat <<'EOF'
Add iCart mini ROS2 source (CRG-Tohoku/icart-ros2), resolving the TODO

Replaces the placeholder with the instructor's in-progress ROS 2 Jazzy
migration branch. Extends clone_one() with --recurse-submodules
support to pull the ypspur_ros2 submodule alongside the main repo.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `Dockerfile` — add iCart mini system dependencies

**Files:**
- Modify: `Dockerfile:16-38` (core tools block — add `libboost-all-dev`)
- Modify: `Dockerfile:49-83` (new apt block + updated comments)
- Create (inline): new `RUN` step for building `yp-spur` from source

**Interfaces:**
- Consumes: nothing from Task 1 (independently buildable).
- Produces: an image where `ypspur` is discoverable by CMake (`find_package(ypspur 1.20.0)` succeeds) and all rosdep keys needed by the 6 iCart packages + `ypspur_ros2` resolve to already-installed apt packages. Task 5 depends on this.

- [ ] **Step 1: Add `libboost-all-dev` to the core tools block**

In `Dockerfile`, replace lines 16-38:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    git \
    curl \
    wget \
    nano \
    vim \
    tree \
    sudo \
    build-essential \
    cmake \
    pkg-config \
    bash-completion \
    iputils-ping \
    net-tools \
    udev \
    libusb-1.0-0-dev \
    # ^ libusb-1.0-0-dev: needed by DynamixelSDK for USB-serial (U2D2)
    #   access when building the OpenManipulator arm packages from source.
    && rm -rf /var/lib/apt/lists/*
```

with:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    git \
    curl \
    wget \
    nano \
    vim \
    tree \
    sudo \
    build-essential \
    cmake \
    pkg-config \
    bash-completion \
    iputils-ping \
    net-tools \
    udev \
    libusb-1.0-0-dev \
    # ^ libusb-1.0-0-dev: needed by DynamixelSDK for USB-serial (U2D2)
    #   access when building the OpenManipulator arm packages from source.
    libboost-all-dev \
    # ^ libboost-all-dev: needed by ypspur_ros2's CMake
    #   (find_package(Boost ... chrono thread atomic)) — see
    #   docs/repository_sources.md.
    && rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 2: Replace the ROS packages block + stale comments with iCart mini additions**

Replace lines 49-83 (the existing ROS packages `RUN` block through the `tf-transformations` comment) with:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-moveit \
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-rviz2 \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# ros2-control/ros2-controllers above are needed by the OpenManipulator
# arm's dynamixel_hardware_interface package (a ros2_control plugin), and
# by iCart mini's icart_mini_control/icart_mini_gazebo packages.
#
# The OpenManipulator-family source packages themselves — DynamixelSDK,
# dynamixel_interfaces, dynamixel_hardware_interface, and their further
# dependency robotis_interfaces — are intentionally NOT apt-installed
# here. They are cloned as source by scripts/clone_repos.sh into
# ros2_ws/src and built from source by `rosdep install` + `colcon build`
# in scripts/setup_workspace.sh, matching ROBOTIS's own official Jazzy
# Docker workflow (avoids guessing apt package names/versions).
#
# Optional/out of scope for the default setup, not installed here:
# - RealSense camera support (ros-jazzy-realsense2-description, libglfw3-dev)
# If a class needs it, add it here and document why.

# Optional package, not installed by default because availability varies by
# platform/architecture: ros-jazzy-tf-transformations
# If you need it, try installing it manually inside the container with:
#   sudo apt-get update && sudo apt-get install -y ros-jazzy-tf-transformations
# or install it via pip: pip3 install --user tf-transformations

# ---------------------------------------------------------------------------
# iCart mini (mobile base) dependencies — CRG-Tohoku/icart-ros2, see
# docs/repository_sources.md. Includes Gazebo simulation support
# (icart_mini_gazebo), previously out of scope for this image.
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-controller-manager \
    ros-jazzy-teleop-twist-joy \
    ros-jazzy-joy \
    ros-jazzy-urg-node \
    ros-jazzy-launch-testing \
    ros-jazzy-launch-testing-ament-cmake \
    liburdfdom-tools \
    python3-pytest \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# yp-spur: non-ROS C library required by ypspur_ros2's CMake
# (find_package(ypspur 1.20.0 REQUIRED)) — not resolvable by rosdep.
# Built from source here, mirroring CRG-Tohoku/icart-ros2's own Dockerfile.
# ---------------------------------------------------------------------------
RUN git clone --depth 1 https://github.com/openspur/yp-spur.git /tmp/yp-spur \
    && cd /tmp/yp-spur \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /tmp/yp-spur
```

- [ ] **Step 3: Rebuild the image**

Run: `bash scripts/docker_build.sh`
Expected: build completes successfully (exits 0), reaching the final `naming to docker.io/library/2026-tesp-robot-basketball` step with no apt/dpkg errors and no `yp-spur` build failures (`./configure`, `make`, `make install` all succeed).

- [ ] **Step 4: Verify `yp-spur` is discoverable**

Run: `docker compose run --rm --entrypoint "" robot-basketball bash -c "pkg-config --modversion ypspur || find / -iname 'ypspurConfig*.cmake' 2>/dev/null"`
Expected: prints a version string (e.g. `1.20.0`) or lists a found `ypspurConfig.cmake` file — confirms `make install` actually registered the library where CMake's `find_package` will look.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile
git commit -m "$(cat <<'EOF'
Add iCart mini system dependencies to the shared Dockerfile

Adds libboost-all-dev, Gazebo simulation packages, and the remaining
apt-resolvable ROS deps needed by CRG-Tohoku/icart-ros2's 6 packages,
plus a from-source build of the yp-spur C library (required by
ypspur_ros2's CMake, not resolvable via rosdep). Mirrors icart-ros2's
own Dockerfile build steps for yp-spur exactly.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `docs/repository_sources.md` — document the resolved source

**Files:**
- Modify: `docs/repository_sources.md:10` (table row)
- Modify: `docs/repository_sources.md:17-34` (TODO section → resolved section)

**Interfaces:**
- Consumes: nothing (docs-only; describes Task 1/2's outcome).
- Produces: nothing consumed elsewhere — this is the terminal documentation of the decision.

- [ ] **Step 1: Replace the table row**

Replace line 10:

```markdown
| iCart mini | Mobile base drivers, description, bringup, navigation support | `ros2_ws/src/icart_mini` | **TODO** — see below | No ROS 2 branch exists upstream. Left unset in `clone_repos.sh` on purpose. |
```

with:

```markdown
| iCart mini (`icart-ros2`) | Mobile base drivers, description, ros2_control, Gazebo sim, param/udev setup, YP-Spur bridge | `ros2_ws/src/icart-ros2` | https://github.com/CRG-Tohoku/icart-ros2 (branch: `worktree-ros2-jazzy-migration`) | 6 colcon packages + `ypspur_ros2` git submodule in one repo — see below. |
```

- [ ] **Step 2: Replace the TODO section**

Replace the `## iCart mini: no ROS 2 support upstream` section (lines 17-34) with:

```markdown
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
```

- [ ] **Step 3: Sanity-check the table renders**

Run: `grep -c '^|' docs/repository_sources.md`
Expected: a number ≥ 6 (header + separator + 5 data rows), confirming no broken `|` syntax was introduced. Visually confirm the new "Role" sub-table under the new section also has matching `|` counts per row.

- [ ] **Step 4: Commit**

```bash
git add docs/repository_sources.md
git commit -m "$(cat <<'EOF'
Document the resolved iCart mini source in repository_sources.md

Replaces the TODO row/section with CRG-Tohoku/icart-ros2's confirmed
6-package + submodule structure and the two build-time system deps
(yp-spur, Gazebo) now handled in the Dockerfile.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `docs/docker_workflow.md` — iCart mini real-hardware note

**Files:**
- Modify: `docs/docker_workflow.md` (insert new subsection between "### OpenManipulator arm (U2D2 USB-serial adapter)" and "## ROS 2 networking")

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed elsewhere — terminal documentation.

- [ ] **Step 1: Insert the new subsection**

In `docs/docker_workflow.md`, find this existing text:

```markdown
### OpenManipulator arm (U2D2 USB-serial adapter)

The arm's U2D2 USB-serial adapter needs a udev rule so it shows up with
consistent permissions. ROBOTIS provides this in the cloned
`open_manipulator` repo — after running `scripts/clone_repos.sh`, follow
its own instructions to install the rule (typically
`open_manipulator_bringup/open-manipulator-cdc.rules` plus the
`om_create_udev_rules.py` helper script). This is not automated by this
repository — check the arm's own README for the current steps before
connecting it.

## ROS 2 networking
```

and replace it with:

```markdown
### OpenManipulator arm (U2D2 USB-serial adapter)

The arm's U2D2 USB-serial adapter needs a udev rule so it shows up with
consistent permissions. ROBOTIS provides this in the cloned
`open_manipulator` repo — after running `scripts/clone_repos.sh`, follow
its own instructions to install the rule (typically
`open_manipulator_bringup/open-manipulator-cdc.rules` plus the
`om_create_udev_rules.py` helper script). This is not automated by this
repository — check the arm's own README for the current steps before
connecting it.

### iCart mini (URG lidar + joystick)

`icart_mini_driver` (real hardware) depends on a URG lidar (`urg_node`)
and joystick teleop (`joy`, `teleop_twist_joy`) in addition to the
YP-Spur motor-controller bridge (`ypspur_ros2`). Like the OpenManipulator
arm, these are real-hardware components: don't launch `icart_mini_driver`
until the instructor confirms it's safe (see
[docs/setup.md](setup.md#safety-warning)). `icart_mini_setup` (cloned
alongside the driver) has scripts to generate the udev rules and
parameter files these depend on — see its README under
`ros2_ws/src/icart-ros2/icart_mini_setup`.

## ROS 2 networking
```

- [ ] **Step 2: Confirm the file still has exactly one `## ROS 2 networking` heading**

Run: `grep -c '^## ROS 2 networking' docs/docker_workflow.md`
Expected: `1` (confirms the replace didn't duplicate or drop the following section).

- [ ] **Step 3: Commit**

```bash
git add docs/docker_workflow.md
git commit -m "$(cat <<'EOF'
Document iCart mini real-hardware deps in docker_workflow.md

Adds a subsection mirroring the existing OpenManipulator one, covering
icart_mini_driver's lidar/joystick real-hardware pieces and pointing
back to the safety warning before connecting hardware.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: End-to-end verification

**Files:** none (verification only — no new changes).

**Interfaces:**
- Consumes: Task 1's cloned `ros2_ws/src/icart-ros2/` (with populated submodule) and Task 2's rebuilt image (with `yp-spur` installed and all apt deps present).

- [ ] **Step 1: Confirm the clone and image are both current**

Run:
```bash
ls ros2_ws/src/icart-ros2/ypspur_ros2/CMakeLists.txt
docker images 2026-tesp-robot-basketball --format '{{.CreatedSince}}'
```
Expected: the file exists (Task 1 done); the image was created recently (Task 2 done). If either is missing/stale, re-run `bash scripts/clone_repos.sh` and/or `bash scripts/docker_build.sh` first.

- [ ] **Step 2: rosdep install + full colcon build inside the container**

Run:
```bash
docker compose run --rm robot-basketball bash -lc \
  "source /opt/ros/jazzy/setup.bash && cd ros2_ws && rosdep install --from-paths src --ignore-src -r -y && colcon build --symlink-install"
```
Expected: `rosdep install` reports no unresolved keys for any `icart_mini*` or `ypspur_ros2` package (spot-check the output for `ypspur_ros2` — it should NOT appear as unresolved, since `yp-spur` is a system library, not a rosdep key, so rosdep has nothing to do for it). `colcon build` finishes with **0 failed** packages, and its summary lists all 7 new packages (`icart_mini`, `icart_mini_control`, `icart_mini_description`, `icart_mini_driver`, `icart_mini_gazebo`, `icart_mini_setup`, `ypspur_ros2`) as finished successfully.

- [ ] **Step 3: If anything failed, diagnose before moving on**

If `colcon build` reports a failure for `ypspur_ros2` specifically, re-run Task 2 Step 4 (`pkg-config --modversion ypspur`) to confirm the library is actually installed in the image — a failure here means the `yp-spur` `make install` step didn't complete or didn't register with CMake/pkg-config, and Task 2 needs another look before continuing.

If `colcon build` reports a failure for `icart_mini_gazebo` specifically, check that `ros-jazzy-ros-gz` and `ros-jazzy-gz-ros2-control` actually installed (re-run Task 2 Step 3's build log, search for those package names) — an apt name mismatch for the current Jazzy release would show up here first.

- [ ] **Step 4: Confirm no regressions in previously-working packages**

Run:
```bash
docker compose run --rm robot-basketball bash -lc \
  "source /opt/ros/jazzy/setup.bash && cd ros2_ws && colcon build --symlink-install --packages-select open_manipulator dynamixel_hardware_interface dynamixel_interfaces DynamixelSDK"
```
Expected: these still build successfully — confirms the new `libboost-all-dev` / apt additions in Task 2 didn't break the existing OpenManipulator packages.

No commit for this task — it's verification of Tasks 1-4's already-committed changes.
