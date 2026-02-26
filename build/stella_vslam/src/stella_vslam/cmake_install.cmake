# Install script for directory: /home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam

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
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libstella_vslam.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libstella_vslam.so")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libstella_vslam.so"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/lib/libstella_vslam.so")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libstella_vslam.so" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libstella_vslam.so")
    file(RPATH_CHANGE
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libstella_vslam.so"
         OLD_RPATH "/usr/local/lib:"
         NEW_RPATH "")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libstella_vslam.so")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/stella_vslam" TYPE FILE FILES
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/config.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/global_optimization_module.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/mapping_module.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/system.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/tracking_module.h"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/src/stella_vslam/type.h"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/stella_vslam/3rd/json/include/nlohmann" TYPE FILE FILES
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/3rd/json/include/nlohmann/json.hpp"
    "/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/stella_vslam/3rd/json/include/nlohmann/json_fwd.hpp"
    )
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/camera/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/data/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/feature/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/initialize/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/io/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/marker_detector/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/marker_model/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/match/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/module/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/optimize/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/publish/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/solve/cmake_install.cmake")
  include("/home/ren/workspaces/turtlebot3_ws/src/turtlebot-maze/build/stella_vslam/src/stella_vslam/util/cmake_install.cmake")

endif()

