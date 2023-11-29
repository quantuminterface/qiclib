# Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Richard Gebauer, IPE, Karlsruhe Institute of Technology
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
"""Generated interface files to communicate with the QiController via gRPC

This module contains the generated interface files for the gRPC remote
procedure calls. As they are completely encapsulated by the component classes
in `qiclib.hardware`, please look there for usage guidance.

The protobuf specification files used to generate the interface are located
within the git submodule beneath `./ipe_servicehub_protos`.

Regeneration requires the `grpcio-tools` to be installed from pip. Then, the
script `./grpc_generate.sh` can be called with specifying the location of the
protobuf specification files.
"""
