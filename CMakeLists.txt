cmake_minimum_required(VERSION 3.16)
project(lvgl-ui-automation LANGUAGES C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Add compile definitions for Windows
if(WIN32)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    add_definitions(-D_WIN32_WINNT=0x0601)
endif()

# Find required packages
if(WIN32)
    # For Windows, try to find SDL2 in our third_party directory first, then fallback to system
    set(SDL2_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/sdl2/SDL2-devel-2.30.8-VC/SDL2-2.30.8)
    
    find_path(SDL2_INCLUDE_DIR SDL.h 
        HINTS 
            ENV SDL2DIR 
            ${SDL2_DIR}
            ${CMAKE_TOOLCHAIN_FILE}/../../../installed/x64-windows  # vcpkg path
        PATH_SUFFIXES include
    )
    
    if(CMAKE_SIZEOF_VOID_P EQUAL 8)
        set(SDL2_LIB_SUFFIX "x64")
    else()
        set(SDL2_LIB_SUFFIX "x86")
    endif()
    
    find_library(SDL2_LIBRARY 
        NAMES SDL2 
        HINTS 
            ENV SDL2DIR 
            ${SDL2_DIR}
        PATH_SUFFIXES lib/${SDL2_LIB_SUFFIX} lib
    )
    
    find_library(SDL2MAIN_LIBRARY 
        NAMES SDL2main 
        HINTS 
            ENV SDL2DIR 
            ${SDL2_DIR}
        PATH_SUFFIXES lib/${SDL2_LIB_SUFFIX} lib
    )
    
    if(NOT SDL2_INCLUDE_DIR OR NOT SDL2_LIBRARY OR NOT SDL2MAIN_LIBRARY)
        message(WARNING "SDL2 not found. Please install SDL2 development libraries or set SDL2DIR environment variable")
        message(WARNING "For Windows: Install SDL2 from https://www.libsdl.org/download-2.0.php")
        message(WARNING "Or use vcpkg: vcpkg install sdl2")
        message(STATUS "Looking for SDL2 in: ${SDL2_DIR}")
        message(STATUS "SDL2_INCLUDE_DIR: ${SDL2_INCLUDE_DIR}")
        message(STATUS "SDL2_LIBRARY: ${SDL2_LIBRARY}")
        message(STATUS "SDL2MAIN_LIBRARY: ${SDL2MAIN_LIBRARY}")
    else()
        message(STATUS "Found SDL2: ${SDL2_INCLUDE_DIR}")
    endif()
    
    set(SDL2_LIBRARIES ${SDL2_LIBRARY} ${SDL2MAIN_LIBRARY})
else()
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(SDL2 REQUIRED sdl2)
endif()

# Find pthread (required for TCP server)
if(WIN32)
    set(PTHREAD_LIBRARIES "")  # Windows uses native threading
else()
    find_package(Threads REQUIRED)
    set(PTHREAD_LIBRARIES Threads::Threads)
endif()

# LVGL configuration
set(LVGL_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/lvgl)
if(EXISTS ${LVGL_DIR})
    # Set LVGL configuration BEFORE adding subdirectory (this is critical!)
    set(LV_CONF_BUILD_DISABLE_EXAMPLES ON CACHE BOOL "Disable examples" FORCE)
    set(LV_CONF_BUILD_DISABLE_DEMOS ON CACHE BOOL "Disable demos" FORCE)
    
    # Use the CORRECT CONFIG_ prefixed options that LVGL actually uses
    set(CONFIG_LV_BUILD_DEMOS OFF CACHE BOOL "Build LVGL demos" FORCE)
    set(CONFIG_LV_BUILD_EXAMPLES OFF CACHE BOOL "Build LVGL examples" FORCE)
    set(CONFIG_LV_USE_THORVG_INTERNAL OFF CACHE BOOL "Use internal ThorVG" FORCE)
    
    # Point LVGL to our configuration file
    set(LV_CONF_PATH ${CMAKE_CURRENT_SOURCE_DIR}/lv_conf.h CACHE STRING "Path to lv_conf.h" FORCE)
    
    add_subdirectory(${LVGL_DIR})
    
    # Ensure LVGL can find SDL2 headers
    target_include_directories(lvgl PUBLIC ${SDL2_INCLUDE_DIR})
    
    
    # Suppress warnings for LVGL to get clean build output
    if(MSVC)
        target_compile_options(lvgl PRIVATE
            /wd4005  # macro redefinition
            /wd4819  # character encoding 
            /wd4996  # deprecated functions
            /wd4244  # conversion warnings
            /wd4267  # size_t conversion
            /W1      # minimal warnings for LVGL
        )
        
        # Also suppress for lvgl_demos and lvgl_examples if they exist
        if(TARGET lvgl_demos)
            target_compile_options(lvgl_demos PRIVATE /W0)  # No warnings for demos
        endif()
        if(TARGET lvgl_examples)
            target_compile_options(lvgl_examples PRIVATE /W0)  # No warnings for examples
        endif()
    endif()
else()
    message(WARNING "LVGL not found at ${LVGL_DIR}")
    message(WARNING "Please run: git submodule add https://github.com/lvgl/lvgl.git third_party/lvgl")
    message(WARNING "Or clone LVGL manually into third_party/lvgl")
endif()

# LodePNG for PNG encoding
set(LODEPNG_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/lodepng)
if(NOT EXISTS ${LODEPNG_DIR})
    message(STATUS "LodePNG not found, will download during build")
endif()

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
    ${SDL2_INCLUDE_DIR}
)

