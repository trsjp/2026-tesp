# Troubleshooting

## Docker not installed

- **Symptom:** `docker: command not found`.
- **Likely cause:** Docker Engine is not installed.
- **First checks:** `which docker`.
- **Possible fix:** Install Docker following the official docs:
  https://docs.docker.com/engine/install/

## Docker permission denied

- **Symptom:** `permission denied while trying to connect to the Docker
  daemon socket`.
- **Likely cause:** Your user is not in the `docker` group.
- **First checks:** `groups $USER`.
- **Possible fix:** Add your user to the `docker` group and re-login, or
  prefix Docker commands with `sudo` (not recommended long-term).

## docker compose unavailable

- **Symptom:** `docker compose: command not found` or "unknown command".
- **Likely cause:** The Compose plugin is not installed, or you are using
  the legacy standalone `docker-compose` binary.
- **First checks:** `docker compose version`.
- **Possible fix:** Install the Compose plugin:
  https://docs.docker.com/compose/install/

## rviz2 cannot open display

- **Symptom:** `Could not connect to display` or similar when running
  `rviz2` inside the container.
- **Likely cause:** X11 forwarding is not set up.
- **First checks:** Is `DISPLAY` set on the host? Did you run
  `xhost +local:docker`?
- **Possible fix:** On Linux, run `xhost +local:docker` on the host before
  starting the container. On macOS/Windows, install and configure an X
  server (XQuartz/VcXsrv) first.

## ros2 command not found

- **Symptom:** `ros2: command not found`.
- **Likely cause:** ROS 2 is not sourced in the current shell.
- **First checks:** `echo $ROS_DISTRO`.
- **Possible fix:** `source /opt/ros/jazzy/setup.bash`.

## colcon command not found

- **Symptom:** `colcon: command not found`.
- **Likely cause:** `python3-colcon-common-extensions` is not installed.
- **First checks:** `which colcon`.
- **Possible fix:** Use the Docker image (already includes colcon), or
  install it natively: `sudo apt-get install python3-colcon-common-extensions`.

## rosdep command not found

- **Symptom:** `rosdep: command not found`.
- **Likely cause:** `python3-rosdep` is not installed.
- **First checks:** `which rosdep`.
- **Possible fix:** Use the Docker image, or install natively:
  `sudo apt-get install python3-rosdep`.

## Package not found after build

- **Symptom:** `ros2 run <package> ...` or `ros2 launch <package> ...`
  fails with "package not found".
- **Likely cause:** The workspace overlay was not sourced after building.
- **First checks:** Did you run `source ros2_ws/install/setup.bash` after
  `colcon build`?
- **Possible fix:** Source the overlay: `source ros2_ws/install/setup.bash`.

## Forgot to source install/setup.bash

- **Symptom:** New packages or changes don't seem to take effect.
- **Likely cause:** The current shell still has the old (or no) overlay
  sourced.
- **First checks:** Open a fresh terminal/container shell.
- **Possible fix:** `source ros2_ws/install/setup.bash` in every new shell
  that needs the workspace.

## Permission denied editing files created by the container

- **Symptom:** Files under `ros2_ws` (e.g. `build/`, `install/`, or a repo
  cloned from inside the container) can't be edited or deleted from the
  host without `sudo`.
- **Likely cause:** The container's `ros` user was built with a UID/GID
  that doesn't match your host user, so files it creates on the
  bind-mounted `/workspace` are owned by a different UID.
- **First checks:** `ls -ln ros2_ws` on the host and compare the numeric
  owner to `id -u` / `id -g` for your user.
- **Possible fix:** Rebuild the image so it matches your current host
  user: `bash scripts/docker_build.sh` (it auto-detects your UID/GID).
  Prefer cloning external repos on the host with `scripts/clone_repos.sh`
  before starting the container, rather than inside it, to avoid this
  case entirely.

## USB/serial permission issue

- **Symptom:** `Permission denied` opening `/dev/ttyUSB0` or similar.
- **Likely cause:** The container user is not in the `dialout` group, or
  the device was not passed into the container.
- **First checks:** `ls -l /dev/ttyUSB0` on the host; is `devices:` set in
  `docker-compose.yml`?
- **Possible fix:** Add the device under `devices:` and `dialout` under
  `group_add:` in `docker-compose.yml` (see
  [docs/docker_workflow.md](docker_workflow.md#hardware-access)).

## ROS_DOMAIN_ID mismatch

- **Symptom:** Two machines that should see each other's topics don't.
- **Likely cause:** They are using different `ROS_DOMAIN_ID` values.
- **First checks:** `echo $ROS_DOMAIN_ID` on each machine.
- **Possible fix:** Set the same `ROS_DOMAIN_ID` on all machines that need
  to communicate.

## Robot not visible over network

- **Symptom:** `ros2 node list` / `ros2 topic list` don't show the
  robot's nodes/topics.
- **Likely cause:** Network mode, `ROS_DOMAIN_ID`, or firewall issue.
- **First checks:** Same `ROS_DOMAIN_ID`? Same network? Is host networking
  enabled?
- **Possible fix:** Confirm host networking is active in
  `docker-compose.yml` and that both machines are on the same LAN/subnet.

## Robot does not move when /cmd_vel is published

- **Symptom:** Publishing to `/cmd_vel` has no effect.
- **Likely cause:** Base driver not running, wrong topic name/namespace,
  or an active safety stop.
- **First checks:** `ros2 topic list` (is `/cmd_vel` there?), `ros2 topic
  echo /cmd_vel` (are messages arriving?), is the e-stop engaged?
- **Possible fix:** Confirm the base driver node is running and subscribed
  to the correct topic; check for an active emergency stop.

## /joint_states not changing

- **Symptom:** Arm joint values appear frozen.
- **Likely cause:** Joint state publisher or arm driver not running, or
  arm is not powered.
- **First checks:** `ros2 topic echo /joint_states`; is the arm driver
  node alive (`ros2 node list`)?
- **Possible fix:** Start/restart the arm driver; confirm arm power and
  connection.

## Nav2 does not localize

- **Symptom:** The robot's estimated pose in Nav2/RViz does not match its
  real position.
- **Likely cause:** Missing or incorrect initial pose, bad map, or sensor
  data not arriving.
- **First checks:** Is `/scan` publishing? Was an initial pose set in
  RViz?
- **Possible fix:** Set the initial pose estimate in RViz; confirm laser
  data and map are being published correctly.

## MoveIt cannot plan

- **Symptom:** Motion planning requests fail or time out.
- **Likely cause:** Missing/incorrect MoveIt configuration for the arm,
  or `/joint_states` not available.
- **First checks:** Is the MoveIt config for this arm present and correct?
  Is `/joint_states` publishing?
- **Possible fix:** Confirm the arm's MoveIt configuration package is
  built and launched; confirm `/tf` and `/joint_states` are available.
