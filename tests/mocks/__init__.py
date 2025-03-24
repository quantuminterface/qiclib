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
The mocks package provides means to easily mock hardware components resp. the grpc service stubs of these components.
The intended usage is with the `patch()` function from `unittest`, for example:

```
from unittest import patch
from mocks import pimc


@patch("qiclib.packages.grpc.pimc_pb2_grpc.PIMCServiceStub", new=pimc.MockPIMCService)
def test_something_that_uses_the_pimc_module(): ...  # In this function, all calls to the PIMC service are replaced by the mock pimc service
```

For easier development, all mocked modules contain a `patch` function to replace their 'real' counterpart, i.e.

```
from mocks import pimc


@pimc.patch()
def test_something_that_uses_the_pimc_module(): ...  # Same as above
```

The `patch` function from the mocks module can be mock multiple modules, i.e. this
```
@pimc.patch()
@pulse_gen.patch()
@recording.patch()
...
def test_something():
    ... # Test something that uses many hardware component, for example a `QiJob`
```

is equivalent to the following:
```
@mocks.patch(pimc, pulse_gen, recording, ...)
def test_something(): ...  # Test something that uses many hardware component, for example a `QiJob`
```
"""

from mocks import (
    digital_trigger,
    pimc,
    pulse_gen,
    recording,
    rfdc,
    sequencer,
    servicehub_control,
    taskrunner,
    unit_cell,
)
from mocks.unit_cell import MockUnitCellServiceStub

__all__ = [
    "MockUnitCellServiceStub",
    "digital_trigger",
    "pimc",
    "pulse_gen",
    "recording",
    "rfdc",
    "sequencer",
    "servicehub_control",
    "taskrunner",
    "unit_cell",
]


def patch(*modules):
    """
    Patch all the modules. A module is an element with a `patch()` function.
    Usage:
    ```
    from mocks import *
    import mocks


    @mocks.patch(pimc, pulse_gen)
    def test_something(): ...  # test code
    ```
    """

    def wrapper(f):
        for dec in modules:
            f = dec.patch()(f)
        return f

    return wrapper
