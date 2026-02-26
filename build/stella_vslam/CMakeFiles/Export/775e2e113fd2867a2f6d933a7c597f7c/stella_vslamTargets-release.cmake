#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "stella_vslam::stella_vslam" for configuration "Release"
set_property(TARGET stella_vslam::stella_vslam APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(stella_vslam::stella_vslam PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libstella_vslam.so"
  IMPORTED_SONAME_RELEASE "libstella_vslam.so"
  )

list(APPEND _cmake_import_check_targets stella_vslam::stella_vslam )
list(APPEND _cmake_import_check_files_for_stella_vslam::stella_vslam "${_IMPORT_PREFIX}/lib/libstella_vslam.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
