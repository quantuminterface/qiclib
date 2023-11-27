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
"""Module providing support for Qkit."""

# If Qkit present, use Qkit's sample class
# otherwise user will have to populate the object himself,
# but at least it will still work
import warnings

try:
    import qkit
    import qkit.core.instrument_base as _qkinst
    import qkit.measure.samples_class as _sc

    Instrument = _qkinst.Instrument
    QkitSample = _sc.Sample
    from qkit.gui.notebook.Progress_Bar import Progress_Bar
    from qkit.storage.hdf_DateTimeGenerator import DateTimeGenerator

    QKIT_ENABLED = True

    try:
        qkit.instruments
    except AttributeError:
        warnings.warn(
            "If you intend to use the QiController together with Qkit, do not forget "
            "to start it with qkit.start() before creating the QiController instance."
        )
except ImportError:
    Instrument = object
    QkitSample = object
    qkit = None
    Progress_Bar = None
    DateTimeGenerator = None
    QKIT_ENABLED = False


class SampleObject(QkitSample):
    """Sample object to store experiment specific values.

    The experiment classes (:class:`qiclib.experiment.base.BaseExperiment`) use
    these values to configure the `qiclib.hardware.controller.QiController`.

    .. note:: Qkit
        If Qkit is present in the system, additional functionality will be
        available as given by `qkit.measure.samples_class.Sample`.

    .. note::
        Standard experiments require `tpi`, `tpi2`. and `T_rep` to be given by the
        user. Also `rec_pulselength`, `rec_duration`, and `rec_offset` should be
        set. This can be done by running `qiclib.experiment.autoconf_readout.AutoconfReadout`
        or `qiclib.experiment.base.BaseExperiment.configure_readout_pulse`.
        Alternatively, the values can be set manually in this sample object.

    :ivar tpi:
        The time of a pi pulse in seconds.
    :type tpi: float
    :ivar tpi2:
        The time of a pi/2 pulse in seconds.
    :type tpi2: float
    :ivar T_rep: float
        The delay between consecutive executions on the QiController in seconds.
    :ivar fr: float
        The frequency of the readout resonator in Hz.
    :ivar f01: float
        The frequency of the qubit state transition in Hz.
    :ivar rec_pulselength: float
        The pulse length of the standard readout pulse in seconds.
    :ivar rec_duration: float
        The duration of the recording window in seconds.
    :ivar rec_offset: float
        The delay between triggering the readout pulse and starting the recording in seconds.
    :ivar rec_phase: float
        The phase offset of the internal oscillator used for the down-conversion.
        Only relevant if not in the interferometer recording mode.
    :ivar rec_if_frequency: float
        The frequency of the internal oscillator to generate and down-convert
        the IF frequency readout pulse.
    :ivar rec_shift_offset: int (-15 - 15)
        The value_shift_offset to use for the recording. A value of 0 will not cause
        any overflow but might reduce signal quality as less bits are used.
        Higher values will increase signal level but might lead to overflow.
    :ivar rec_shift_average: int (0-15)
        The average_shift to use for the recording.
    :ivar rec_ref_delay: float
        The delay between the signal and the reference input.
        Only relevant if in the interferomenter recording mode.
    :ivar rec_interferometer_mode: bool
        If the recording module is operated in the interferometer mode.
    :ivar manip_if_frequency: float
        The frequency of the internal oscillator to generate
        the IF frequency manipulation pulses.

    """
