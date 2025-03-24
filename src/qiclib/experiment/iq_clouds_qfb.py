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
"""This file contains the IQCloudsQFB experiment description for the QiController."""

import warnings

from qiclib.experiment.iq_clouds import IQClouds


class IQCloudsQFB(IQClouds):
    """Experiment preparing the qubit state followed by an active reset
    quantum feedback operation and a final measurement.

    .. deprecated::
        IQCloudsQFB is deprecated. Please use the new QiCode syntax instead, i.e. use
        ``qiclib.jobs.ActiveReset(target_state).run(..., data_collection="iqcloud")``.

    :param controller:
        The QiController driver
    :param state:
        The state in which the qubit should be initialized (the default is 0)
    :param count:
        The number of IQ points received (the default is 100k)
    """

    def __init__(self, controller, state=0, count=100000, averaging=False):
        super().__init__(controller, state, count, averaging)
        warnings.warn(
            "IQCloudsQFB is deprecated. Please use the new QiCode syntax instead, i.e. "
            "use the `QiJob` defined in `qiclib.jobs.ActiveReset(target_state)`.",
            FutureWarning,
        )

    def _configure_sequences(self):
        def _sequence(code):
            if self.state == 1:
                # Prepare initial state to |1>
                code.trigger_immediate(self.qic.sample.tpi, manipulation=1)

            # We jump to final readout and skip pi pulse if qubit is in state 0
            code.trigger_active_reset(pi_trigger=1, pi_length=self.qic.sample.tpi)

        self._built_code_from_sequences({"exp": _sequence})
