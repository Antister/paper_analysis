cmake_minimum_required(VERSION 3.28)
project(freq LANGUAGES CXX)

find_package(Python 3.13 COMPONENTS Interpreter Development REQUIRED)

execute_process(
    COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT
)
find_package(nanobind REQUIRED)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

nanobind_add_module(freq freq.cpp)

target_compile_options(freq PRIVATE -Wall -Wextra -flto -O3 -march=native -mtune=native)