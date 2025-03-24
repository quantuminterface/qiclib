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

# pylint: disable=wrong-import-order, import-error, wrong-import-position
import threading
import time

import numpy as np

from qiclib.packages.qkit_polyfill import QKIT_ENABLED

from .qubit_times import QubitTimes

if not QKIT_ENABLED:
    raise ImportError("Qkit is required to use the QubitTimesQkit experiment...")

import qkit.measure.write_additional_files as waf
from qkit.analysis import qfit
from qkit.gui.plot import plot as qviewkit
from qkit.storage import store


class QubitTimesQkit(QubitTimes):
    """Interleaved execution of T1, Ramsey and SpinEcho experiments with Qkit integration.

    .. deprecated::
        QubitTimes is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.qubit_times`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param delays_t1:
        List of delays for the T1 experiment.
    :param delays_ramsey:
        List of delays for the Ramsey experiment.
    :param delays_spinecho:
        List of delays for the SpinEcho experiment. The delays are the sum of both delays.
    :param order:
        List specifying the order of the experiments within a single repetition.
        0 - T1, 1 - Ramsey, 2 - SpinEcho
    :param ramsey_detuning:
        The detuning (in Hz) for the Ramsey experiment.
    :param spinecho_phase:
        The relative phase of the correcting pi pulse between the pi/2 pulses. Defaults to pi/2 (Y instead of X rotation).
    """

    def __init__(
        self,
        controller,
        delays_t1,
        delays_ramsey,
        delays_echo,
        order=[0, 1, 2],
        ramsey_detuning=0,
        spinecho_phase=np.pi / 2,
        iterations=1,
    ):
        super().__init__(
            controller,
            delays_t1,
            delays_ramsey,
            delays_echo,
            order,
            ramsey_detuning,
            spinecho_phase,
        )

        # Faster if we process data while next iteration is running
        self.raw_results = True

        self._names = ["t1", "ramsey", "echo"]
        self._delays = {
            "t1": self.delays_t1,
            "ramsey": self.delays_ramsey,
            "echo": self.delays_echo,
        }

        self.iterations = iterations
        self.dirname = "qubit-times-iterations"
        self.comment = None
        self.open_qviewkit = True
        self.remove_failed_fits = True

        self._data_to_fit = None
        self._h5d = None
        self._logfile = None

        self._iteration_coord = None
        self._coordinates = {}
        self._amp_matrices = {}
        self._pha_matrices = {}
        self._fit_vectors = {}
        self._std_vectors = {}
        self._times_vector = {}

        self._qf = qfit.QFIT()
        self._qf.cfg["show_plot"] = False
        self._qf.cfg["save_png"] = False
        self._qf.cfg["show_output"] = False
        self._qf.cfg["show_complex_plot"] = False

    def record(self):
        # Make sure we get the raw data
        self.raw_results = True

        self._prepare_measurement_file()

        if self.open_qviewkit:
            qviewkit.plot(self._h5d.get_filepath(), live=True)

        self._create_progress(self.iterations, name="Iteration")
        start_time = time.time()
        for _ in range(self.iterations):
            current_time = np.round(time.time() - start_time, 3)
            data = super().record()
            self._data_to_fit = {"time": current_time, "data": data}
            self._iterate_progress(name="Iteration")
        # We need to process the remaining data after the last iteration
        self._callback_after_task_start()

        self._close_measurement_file()

    def _create_measurement_file(self):
        self._h5d = store.Data(name=self.dirname, mode="a")
        self._h5d.add_textlist("settings").append(
            waf.get_instrument_settings(self._h5d.get_filepath())
        )
        self._logfile = waf.open_log_file(self._h5d.get_filepath())
        if self.comment:
            self._h5d.add_comment(self.comment)

    def _close_measurement_file(self):
        self._h5d.close_file()
        threading.Thread(
            target=qviewkit.save_plots, args=[self._h5d.get_filepath(), ""]
        ).start()
        waf.close_log_file(self._logfile)

    def _prepare_measurement_file(self):
        self._create_measurement_file()

        # Prepare measurement file
        self._iteration_coord = self._h5d.add_coordinate(
            "iteration", unit="", comment="Iteration of the whole experiment"
        )
        self._iteration_coord.add(np.arange(self.iterations, dtype=int) + 1)
        self._coordinates = {}
        self._amp_matrices = {}
        self._pha_matrices = {}
        self._fit_vectors = {}
        self._std_vectors = {}
        for name in self._names:
            self._coordinates[name] = self._h5d.add_coordinate(
                f"delay_{name}",
                unit="s",
                comment=f"Delay values of the {name} experiment",
            )
            self._coordinates[name].add(self._delays[name])
            self._amp_matrices[name] = self._h5d.add_value_matrix(
                f"amplitude_{name}",
                y=self._coordinates[name],
                x=self._iteration_coord,
                unit="arb. unit",
                comment=f"Amplitude result of the {name} experiment",
            )
            self._pha_matrices[name] = self._h5d.add_value_matrix(
                f"phase_{name}",
                y=self._coordinates[name],
                x=self._iteration_coord,
                unit="rad",
                comment=f"Phase result of the {name} experiment",
            )
            self._fit_vectors[name] = self._h5d.add_value_vector(
                f"time_{name}",
                x=self._iteration_coord,
                unit="s",
                comment=f"Fitted decay time of the {name} experiment",
            )
            self._std_vectors[name] = self._h5d.add_value_vector(
                f"stdev_{name}",
                x=self._iteration_coord,
                unit="s",
                comment=f"Standard deviation of fitted decay time of the {name} experiment",
            )
        self._fit_vectors["detuning"] = self._h5d.add_value_vector(
            "detuning",
            x=self._iteration_coord,
            unit="Hz",
            comment="Fitted detuning of the ramsey experiment",
        )
        self._std_vectors["detuning"] = self._h5d.add_value_vector(
            "stdev_detuning",
            x=self._iteration_coord,
            unit="Hz",
            comment="Standard deviation of fitted detuning of the ramsey experiment",
        )
        self._times_vector = self._h5d.add_value_vector(
            "time",
            x=self._iteration_coord,
            unit="s",
            comment="Time since the beginning of the measurement",
        )

    def _callback_after_task_start(self):
        if self._data_to_fit is None:
            return

        self._fit_data_and_add_to_qkit(self._data_to_fit)

    def _fit_data_and_add_to_qkit(self, data_dict):
        self._times_vector.append(data_dict["time"])
        data = self.format_data(data_dict["data"])

        fit_result = self._fit_formatted_data(self._delays, data)
        for fitname, result in fit_result.items():
            self._std_vectors[fitname].append(result[1])
            if self.remove_failed_fits and result[1] == float("inf"):
                self._fit_vectors[fitname].append(float("inf"))
            else:
                self._fit_vectors[fitname].append(result[0])

        for name, (amp, pha) in data.items():
            self._amp_matrices[name].append(np.atleast_1d(amp))
            self._pha_matrices[name].append(np.atleast_1d(pha))

    def _fit_formatted_data(self, delays, data):
        fit_times = {}
        for name, (_, phase) in data.items():
            self._qf.load(coordinate=delays[name], data=phase)

            if name == "ramsey":
                self._qf.fit_damped_sine()
                fit_times["ramsey"] = (self._qf.popt[1], self._qf.std[1])  # Td
                fit_times["detuning"] = (self._qf.popt[0], self._qf.std[0])  # fs
            else:
                self._qf.fit_exp()
                fit_times[name] = (self._qf.popt[0], self._qf.std[0])
        return fit_times
