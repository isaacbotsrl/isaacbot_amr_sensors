cmake_minimum_required(VERSION 3.10)
project(isaacbot_amr_realsense)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/attach_camera.sh DESTINATION lib/${PROJECT_NAME})

ament_package()
