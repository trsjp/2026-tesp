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
    ros-jazzy-xacro \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-rviz2 \
    ros-jazzy-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*

# Optional package, not installed by default because availability varies by
# platform/architecture: ros-jazzy-tf-transformations
# If you need it, try installing it manually inside the container with:
#   sudo apt-get update && sudo apt-get install -y ros-jazzy-tf-transformations
# or install it via pip: pip3 install --user tf-transformations

# ---------------------------------------------------------------------------
# Non-root user
# ---------------------------------------------------------------------------
RUN useradd -m -s /bin/bash ros \
    && usermod -aG sudo ros \
    && echo "ros ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Source ROS 2 (and the workspace overlay, once built) automatically
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/ros/.bashrc \
    && echo "if [ -f /workspace/ros2_ws/install/setup.bash ]; then source /workspace/ros2_ws/install/setup.bash; fi" >> /home/ros/.bashrc \
    && chown ros:ros /home/ros/.bashrc

USER ros
WORKDIR /workspace

CMD ["bash"]
