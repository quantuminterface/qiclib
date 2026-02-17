cmake_minimum_required(VERSION 3.23)
project(qicode VERSION 0.0.1 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Find required packages
find_package(protobuf REQUIRED)

# Proto files
# This is a hack to enable conan create as well as building (and testing) locally.
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/qicode")
set(PROTO_BASE_DIR ${CMAKE_CURRENT_SOURCE_DIR})
else()
cmake_path(GET CMAKE_CURRENT_SOURCE_DIR PARENT_PATH PARENT_DIR)
cmake_path(GET PARENT_DIR PARENT_PATH PROTO_BASE_DIR)
endif()

message(STATUS "PROTO_BASE_DIR set to ${PROTO_BASE_DIR}")

cmake_path(APPEND PROTO_BASE_DIR qicode proto OUTPUT_VARIABLE PROTO_SRC_DIR)

file(GLOB PROTO_FILES "${PROTO_SRC_DIR}/*.proto")
message(STATUS "Proto files found: ${PROTO_SRC_DIR}")

set(PROTO_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")

# Ensure the output directory exists
file(MAKE_DIRECTORY "${PROTO_BINARY_DIR}")

# Generate protobuf files
protobuf_generate(
    OUT_VAR PROTO_GENERATED_SRCS
    LANGUAGE cpp
    PROTOS ${PROTO_FILES}
    PROTOC_OUT_DIR "${PROTO_BINARY_DIR}"
    IMPORT_DIRS "${PROTO_BASE_DIR}"
)

add_library(qicode ${PROTO_GENERATED_SRCS})

# Set compiler warning flags
if(MSVC)
    target_compile_options(qicode PRIVATE /W4)
else()
    target_compile_options(qicode PRIVATE -Wall -Wextra -Wpedantic)
endif()

target_include_directories(qicode
    PUBLIC
        $<BUILD_INTERFACE:${PROTO_BINARY_DIR}>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Link protobuf library
target_link_libraries(qicode PUBLIC protobuf::libprotobuf)

# Installation
install(TARGETS qicode)

install(DIRECTORY ${PROTO_GENERATED_SRCS}
    DESTINATION include/qicode/proto
    FILES_MATCHING PATTERN "*.h"
)
