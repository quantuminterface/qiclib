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

files="pimc.proto pulsegen.proto recording.proto servicehubcontrol.proto sequencer.proto taskrunner.proto qic_storage.proto qic_unitcell.proto rfdc.proto"
folder="ipe_servicehub_protos"

set -e

for f in $files
do
    if [ -e $folder/"$f" ]
    then
        python3 -m grpc_tools.protoc -I"$folder" --python_out=. --grpc_python_out=. "$folder/$f"
        echo "+ Generated code from $f"
    else
        echo "! Could not find $folder/$f"
    fi
done

2to3 ./ -w -n
python3 -m black --exclude "$folder" ./
