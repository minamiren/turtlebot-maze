# Install script for directory: /home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/install/stella_vslam")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/stella_vslam/optimize/internal/se3" TYPE FILE FILES
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/equirectangular_pose_opt_edge.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/equirectangular_reproj_edge.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/perspective_pose_opt_edge.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/perspective_reproj_edge.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/pose_opt_edge_wrapper.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/reproj_edge_wrapper.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/shot_vertex.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/optimize/internal/se3/shot_vertex_container.h"
    )
endif()

