# conan-vscode_cmakekit_generator

This conan generator creates the file `cmake-kits.json`
inside your build folder. This file can be used in Visual Studio Code's
cmake plugin where it will set environment variables as well as `CMAKE_MODULE_PATH` 
and `CMAKE_PREFIX_PATH` like in the `cmake_paths` generator.

## Usage
Copy the cmake-kits.json to your .vscode folder and select the conan-generated kit.