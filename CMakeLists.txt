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
    # For Windows, try multiple approaches to find SDL2
    set(SDL2_LOCAL_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/sdl2/SDL2-devel-2.30.8-VC/SDL2-2.30.8)
    
    # Method 1: Try local third_party directory first (for development)
    if(EXISTS ${SDL2_LOCAL_DIR})
        message(STATUS "Trying local SDL2 at: ${SDL2_LOCAL_DIR}")
        find_path(SDL2_INCLUDE_DIR SDL.h 
            HINTS ${SDL2_LOCAL_DIR}
            PATH_SUFFIXES include
            NO_DEFAULT_PATH
        )
        
        if(CMAKE_SIZEOF_VOID_P EQUAL 8)
            set(SDL2_LIB_SUFFIX "x64")
        else()
            set(SDL2_LIB_SUFFIX "x86")
        endif()
        
        if(SDL2_INCLUDE_DIR)
            find_library(SDL2_LIBRARY 
                NAMES SDL2 
                HINTS ${SDL2_LOCAL_DIR}
                PATH_SUFFIXES lib/${SDL2_LIB_SUFFIX} lib
                NO_DEFAULT_PATH
            )
            
            find_library(SDL2MAIN_LIBRARY 
                NAMES SDL2main 
                HINTS ${SDL2_LOCAL_DIR}
                PATH_SUFFIXES lib/${SDL2_LIB_SUFFIX} lib
                NO_DEFAULT_PATH
            )
            
            if(SDL2_LIBRARY AND SDL2MAIN_LIBRARY)
                set(SDL2_LIBRARIES ${SDL2_LIBRARY} ${SDL2MAIN_LIBRARY})
                message(STATUS "Found local SDL2: ${SDL2_INCLUDE_DIR}")
            endif()
        endif()
    endif()
    
    # Method 2: Try vcpkg find_package (for CI)
    if(NOT SDL2_INCLUDE_DIR OR NOT SDL2_LIBRARIES)
        message(STATUS "Local SDL2 not found, trying vcpkg...")
        find_package(SDL2 QUIET)
        if(SDL2_FOUND)
            message(STATUS "Found SDL2 via find_package: ${SDL2_INCLUDE_DIRS}")
            set(SDL2_INCLUDE_DIR ${SDL2_INCLUDE_DIRS})
            set(SDL2_LIBRARIES ${SDL2_LIBRARIES})
        else()
            # Try alternative SDL2 target names that vcpkg might use
            find_package(SDL2 QUIET CONFIG)
            if(TARGET SDL2::SDL2 AND TARGET SDL2::SDL2main)
                message(STATUS "Found SDL2 via CONFIG mode with targets")
                get_target_property(SDL2_INCLUDE_DIR SDL2::SDL2 INTERFACE_INCLUDE_DIRECTORIES)
                set(SDL2_LIBRARIES SDL2::SDL2 SDL2::SDL2main)
            elseif(TARGET SDL2::SDL2-static AND TARGET SDL2::SDL2main)
                message(STATUS "Found SDL2 static via CONFIG mode with targets")
                get_target_property(SDL2_INCLUDE_DIR SDL2::SDL2-static INTERFACE_INCLUDE_DIRECTORIES)
                set(SDL2_LIBRARIES SDL2::SDL2-static SDL2::SDL2main)
            endif()
        endif()
    endif()
    
    # Method 3: Try manual vcpkg paths (fallback)
    if(NOT SDL2_INCLUDE_DIR OR NOT SDL2_LIBRARIES)
        message(STATUS "find_package failed, trying manual vcpkg detection...")
        find_path(SDL2_INCLUDE_DIR SDL.h 
            PATHS 
                $ENV{VCPKG_ROOT}/installed/x64-windows/include
                C:/vcpkg/installed/x64-windows/include
                ${CMAKE_PREFIX_PATH}/include
            NO_DEFAULT_PATH
        )
        
        if(SDL2_INCLUDE_DIR)
            find_library(SDL2_LIBRARY 
                NAMES SDL2 
                PATHS 
                    $ENV{VCPKG_ROOT}/installed/x64-windows/lib
                    C:/vcpkg/installed/x64-windows/lib
                    ${CMAKE_PREFIX_PATH}/lib
                NO_DEFAULT_PATH
            )
            
            find_library(SDL2MAIN_LIBRARY 
                NAMES SDL2main 
                PATHS 
                    $ENV{VCPKG_ROOT}/installed/x64-windows/lib
                    C:/vcpkg/installed/x64-windows/lib
                    ${CMAKE_PREFIX_PATH}/lib
                NO_DEFAULT_PATH
            )
            
            if(SDL2_LIBRARY AND SDL2MAIN_LIBRARY)
                set(SDL2_LIBRARIES ${SDL2_LIBRARY} ${SDL2MAIN_LIBRARY})
                message(STATUS "Found SDL2 via manual vcpkg detection: ${SDL2_INCLUDE_DIR}")
            endif()
        endif()
    endif()
    
    # Final check and error reporting
    # Check if we have SDL2 targets or traditional variables
    set(SDL2_FOUND FALSE)
    if(TARGET SDL2::SDL2 OR TARGET SDL2::SDL2-static)
        set(SDL2_FOUND TRUE)
        message(STATUS "SDL2 configuration successful (using targets):")
        if(TARGET SDL2::SDL2)
            message(STATUS "  Target: SDL2::SDL2")
        endif()
        if(TARGET SDL2::SDL2-static)
            message(STATUS "  Target: SDL2::SDL2-static")
        endif()
        if(TARGET SDL2::SDL2main)
            message(STATUS "  Target: SDL2::SDL2main")
        endif()
    elseif(SDL2_INCLUDE_DIR AND SDL2_LIBRARIES)
        set(SDL2_FOUND TRUE)
        message(STATUS "SDL2 configuration successful (using variables):")
        message(STATUS "  Include: ${SDL2_INCLUDE_DIR}")
        message(STATUS "  Libraries: ${SDL2_LIBRARIES}")
    endif()
    
    if(NOT SDL2_FOUND)
        message(FATAL_ERROR "SDL2 not found! Please install SDL2:
        - For local development: Place SDL2 in third_party/sdl2/
        - For CI: Use 'vcpkg install sdl2:x64-windows'
        - Manual install: Download from https://www.libsdl.org/download-2.0.php
        
        Searched locations:
        - Local: ${SDL2_LOCAL_DIR}
        - vcpkg: $ENV{VCPKG_ROOT}/installed/x64-windows/
        - System: ${CMAKE_PREFIX_PATH}")
    endif()
else()
    # Linux: Use pkg-config to find SDL2
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(SDL2 REQUIRED sdl2)
    
    # Convert pkg-config variables to match our Windows variable names
    set(SDL2_INCLUDE_DIR ${SDL2_INCLUDE_DIRS})
    set(SDL2_LIBRARIES ${SDL2_LIBRARIES})
    
    message(STATUS "Linux SDL2 found via pkg-config:")
    message(STATUS "  SDL2_INCLUDE_DIRS: ${SDL2_INCLUDE_DIRS}")
    message(STATUS "  SDL2_LIBRARIES: ${SDL2_LIBRARIES}")
    message(STATUS "  SDL2_CFLAGS: ${SDL2_CFLAGS}")
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
    if(TARGET SDL2::SDL2)
        message(STATUS "Linking SDL2 target to LVGL")
        target_link_libraries(lvgl PUBLIC SDL2::SDL2)
    elseif(TARGET SDL2::SDL2-static)
        message(STATUS "Linking SDL2 static target to LVGL")
        target_link_libraries(lvgl PUBLIC SDL2::SDL2-static)
    elseif(SDL2_INCLUDE_DIR)
        message(STATUS "Adding SDL2 include directory to LVGL: ${SDL2_INCLUDE_DIR}")
        target_include_directories(lvgl PUBLIC ${SDL2_INCLUDE_DIR})
    elseif(SDL2_INCLUDE_DIRS)
        message(STATUS "Adding SDL2 include directories to LVGL: ${SDL2_INCLUDE_DIRS}")
        target_include_directories(lvgl PUBLIC ${SDL2_INCLUDE_DIRS})
    else()
        message(WARNING "No SDL2 include directories found for LVGL!")
    endif()
    
    # On Linux, also add compile flags from pkg-config
    if(NOT WIN32 AND SDL2_CFLAGS)
        target_compile_options(lvgl PUBLIC ${SDL2_CFLAGS})
    endif()
    
    
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

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)

