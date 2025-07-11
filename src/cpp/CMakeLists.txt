cmake_minimum_required(VERSION 3.30)
project(cpp_ext LANGUAGES CXX)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Python 3.13 COMPONENTS Interpreter Development REQUIRED)
execute_process(
    COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE 
    OUTPUT_VARIABLE nanobind_ROOT
)
find_package(nanobind REQUIRED)

function(create_module MODULE_NAME SOURCE_FILES)
    # Python binding stuff
    nanobind_add_module(${MODULE_NAME} ${SOURCE_FILES})
    nanobind_add_stub(
        ${MODULE_NAME}_stub
        MODULE ${MODULE_NAME}
        OUTPUT ${MODULE_NAME}.pyi
        DEPENDS ${MODULE_NAME}
    )
    
    # Compile options
    set_target_properties(
        ${MODULE_NAME} PROPERTIES
        CXX_VISIBILITY_PRESET "hidden"
        VISIBILITY_INLINES_HIDDEN true
    )
    if (MSVC)
        target_compile_options(
            ${MODULE_NAME} PRIVATE 
            /W4
            /O2
            /GL
            /MP
        )
        target_link_options(
            ${MODULE_NAME} PRIVATE 
            /LTCG
        )
    else()
        target_compile_options(
            ${MODULE_NAME} PRIVATE 
            -fdiagnostics-color=always
            -Wall -Wextra
            -g3
            -O3 -march=native -mtune=native
            -flto -ffunction-sections
        )
    endif()

    # Set install path, default to ${Project}/.cache
    set(EXT_DIR ".cache")
    install(
        TARGETS ${MODULE_NAME}
        DESTINATION ${EXT_DIR}
    )
    install(
        FILES ${CMAKE_CURRENT_BINARY_DIR}/${MODULE_NAME}.pyi
        DESTINATION ${EXT_DIR}
    )
endfunction(create_module)

create_module(freq freq.cpp)
create_module(check check.cpp)