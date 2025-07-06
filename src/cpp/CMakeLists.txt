cmake_minimum_required(VERSION 3.30)
project(cpp_ext LANGUAGES CXX)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python 3.13 COMPONENTS Interpreter Development REQUIRED)
execute_process(
    COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_ROOT
)
find_package(nanobind REQUIRED)

nanobind_add_module(freq freq.cpp)
nanobind_add_stub(
    freq_stub
    MODULE freq
    OUTPUT freq.pyi
    DEPENDS freq
)
target_compile_options(
    freq PRIVATE 
    -Wall -Wextra 
    -O3 -march=native -mtune=native
    -flto -ffunction-sections
)
set_target_properties(
    freq PROPERTIES
    CXX_VISIBILITY_PRESET "hidden"
    VISIBILITY_INLINES_HIDDEN true
)

set(EXT_DIR ".cache")
install(
    TARGETS freq
    DESTINATION ${EXT_DIR}
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/freq.pyi
    DESTINATION ${EXT_DIR}
)