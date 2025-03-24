# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
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
"""qiclib is Quantum Interface's official Python client for the QiController.

This documentation aims to provide an overview over the provided functionality
of the QiController and its usage with the :python:`qiclib` Python package. As the
system is under active development, it might happen that some documentation is
not complete or lacking additional information. In this case, please feel free
to contact the developers or open an issue in the repository.

:python:`qiclib` is organized in several submodules providing different functionality.
For convenience. the following two objects are also directly accessible by
importing :python:`qiclib`:

* :class:`~qiclib.hardware.controller.QiController`:
    The heart of the client providing access to the QiController and all its configuration and
    control interface.
* :class:`~qiclib.experiment.collection`:
    A collection of descriptions for most common qubit experiments.
"""

from qiclib._version import __version__, __version_tuple__
from qiclib.experiment import collection as exp
from qiclib.experiment.qicode import collection as jobs
from qiclib.experiment.qicode import init_readout as init
from qiclib.hardware.controller import QiController

__all__ = ["QiController", "__version__", "__version_tuple__", "exp", "init", "jobs"]
