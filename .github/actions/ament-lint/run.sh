#!/bin/bash
set -e

source /opt/ros/${ROS_DISTRO}/setup.bash
./setup.sh
ament_${LINTER} src/
