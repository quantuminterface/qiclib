# Copyright © 2024 Quantum Interface (quantuminterface@ipe.kit.edu)
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
from unittest import mock


class MockDigitalTriggerService:
    def __init__(self, _):
        pass

    def ClearTriggerSets(self, *args, **kwargs):
        pass


module = "qiclib.packages.grpc.digital_trigger_pb2_grpc.DigitalTriggerServiceStub"


def patch():
    return mock.patch(module, new=MockDigitalTriggerService)
