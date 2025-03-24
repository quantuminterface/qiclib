# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Lukas Scheller, IPE, Karlsruhe Institute of Technology
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
This is a [hatchling build hook](https://hatch.pypa.io/1.7/plugins/build-hook/custom/#pyprojecttoml)
to automatically generate python grpc bindings for protobuf files.
"""

from __future__ import annotations

import re
import shutil
from importlib import resources
from io import StringIO
from pathlib import Path

import grpc_tools.protoc
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _get_resource_file_name(package_or_requirement: str, resource_name: str) -> str:
    """Obtain the filename for a resource on the file system."""
    return str((resources.files(package_or_requirement) / resource_name).resolve())


def _patch_generated_grpc_file(path_to_file: Path):
    """
    Patches the generated GRPC file by appending the package name to the generated protobuf file.
    This is suboptimal as the patching might have unwanted side effects, but this seems to be the only viable solution
    See also this discussion (https://github.com/protocolbuffers/protobuf/issues/1491) on GitHub for a better understanding.
    """
    patched = StringIO()
    with open(path_to_file, encoding="utf-8") as infile:
        for line in infile:
            if match := re.search(r"^import ([\w_]+)_pb2 as ([\w_]+)$", line):
                module_name = match.group(1)
                imported_module_name = match.group(2)
                patched.write(
                    f"import qiclib.packages.grpc.{module_name}_pb2 as {imported_module_name}\n"
                )
            # for example: when calling `from datatypes_pb2 import *` (i.e., in pulse_player_pb2.py)
            elif match := re.search(r"from ([\w_]+)_pb2 import (.*)", line):
                module_name = match.group(1)
                # avoid override for "from google.protobuf.x import y"
                # This is hacky as there might be other modules we want to avoid overriding.
                if module_name.startswith("google"):
                    patched.write(line)
                else:
                    imported_stuff = match.group(2)
                    patched.write(
                        f"from qiclib.packages.grpc.{module_name}_pb2 import {imported_stuff}\n"
                    )
            else:
                patched.write(line)
    with open(path_to_file, "w", encoding="utf-8") as outfile:
        patched.seek(0)
        shutil.copyfileobj(patched, outfile)


def _collect_proto_files(path: Path) -> list[str]:
    with open(path / "proto_files.txt", encoding="utf-8") as infile:
        return [line.strip() for line in infile if not line.lstrip().startswith("#")]


class BuildProtos(BuildHookInterface):
    """
    Automatically builds proto files from the `ipe_servicehub_protos` repository
    that is present as submodule herein.
    """

    description = "build selected protos from ipe_servicehub_protos"

    def initialize(self, _version, _build_data):
        build_root = Path(self.root)
        root_dir = build_root / self.config["protos_root"]
        ipe_servicehub_protos = root_dir / "ipe_servicehub_protos"
        out_dir = root_dir
        well_known_protos_include = _get_resource_file_name("grpc_tools", "_proto")
        proto_files = _collect_proto_files(root_dir)
        for file in proto_files:
            proto_file = ipe_servicehub_protos / file
            if not proto_file.exists():
                raise FileNotFoundError(f"Required file {proto_file} not found")
            command = [
                "grpc_tools.protoc",
                f"--proto_path={well_known_protos_include}",
                f"--proto_path={ipe_servicehub_protos}",
                f"--python_out={out_dir}",
                f"--grpc_python_out={out_dir}",
                f"--pyi_out={out_dir}",
                str(proto_file),
            ]
            if ret_code := grpc_tools.protoc.main(command) != 0:
                raise Exception(
                    f"Command returned with non-zero exit code 0 ({ret_code})"
                )
            stem = proto_file.stem
            _patch_generated_grpc_file(out_dir / (stem + "_pb2.py"))
            _patch_generated_grpc_file(out_dir / (stem + "_pb2_grpc.py"))
            _patch_generated_grpc_file(out_dir / (stem + "_pb2.pyi"))
