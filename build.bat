@echo off
rem Build script for LVGL UI Test Prototype (Windows)

echo LVGL UI Test Prototype - Build Script (Windows)
echo ================================================

rem Check for CMake
cmake --version >nul 2>&1
if errorlevel 1 (
    echo Error: CMake not found. Please install CMake.
    exit /b 1
)

rem Check for Git
git --version >nul 2>&1
if errorlevel 1 (
    echo Error: Git not found. Please install Git.
    exit /b 1
)

echo Dependencies check passed

rem Setup LVGL submodule
echo Setting up LVGL...
if not exist "third_party\lvgl\.git" (
    echo Cloning LVGL...
    git submodule add https://github.com/lvgl/lvgl.git third_party/lvgl 2>nul
    git submodule update --init --recursive third_party/lvgl
) else (
    echo LVGL already cloned
)

rem Setup LodePNG
echo Setting up LodePNG...
if not exist "third_party\lodepng" (
    echo Cloning LodePNG...
    cd third_party
    git clone https://github.com/lvgl/lodepng.git
    cd ..
) else (
    echo LodePNG already cloned
)

rem Create build directory
echo Creating build directory...
if not exist "build" mkdir build
cd build

rem Configure CMake
echo Configuring CMake for Visual Studio...
cmake .. -G "Visual Studio 16 2019" -A x64
if errorlevel 1 (
    echo CMake configuration failed. Trying with default generator...
    cmake ..
    if errorlevel 1 (
        echo CMake configuration failed completely
        cd ..
        exit /b 1
    )
)

rem Build
echo Building...
cmake --build . --config Release
if errorlevel 1 (
    echo Build failed!
    cd ..
    exit /b 1
)

rem Check for executable
if exist "Release\lvgl-ui-test-proto.exe" (
    echo Build completed successfully!
    echo Executable: build\Release\lvgl-ui-test-proto.exe
    echo.
    echo To run the simulator:
    echo   cd build\Release ^&^& lvgl-ui-test-proto.exe
    echo.
    echo To run tests:
    echo   cd python-client
    echo   pip install -r requirements.txt
    echo   python -m pytest tests/ -v
) else if exist "lvgl-ui-test-proto.exe" (
    echo Build completed successfully!
    echo Executable: build\lvgl-ui-test-proto.exe
    echo.
    echo To run the simulator:
    echo   cd build ^&^& lvgl-ui-test-proto.exe
) else (
    echo Warning: Could not find executable
)

cd ..
echo Build script completed