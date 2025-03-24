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
"""This file contains the IQCloud experiment description for the QiController."""

import warnings

from qiclib.experiment.base import BaseExperiment


class IQClouds(BaseExperiment):
    """Experiment performing many single-shot readouts and returning
    IQ fourier coefficients.

    .. deprecated::
        IQClouds is deprecated. Please use the new QiCode syntax instead, i.e. use
        `qiclib.jobs.SimpleReadout().run(..., data_collection="iqcloud")`.

    :param controller:
        The QiController driver
    :param state:
        The state in which the qubit should be initialized
        (the default is 0)
    :param count:
        The number of IQ points received
        (the default is 100k)
    :param averaging: {bool}, optional
        If averaging on the card should be allowed (no real single-shot then)
        (the default is False)
    """

    def __init__(self, controller, state=0, count=100000, averaging=False):
        super().__init__(controller)
        self.count = int(count)
        self.state = state
        self.averaging = averaging

        warnings.warn(
            "IQClouds is deprecated. Please use the new QiCode syntax instead, i.e. use"
            ' `qiclib.jobs.SimpleReadout().run(..., data_collection="iqcloud")`',
            FutureWarning,
        )
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                "state0": lambda code: code,
                "state1": lambda code: code.trigger_immediate(
                    self._p["Rx pi"]["length"], manipulation=self._p["Rx pi"]["trigger"]
                ),
            }
        )

        # Select the start program counter
        start_pc = self._pc_dict.get(f"state{self.state}")
        if start_pc is None:
            raise ValueError("State attribute is invalid! Only 0 or 1 is allowed.")
        # Create alias with name "exp" for the experiment sequence to use.
        self._pc_dict["exp"] = start_pc

    def _configure_taskrunner(self):
        self.qic.taskrunner.load_task_source("iq_clouds.c", "IQClouds")
        self.qic.taskrunner.set_param_list([self.count, self._pc_dict["exp"]])

    def _record_internal(self):
        old_averages = self.qic.sequencer.averages
        try:
            if not self.averaging:
                # Ensure no averaging
                self.qic.sequencer.averages = 1

            data = self._record_internal_taskrunner(
                self.count, "IQ Points", allow_partial_data=True
            )[0]
        finally:
            if not self.averaging:
                # Restore old value
                self.qic.sequencer.averages = old_averages

        return (data[::2], data[1::2])
