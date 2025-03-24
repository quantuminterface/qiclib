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
"""Measurement script that integrates IQClouds measurements with the QiController into Qkit."""

import logging
import threading

import numpy as np

# For type recognition
# pylint: disable=unused-import
# pylint: enable=unused-import
from qiclib.packages.qkit_polyfill import QKIT_ENABLED, qkit

if QKIT_ENABLED:
    import qkit.measure.write_additional_files as waf
    from qkit.gui.plot import plot as qkit_viewer
    from qkit.storage import store as hdf


class IQMeasurement:
    """IQClouds measurement class storing IQClouds obtained from the QiController setup."""

    def __init__(self, experiment):
        if not QKIT_ENABLED:
            raise RuntimeError(
                "This measurement class can only be executed when Qkit is installed!"
            )
        self.experiment = experiment  # type: IQClouds
        self.qic = self.experiment.qic
        self.sample = self.qic.sample

        self.comment = None
        self.dirname = "iq-measurement"
        self.data_dir = None
        self.plot_comment = ""

        self.x_coordname = "count"
        self.x_unit = ""
        self.x_vector = None
        self.data_unit = "arb. unit"

        self.open_qviewkit = True
        self.control_mw_src = True

        self._data_file = None  # type: hdf.Data
        self._data_axis = None  # type: hdf.hdf_dataset
        self._data_settings = None  # type: hdf.hdf_dataset
        self._data_i = None  # type: hdf.hdf_dataset
        self._data_q = None  # type: hdf.hdf_dataset
        self._log = None  # type: waf.logging.FileHandler

    def measure_iq(self):
        """Starts an IQClouds like measurement, storing the data inside a Qkit container."""
        self._prepare_measurement_file()
        self._prepare_experiment()
        self._measure_and_store()
        self._cleanup_experiment()
        self._cleanup_measurement_file()

    def _measure_and_store(self):
        data = self.experiment.record()
        data_i = np.atleast_1d(data[0])
        data_q = np.atleast_1d(data[1])
        self._store_data(data_i, data_q)

    def _prepare_experiment(self):
        qkit.flow.start()  # pylint: disable=no-member
        if self.control_mw_src:
            # Enable local oscillators
            try:
                self.qic.readout.local_oscillator.on()
                self.qic.manipulation.local_oscillator.on()
            except AttributeError:
                pass

        # Setup the QiController for the experiment
        self.experiment.configure()

    def _cleanup_experiment(self):
        if self.control_mw_src:
            # Turn off local oscillators again
            try:
                self.qic.readout.local_oscillator.off()
                self.qic.manipulation.local_oscillator.off()
            except AttributeError:
                pass
        qkit.flow.end()  # pylint: disable=no-member

    def _store_data(self, data_i, data_q):
        if len(data_i) != len(data_q):
            logging.warning("%s: I and Q data list do not have same length!", __name__)

        self._data_i.append(data_i)
        self._data_q.append(data_q)

    def _prepare_measurement_file(self):
        self._data_file = hdf.Data(name=self.dirname, mode="a")
        self._data_axis = self._data_file.add_coordinate(
            self.x_coordname, unit=self.x_unit
        )

        # if self.x_vector is None:
        #     self._data_axis.add(np.arange(self.experiment.count, dtype=int))
        # else:
        #     self._data_axis.add(self.x_vector)

        self._data_settings = self._data_file.add_textlist("settings")
        self._data_settings.append(
            waf.get_instrument_settings(self._data_file.get_filepath())
        )

        self._log = waf.open_log_file(self._data_file.get_filepath())

        self._data_i = self._data_file.add_value_vector(
            "i_component", x=self._data_axis, unit=self.data_unit
        )
        self._data_q = self._data_file.add_value_vector(
            "q_component", x=self._data_axis, unit=self.data_unit
        )

        if self.comment is not None:
            self._data_file.add_comment(self.comment)

        if self.open_qviewkit:
            qkit_viewer.plot(self._data_file.get_filepath())

    def _cleanup_measurement_file(self):
        self._data_file.add_view(
            "iq_plane",
            x=self._data_i,
            y=self._data_q,
            view_params={"plot_style": 2, "markersize": 2},
        )

        thread = threading.Thread(
            target=qkit_viewer.save_plots,
            args=[self._data_file.get_filepath(), self.plot_comment],
        )
        thread.start()

        self._data_file.close_file()
        waf.close_log_file(self._log)