# Add SDL2 include directory only if found (for traditional variables, targets handle this automatically)
if(SDL2_INCLUDE_DIR AND NOT TARGET SDL2::SDL2 AND NOT TARGET SDL2::SDL2-static)
    include_directories(${SDL2_INCLUDE_DIR})
endif()

# Source files
set(SOURCES
    src/main.c
    src/ui_watch.c
    src/test_harness.c
    src/tcp_server.c
    src/screenshot.c
)

# LodePNG not needed - LVGL v9 has built-in PNG support via stb_image_write

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Link libraries
if(EXISTS ${LVGL_DIR})
    # Enable LVGL for visual emulator
    target_compile_definitions(${PROJECT_NAME} PRIVATE HAVE_LVGL=1)
    
    # Link SDL2 - use targets if available, otherwise variables
    if(TARGET SDL2::SDL2 AND TARGET SDL2::SDL2main)
        target_link_libraries(${PROJECT_NAME} 
            lvgl
            SDL2::SDL2
            SDL2::SDL2main
            ${PTHREAD_LIBRARIES}
        )
    elseif(TARGET SDL2::SDL2-static AND TARGET SDL2::SDL2main)
        target_link_libraries(${PROJECT_NAME} 
            lvgl
            SDL2::SDL2-static
            SDL2::SDL2main
            ${PTHREAD_LIBRARIES}
        )
    else()
        target_link_libraries(${PROJECT_NAME} 
            lvgl
            ${SDL2_LIBRARIES}
            ${PTHREAD_LIBRARIES}
        )
    endif()
else()
    # Fallback without LVGL for initial setup
    if(TARGET SDL2::SDL2 AND TARGET SDL2::SDL2main)
        target_link_libraries(${PROJECT_NAME} 
            SDL2::SDL2
            SDL2::SDL2main
            ${PTHREAD_LIBRARIES}
        )
    elseif(TARGET SDL2::SDL2-static AND TARGET SDL2::SDL2main)
        target_link_libraries(${PROJECT_NAME} 
            SDL2::SDL2-static
            SDL2::SDL2main
            ${PTHREAD_LIBRARIES}
        )
    else()
        target_link_libraries(${PROJECT_NAME} 
            ${SDL2_LIBRARIES}
            ${PTHREAD_LIBRARIES}
        )
    endif()
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

# Dependencies are managed via Git submodules - no manual download needed

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
message(STATUS "3. Build:")
message(STATUS "   mkdir build && cd build")
message(STATUS "   cmake .. && make")
message(STATUS "")