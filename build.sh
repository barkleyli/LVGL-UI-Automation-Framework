#!/bin/bash
# Build script for LVGL UI Test Prototype

set -e

echo "LVGL UI Test Prototype - Build Script"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're on Windows (WSL/Git Bash) or Linux
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
else
    echo -e "${YELLOW}Warning: Unknown platform '$OSTYPE', assuming Linux${NC}"
    PLATFORM="linux"
fi

echo "Platform: $PLATFORM"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "Checking dependencies..."

if ! command_exists cmake; then
    echo -e "${RED}Error: CMake not found. Please install CMake.${NC}"
    exit 1
fi

if ! command_exists git; then
    echo -e "${RED}Error: Git not found. Please install Git.${NC}"
    exit 1
fi

if [[ "$PLATFORM" == "linux" ]]; then
    # Check for SDL2 on Linux
    if ! pkg-config --exists sdl2; then
        echo -e "${RED}Error: SDL2 development libraries not found.${NC}"
        echo "Please install: sudo apt-get install libsdl2-dev"
        exit 1
    fi
fi

echo -e "${GREEN}Dependencies check passed${NC}"

# Initialize git submodules if not already done
echo "Setting up dependencies..."

if [ ! -d "third_party/lvgl/.git" ]; then
    echo "Cloning LVGL..."
    if [ -d "third_party/lvgl" ]; then
        rm -rf third_party/lvgl
    fi
    git submodule add https://github.com/lvgl/lvgl.git third_party/lvgl 2>/dev/null || true
    git submodule update --init --recursive third_party/lvgl
else
    echo "LVGL already cloned"
fi

if [ ! -d "third_party/lodepng" ]; then
    echo "Cloning LodePNG..."
    cd third_party
    git clone https://github.com/lvgl/lodepng.git
    cd ..
else
    echo "LodePNG already cloned"
fi

# Create build directory
echo "Creating build directory..."
mkdir -p build
cd build

# Configure CMake
echo "Configuring CMake..."
if [[ "$PLATFORM" == "windows" ]]; then
    # Windows build configuration
    if command_exists cl; then
        # Visual Studio compiler available
        cmake .. -G "Visual Studio 16 2019" -A x64
        BUILD_CMD="cmake --build . --config Release"
    else
        # MinGW/MSYS2 fallback
        cmake .. -G "MinGW Makefiles"
        BUILD_CMD="make -j$(nproc 2>/dev/null || echo 4)"
    fi
else
    # Linux build configuration
    cmake .. -DCMAKE_BUILD_TYPE=Release
    BUILD_CMD="make -j$(nproc)"
fi

# Build
echo "Building..."
eval $BUILD_CMD

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build completed successfully!${NC}"
    
    # Find the executable
    if [[ "$PLATFORM" == "windows" ]]; then
        if [ -f "Release/lvgl-ui-test-proto.exe" ]; then
            EXECUTABLE="Release/lvgl-ui-test-proto.exe"
        elif [ -f "lvgl-ui-test-proto.exe" ]; then
            EXECUTABLE="lvgl-ui-test-proto.exe"
        fi
    else
        EXECUTABLE="lvgl-ui-test-proto"
    fi
    
    if [ -f "$EXECUTABLE" ]; then
        echo -e "${GREEN}Executable: build/$EXECUTABLE${NC}"
        echo ""
        echo "To run the simulator:"
        echo "  cd build && ./$EXECUTABLE"
        echo ""
        echo "To run tests:"
        echo "  cd python-client"
        echo "  pip install -r requirements.txt"
        echo "  python -m pytest tests/ -v"
    else
        echo -e "${YELLOW}Warning: Could not find executable${NC}"
    fi
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

cd ..
echo -e "${GREEN}Build script completed${NC}"