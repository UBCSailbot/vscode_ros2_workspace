import os
from typing import Dict, List

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_context import LaunchContext
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.logging import launch_config
from launch.substitutions import LaunchConfiguration

# TODO: Add the controller package when it is ready
PRODUCTION_ROS_PACKAGES = ["local_pathfinding", "network_systems"]
SIMULATION_ROS_PACKAGES = ["boat_simulator", "local_pathfinding", "network_systems"]

# Add launch arguments here and edit launch_setup() to use new argument(s)
# if needed for global setup.
# TODO: Pass global arguments to children launch files.
GLOBAL_LAUNCH_ARGUMENTS = [
    # put node log files in same directory as launch log files
    # ref: https://github.com/ros2/launch/issues/551#issuecomment-982146452
    SetEnvironmentVariable('ROS_LOG_DIR', launch_config.log_dir),
    # ref: https://answers.ros.org/question/311471/selecting-log-level-in-ros2-launch-file/
    DeclareLaunchArgument(
        name='log_level',
        default_value=['info'],
        description='Logging level',
    ),
]
LAUNCH_ARGUMENTS = [
    DeclareLaunchArgument(
        name="mode",
        default_value="simulation",
        choices=["production", "simulation"],
        description="System mode.",
    ),
]


def generate_launch_description() -> LaunchDescription:
    """Entry point for the launch file. Invokes launch files from all workspace ROS packages.

    Returns:
        LaunchDescription: A collection of entities representing the behavior of the system.
    """
    launch_description = LaunchDescription(
        [
            *LAUNCH_ARGUMENTS,
            *GLOBAL_LAUNCH_ARGUMENTS,
            OpaqueFunction(function=launch_setup),
        ]
    )
    return launch_description


def launch_setup(context: LaunchContext, *args, **kwargs) -> List[IncludeLaunchDescription]:
    """Gathers launch descriptions from the workspace ROS packages to launch. Invoking this
    function from an OpaqueFunction object allows for immediate access to ROS parameters passed
    to this launch file.

    Args:
        context (LaunchContext): The runtime context from the entity invoking this function.

    Returns:
        List[IncludeLaunchDescription]: A list of launch descriptions from ROS packages to be run.
    """
    launch_args = parse_launch_args(context=context)
    ros_package_list = get_running_ros_packages(mode=launch_args["mode"])
    include_launch_descriptions = get_include_launch_descriptions(ros_packages=ros_package_list)
    return include_launch_descriptions


def parse_launch_args(context: LaunchContext) -> Dict[str, str]:
    """Parses ROS arguments from a runtime context.

    Args:
        context (LaunchContext): The context to be parsed.

    Returns:
        Dict[str, str]: A dict containing arguments, where the keys are argument names and the
        values are the argument values.
    """
    parsed_args = dict()
    for argument in LAUNCH_ARGUMENTS:
        parsed_args[argument.name] = LaunchConfiguration(argument.name).perform(context)
    return parsed_args


def get_include_launch_descriptions(ros_packages: List[str]) -> List[IncludeLaunchDescription]:
    """Construct include launch descriptions for the indicated ROS packages.

    Args:
        ros_packages (List[str]): List of ROS packages names to be included.

    Returns:
        List[IncludeLaunchDescription]: List of include launch descriptons for each ROS package.
    """
    ros_packages_dir = os.path.join(os.getenv("ROS_WORKSPACE"), "src")
    package_include_launch_descriptions = list()
    for package in ros_packages:
        launch_file_abs_path = os.path.join(ros_packages_dir, package, 'launch', 'main_launch.py')
        include_launch_description = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file_abs_path)
        )
        package_include_launch_descriptions.append(include_launch_description)
    return package_include_launch_descriptions


def get_running_ros_packages(mode: str) -> List[str]:
    """Gets the names of the ROS packages to be launched depending on an indicated mode.

    Args:
        mode (str): The system mode upon launch. Must be one of 'production', 'simulation'.

    Raises:
        ValueError: Raised when an invalid mode is passed.

    Returns:
        List[str]: List of ROS package names to be launched.
    """
    match mode:
        case "production":
            return PRODUCTION_ROS_PACKAGES
        case "simulation":
            return SIMULATION_ROS_PACKAGES
        case _:
            raise ValueError("Invalid launch mode. Must be one of 'production', 'simulation'.")
