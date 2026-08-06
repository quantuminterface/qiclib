from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy
import os


class QicodeConan(ConanFile):
    name = "qicode"
    version = "0.0.1"
    description = "C++ Protocol Buffer bindings for QiCode language"
    author = "Quantum Interface <quantuminterface@ipe.kit.edu>"
    license = "GPL-3.0-or-later"
    homepage = "https://github.com/quantuminterface/qiclib"
    url = "https://github.com/quantuminterface/qiclib"

    # Settings
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        # Copy the proto folder relative to the sources folder.
        # This change requires the `PROTO_BASE_DIR` variable to be set (see the generate method)
        copy(self, "proto/*", os.path.join(self.recipe_folder, ".."), os.path.join(self.export_sources_folder, "qicode"))

    def requirements(self):
        self.requires("abseil/20250814.0")
        self.requires("protobuf/6.30.1", transitive_headers=True)

    def build_requirements(self):
        # protoc must come from the build context, otherwise CMake picks up
        # whatever protoc is on PATH
        self.tool_requires("protobuf/<host_version>")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.variables["PROTO_BASE_DIR"] = self.source_folder
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["qicode"]
