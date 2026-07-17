# TESP Robot Basketball development image
#
# Base: ROS 2 Jazzy on Ubuntu 24.04.
# This image provides the tools needed to build and test the workspace.
# It does NOT copy the repository source into the image — the repository is
# mounted at /workspace via docker-compose.yml, so edits on the host are
# immediately visible inside the container.

FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------------------
# Core development tools
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# ROS 2 packages used by this project (Nav2, MoveIt, teleop, visualization)
#
# These are installed with apt-get so a missing package fails the build
# loudly rather than silently producing a broken environment. If a package
# in this list is unavailable for the current ROS distro/architecture,
# remove it from the list below and note it in docs/troubleshooting.md
# instead of leaving the Docker build fragile.
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-moveit \
    ros-jazzy-moveit-py \
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-rviz2 \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-joy \
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

# ---------------------------------------------------------------------------
# Non-root user
#
# USER_UID/USER_GID are passed as build args (see docker-compose.yml and
# scripts/docker_build.sh) so the "ros" user inside the container matches
# the host user running Docker. This keeps files created inside the
# container (colcon build output, cloned repos under ros2_ws/src) owned by
# the student's own host user on the bind-mounted /workspace, instead of a
# foreign UID that would need sudo to edit or delete from the host.
# ---------------------------------------------------------------------------
ARG USER_UID=1000
ARG USER_GID=1000

RUN if getent passwd "${USER_UID}" > /dev/null; then \
        userdel -r "$(getent passwd "${USER_UID}" | cut -d: -f1)"; \
    fi \
    && if getent group "${USER_GID}" > /dev/null; then \
        groupdel "$(getent group "${USER_GID}" | cut -d: -f1)"; \
    fi \
    && groupadd -g "${USER_GID}" ros \
    && useradd -m -u "${USER_UID}" -g "${USER_GID}" -s /bin/bash ros \
    && usermod -aG sudo ros \
    && echo "ros ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Source ROS 2 (and the workspace overlay, once built) automatically
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/ros/.bashrc \
    && echo "if [ -f /workspace/ros2_ws/install/setup.bash ]; then source /workspace/ros2_ws/install/setup.bash; fi" >> /home/ros/.bashrc \
    && chown ros:ros /home/ros/.bashrc

USER ros
WORKDIR /workspace

CMD ["bash"]
