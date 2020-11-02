import os
from conans.client.generators.cmake import DepsCppCmake
from conans.model import Generator
from conans.client.build.cmake_flags import CMakeDefinitionsBuilder, get_generator
from conans import ConanFile
from conans.util.env_reader import get_env
from conans.model.conan_file import get_env_context_manager
from conans.util.files import save
from conans.errors import ConanInvalidConfiguration


def _cmake_escape_backslash(inp: str):
    """
    Escapes backslashes for cmake. Basically it replaces any \\ with \\\\
    :param inp: Input string
    :return: Input string with backslashes escaped for cmake
    """
    return inp.replace("\\", "/")


class vscode_cmakekit(Generator):
    """
    conan generator for cmake toolchains. Generates a file conaining all definitions and environment variables
    that would usually be set by conan when invoking cmake. Additionally the functionality of the built in
    cmake_paths generator is kept.
    """

    def _get_cmake_environment_setters(self):
        """
        Detect all environment changes made by conan and convert them to cmake commands
        :return: List of lines to print into a cmake file
        """
        old_env = dict(os.environ)

        with get_env_context_manager(self.conanfile):
            ret = ["\t\t\"environmentVariables\": {"]

            for name, value in self.conanfile.env.items():
                if isinstance(value, list):
                    if name in old_env:
                        value = str(get_env(name)).replace(
                            old_env[name], "${{env:{name}}}").format(name=name)
                    else:
                        value = str(value)
                value = _cmake_escape_backslash(value)
                ret.append("\t\t\t\"{name}\": \"{value}\"".format(
                    name=name, value=value))
            ret[1:-1] = [line + "," for line in ret[1:-1]]
            return ret

    def _get_cmake_definitions(self):
        """
        Detect all definitions conan sends to cmake by command line and convert them to cmake commands. Removes the
        CONAN_EXPORTED definition, so that users may check if conan has been invoked or not.
        :return: List of lines to print into a cmake file
        """
        with get_env_context_manager(self.conanfile):
            ret = ["\t\t\"cmakeSettings\": {"]
            generator = get_generator(self.conanfile.settings)
            self.conanfile.install_folder = ""
            def_builder = CMakeDefinitionsBuilder(
                self.conanfile, generator=generator)
            definitions = def_builder.get_definitions(None)

            for name, value in definitions.items():
                ret.append("\t\t\t\"{name}\": \"{value}\",".format(
                    name=name, value=value))

            deps = []

            for _, dep_cpp_info in self.deps_build_info.dependencies:
                deps.append("\t\t\t\t\t" + DepsCppCmake(dep_cpp_info).rootpath)
            deps[:-1] = [line + "," for line in deps[:-1]]
            ret.append("\t\t\t\"CMAKE_PREFIX_PATH\": [")
            ret.extend(deps)
            ret.append("\t\t\t],")
            ret.append("\t\t\t\"CMAKE_MODULE_PATH\": [")
            ret.extend(deps)
            ret.append("\t\t\t]")
            return ret

    @property
    def filename(self):
        """ Name of the output file """
        return "cmake-kits.json"

    @property
    def content(self):
        """ Content of the output file. """
        # environment and definitions will only be set if cmake has not been invoked by conan
        lines = ["["]
        lines.append("\t{")
        lines.append("\t\t\"name\": \"conan-generated\",")
        lines.extend(self._get_cmake_environment_setters())
        lines.append("\t\t},")
        lines.extend(self._get_cmake_definitions())
        lines.append("\t\t}")
        lines.append("\t}")
        lines.append("]")
        result = os.linesep.join(lines) + "\n"
        savepath = os.path.join(
            os.environ['vscode_output_folder'], self.filename)
        save(savepath, result)
        self.conanfile.output.info(
            "Generator vscode_cmakekit saved cmake-kits.json to: %s" % savepath)
        return result


class VSCodeCmakeKitGeneratorPackage(ConanFile):
    name = 'vscode_cmakekit_generator'
    version = '0.4'
    description = "A generator for conan that can be used to build conan packages "
    "by invoking cmake instead of conan build"
    url = 'https://github.com/pepe82sh/ConanCmakeToolchainGenerator'
    license = 'MIT'
    options = {'vscode_folder': 'ANY'}

    def configure(self):
        """ Configure the vscode_folder in an environment variable to be used in the generator step. """
        vscode_folder = self.options.vscode_folder.value
        if vscode_folder is None or os.path.basename(vscode_folder) != ".vscode":
            raise ConanInvalidConfiguration(
                "The given option for vscode_cmakekit_generator:vscode_folder is not an existing .vscode folder. Found value: %s" % vscode_folder)

        # folder is valid, set it to the environment to use it during the save functionality
        os.environ['vscode_output_folder'] = vscode_folder

    def build(self):
        pass

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
