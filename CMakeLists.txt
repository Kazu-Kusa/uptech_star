cmake_minimum_required(VERSION 3.1)
project(my_project)

# 设置编译输出目录
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/lib)

# 设置临时文件目录
set(TEMP_DIR ${CMAKE_CURRENT_SOURCE_DIR}/temp)

# 创建临时文件目录
file(MAKE_DIRECTORY ${TEMP_DIR})

# 添加源文件
file(GLOB SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/src/*.c)

# 生成动态库
foreach(SOURCE ${SOURCES})
    get_filename_component(SOURCE_NAME ${SOURCE} NAME_WE)
    add_library(${SOURCE_NAME} SHARED ${SOURCE})
    target_compile_options(${SOURCE_NAME} PRIVATE -Wall -Wextra)
    target_link_libraries(${SOURCE_NAME} PRIVATE m)
    set_target_properties(${SOURCE_NAME} PROPERTIES
        CMAKE_TEMP_DIR ${TEMP_DIR}
    )
endforeach()