# Source files
set(SOURCES
    src/main.c
    src/ui_watch.c
    src/test_harness.c
    src/tcp_server.c
    src/screenshot.c
)

# Add LodePNG source if available
if(EXISTS ${LODEPNG_DIR}/lodepng.cpp)
    list(APPEND SOURCES ${LODEPNG_DIR}/lodepng.cpp)
endif()

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Link libraries
if(EXISTS ${LVGL_DIR})
    # Enable LVGL for visual emulator
    target_compile_definitions(${PROJECT_NAME} PRIVATE HAVE_LVGL=1)
    
    target_link_libraries(${PROJECT_NAME} 
        lvgl
        ${SDL2_LIBRARIES}
        ${PTHREAD_LIBRARIES}
    )
else()
    # Fallback without LVGL for initial setup
    target_link_libraries(${PROJECT_NAME} 
        ${SDL2_LIBRARIES}
        ${PTHREAD_LIBRARIES}
    )
endif()

# Windows specific libraries
if(WIN32)
    target_link_libraries(${PROJECT_NAME} ws2_32 winmm)
    
    # Copy SDL2.dll to output directory
    if(EXISTS ${SDL2_DIR}/lib/x64/SDL2.dll)
        add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${SDL2_DIR}/lib/x64/SDL2.dll"
                $<TARGET_FILE_DIR:${PROJECT_NAME}>)
        message(STATUS "SDL2.dll will be copied to output directory")
    endif()
    
    # Suppress common MSVC warnings for better build output
    target_compile_options(${PROJECT_NAME} PRIVATE
        /wd4005  # macro redefinition
        /wd4819  # character encoding
        /wd4996  # deprecated functions
        /W3      # reasonable warning level for our code
    )
    
    # Set global build options for quieter output
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} /nologo")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /nologo")
endif()

# Compiler flags
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(${PROJECT_NAME} PRIVATE -Wall -Wextra)
endif()

# Create a custom target to download dependencies
add_custom_target(download-deps
    COMMAND ${CMAKE_COMMAND} -E echo "Downloading LodePNG..."
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_SOURCE_DIR}/third_party/lodepng
    COMMENT "Downloading dependencies"
)

# Print build instructions
message(STATUS "")
message(STATUS "Build Instructions:")
message(STATUS "==================")
message(STATUS "1. Install dependencies:")
if(WIN32)
    message(STATUS "   Windows: Install SDL2 development libraries")
    message(STATUS "   - Download from: https://www.libsdl.org/download-2.0.php")
    message(STATUS "   - Or use vcpkg: vcpkg install sdl2")
else()
    message(STATUS "   Linux: sudo apt-get install libsdl2-dev")
endif()
message(STATUS "")
message(STATUS "2. Get LVGL:")
message(STATUS "   git submodule add https://github.com/lvgl/lvgl.git third_party/lvgl")
message(STATUS "")
message(STATUS "3. Get LodePNG:")
message(STATUS "   cd third_party && git clone https://github.com/lvgl/lodepng.git")
message(STATUS "")
message(STATUS "4. Build:")
message(STATUS "   mkdir build && cd build")
message(STATUS "   cmake .. && make")
message(STATUS "")