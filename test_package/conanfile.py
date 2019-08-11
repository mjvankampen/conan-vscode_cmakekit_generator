import os

from conans import ConanFile, CMake, tools
from conans.util.env_reader import get_env


class HelloTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "vscode_cmakekit"

    def test(self):
        with open("cmake-kits.json", 'r') as fin:
            print(fin.read())
