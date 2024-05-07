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
"""This module contains the drivers to control and interface with the QiController.

The QiController provides a versatile and flexible qubit control platform and is meant
to be used as laboratory equipment specifically designed to meet the demands of the
superconducting qubit research community. It consists of numerous different modules:
Taskrunner, cell coordinator, multiple digital unit cells, each with sequencer, signal
recorder and two signal generators, among others. All modules can be individually
controlled and configured to obtain the desired output and functionality.
In the following the architecture of the QiController is introduced in more detail.

.. todo:: Add architecture image (overview of the QiController architecture)

.. image:: platform.png

Tasks which require nanosecond accuracy are handled within the FPGA. There, the main functionality is provided by
digital unit cells (see `qiclib.hardware.unitcell`). They generate digital microwave pulses which are flexibly routed
(i.e. combined and distributed) to the available DAC channels. Likewise, returning digitized microwave signals from
the ADCs are distributed and split up onto the belonging cells. The cells are synchronized using a special cell
coordinator which also facilitates data exchange between the cells. On the processing system, online data processing
and advanced control is implemented by the Taskrunner on a dedicated real-time processor. A modular communication
server called ServiceHub provides a user interface to interact with the platform via Ethernet. This python driver
encapsulates the remote procedure calls exposed by the ServiceHub (using the gRPC framework).

Experiments running on the QiController are normally all partitioned in a similar way. Pulse generation, detection,
sequencing and result storage, as well as simple parameter variations, happen with nanosecond precision in the
digital unit cells in the FPGA. Their execution is synchronized by the cell coordinator which is triggered by the
Taskrunner. The Taskrunner controls the execution of the FPGA, performs more complex parameter variations between
multiple executions and collects the result data that is generated within the digital unit cells. Also, further data
aggregation, sorting or online evaluation are possible, depending on the requirements of the experiment. This
includes, but is not limited to, averaging of data, collection of individual qubit states or single measurement
values, as well as counting different qubit state outcomes. You can also define your own C program to perform custom
data processing and aggregation (see `qiclib.hardware.taskrunner`). The resulting data is then sent via the
ServiceHub to the user client where you can either persist or further process the data offline. During the
experiment, in principle, no connection between client and QiController is required. However, you can monitor the
progress of the execution and, depending on the experiment, stream some result data already before the execution
finished.

For more details on how to interact with the QiController, see `qiclib.hardware.controller`. Details concerning the
high-level experiment description language QiCode can be found in `qiclib.code`. The functionalities covered by the
digital unit cells within the FPGA are covered in `qiclib.hardware.unitcell`. For more background regarding the
online data processing and aggregation within the Taskrunner, refer to `qiclib.hardware.taskrunner`."""
