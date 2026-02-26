# Install script for directory: /home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module

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
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/stella_vslam/module" TYPE FILE FILES
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/frame_tracker.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/initializer.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/keyframe_inserter.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/local_map_cleaner.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/local_map_updater.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/loop_bundle_adjuster.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/loop_detector.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/marker_initializer.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/relocalizer.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/two_view_triangulator.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/module/type.h"
    )
endif()

