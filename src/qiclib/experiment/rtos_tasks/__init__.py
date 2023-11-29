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
"""Methods to interact with tasks for the Taskrunner."""


def get_task_source(filename):
    # type: (str) -> str
    """Returns the absolute path to a task source file.

    :param filename: The filename of the task to load (with ending, e.g. "interleaved.c")

    :return: absolute path to the file.
    """
    import os

    base_path = os.path.dirname(os.path.realpath(__file__))
    task_file = os.path.join(base_path, filename)

    if not os.path.isfile(task_file):
        raise FileNotFoundError(
            f"Task source file {filename} could not be found in the task repository. Searched path {task_file}"
        )

    return task_file
