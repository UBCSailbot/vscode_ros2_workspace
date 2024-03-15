import os

import yaml

NET_DIR = os.path.join(
    os.getenv("ROS_WORKSPACE", default="/workspaces/sailbot_workspace"), "src/network_systems"
)
ROS_INFO_FILE = os.path.join(NET_DIR, "ros_info.yaml")

GEN_HDR_FILE = os.path.join(NET_DIR, "lib/cmn_hdrs/ros_info.h")
GEN_FILE_WARN = f"FILE GENERATED BY {__file__} using {ROS_INFO_FILE} - DO NOT EDIT"

GEN_HDR_PREAMBLE = f"""
// {GEN_FILE_WARN}
#pragma once
"""
GEN_HDR_FILE_TOPICS_START = """
namespace ros_topics
{
"""
GEN_HDR_FILE_TOPICS_END = "}; // namespace ros_topics\n"
GEN_HDR_FILE_NODES_START = """
namespace ros_nodes
{
"""
GEN_HDR_FILE_NODES_END = "}; // namespace ros_nodes\n"

GEN_PYTHON_FILE = os.path.join(NET_DIR, "launch/ros_info.py")
GEN_PYTHON_PREAMBLE = f"# {GEN_FILE_WARN}\n"


def populate_hdr(hdr_file_obj, info_target):
    for k, v in info_target.items():
        hdr_file_obj.write(f'static constexpr auto {k} = "{v}";\n')


def populate_py_nodes(py_file_obj, info_target):
    for k, v in info_target.items():
        py_file_obj.write(f'{k}_NODE = "{v}"\n')


def main():
    with open(ROS_INFO_FILE, "r") as f:
        info = yaml.safe_load(f)

        with open(GEN_HDR_FILE, "w+") as out_hdr:
            out_hdr.write(GEN_HDR_PREAMBLE)

            out_hdr.write(GEN_HDR_FILE_TOPICS_START)
            populate_hdr(out_hdr, info["ros_topics"])
            out_hdr.write(GEN_HDR_FILE_TOPICS_END)

            out_hdr.write(GEN_HDR_FILE_NODES_START)
            populate_hdr(out_hdr, info["ros_nodes"])
            out_hdr.write(GEN_HDR_FILE_NODES_END)

        with open(GEN_PYTHON_FILE, "w+") as out_py:
            out_py.write(GEN_PYTHON_PREAMBLE)
            populate_py_nodes(out_py, info["ros_nodes"])


if __name__ == "__main__":
    main()
