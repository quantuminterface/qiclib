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
r"""This module contains the driver to control a signal recorder on the QiController.

A signal recorder is a part of the digital unit cell (see :class:`qiclib.hardware.unitcell`).
Each cell contains one signal recorder to process returning readout signals.

The signal recorder receives the digitized microwave signals from the ADCs in the
complex-valued baseband (as in-phase and quadrature components, I/Q). After an initial
signal conditioning, a digital-down-conversion (DDC) follows using a complex mixer
followed by an accumulator acting as boxcar integrator. The demodulated I and Q value
are further evaluated to obtain the estimated state of the qubit. All results are
forwarded to a separate data storage module (see :mod:`qiclib.hardware.storage`).
There, the desired results are selected, aggregated and consecutively persisted in one or multiple
BRAMs for later retrieval by the PS and the user.

.. todo:: Figure for structure of signal recorder.

A typical readout operation will trigger a signal generator to play a pulse with a
certain length. After some latency and electrical delay through the setup, a modified
version of the pulse will arrive at the recording module. Then, the pulse has to be
demodulated and evaluated by the signal recorder to obtain the amplitude and phase
response of the investigated system. To cover this, the sequencer will not only trigger
the signal generator but simultaneously also activate the signal recorder.
In the signal recorder, a trigger delay is specified to compensate for the latency of
the pulse through electronics and experiment setup. By adjusting the duration of the
recording to the length of the pulse, the accumulator will then take the whole returned
pulse into account. Using these two parameters, the user can define a rectangular
recording window which will be evaluated by the DDC.

Due to mixer and other imperfections in the analog setup, the raw I and Q data from the
converters might not be well balanced in amplitude or have a 90° phase relation.
To correct for this, a signal conditioning is performed on the raw input data.
It consists of a multiplication with a 2x2 conditioning matrix :math:`M_\mathrm{cond}`
following after an offset subtraction to remove a potential DC offset:

.. math::

   \begin{pmatrix} I_\mathrm{out}\\Q_\mathrm{out}\end{pmatrix} =
   M_\mathrm{cond} \left[ \begin{pmatrix} I_\mathrm{in}\\Q_\mathrm{in} \end{pmatrix} -
   \begin{pmatrix} I_\mathrm{offset}\\Q_\mathrm{offset} \end{pmatrix} \right]

The corrected raw time trace is then stored inside a separate memory whenever a
recording is performed. The memory thus always contains a snapshot of the raw data used
for the last demodulated I and Q value. Due to the limited size of the memory, it can
only store up to 1024ns of raw data. If longer recording durations are set, only the
beginning of the incoming raw time trace will be persisted in the BRAM. The stored time
trace can later be used for debugging purposes or to visualize the raw input.

At the same time, the conditioned signal will also be down-converted by complex
multiplication with a reference oscillation from an NCO. The NCO is of the same type as
in the signal generator and both are synchronized at the beginning of an experiment to
have a stable phase relation and reproducible results. The phase offset of the reference
in the signal recorder can furthermore be adapted to rotate the down-converted signal in
the I/Q plane to a desired position.

After the complex multiplication, a low-pass filter and decimation are necessary to
average the resulting I and Q component. These components then correspond to the
amplitude and phase response of the resonator. In the signal recorder, a boxcar
integrator is implemented by using an accumulator to add up the samples over an
adjustable time window. This recording duration can be freely chosen and typically is a
trade-off between a desired fast readout operation and a sufficient signal-to-noise
ratio.

The accumulation will add up the incoming 16bit I and Q values separately for the
specified time window in two 32bit accumulator registers. Therefore, a minimum of 2^16 =
65536 samples can be averaged without creating an overflow, corresponding to recording
durations of over 65µs. After this step, the values will be reduced back to 16bit.
An overflow of the values during this operation can be prevented by shifting the values
by a user-defined number of bits before reducing the bit size, see
:meth:`Recording.value_shift` for more details. It can be beneficial for the signal quality to
intentionally reduce this shift to increase the obtained signal strength.

While conditioning and complex multiplication are performed continuously, the boxcar
integration as well as the storage of the raw time trace are only activated when the
signal recorder receives a trigger signal. Once the recording duration has passed, the
accumulated I/Q result value is passed to the data storage, as well as to a state
estimation routine. In the latter, the result is transformed into a binary information
of 0 or 1 corresponding to the estimation of the measured qubit state. This state result
will be directly returned to the sequencer which can be programmed to wait for this
value and store it in a register. The state will also be passed to the data storage
where it can be aggregated and saved for later retrieval. For more information regarding
the state discrimination, refer to :meth:`Recording.state_config`.

For simple experiments, the signal recorder also provides an averaging functionality,
see :meth:`Recording.get_averaged_result`.

Different operation modes of the signal recorder can be distinguished, based on the
received trigger value, see :class:`RecordingTrigger` for details.
"""

from __future__ import annotations

import warnings
from enum import Enum
from numbers import Number
from typing import Any

import numpy as np
import numpy.typing as npt

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.recording_pb2 as proto
import qiclib.packages.grpc.recording_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import (
    PlatformComponent,
    platform_attribute,
    platform_attribute_collector,
)
from qiclib.packages.servicehub import ServiceHubCall


class RecordingTrigger(Enum):
    """The available trigger commands of the signal recorder.

    They distinguish different operation modes.
    """

    NONE = 0
    """No operation: The signal recorder stays idle when receiving this trigger."""

    SINGLE = 1
    """Perform a single measurement and forward the data to the storage module."""

    ONESHOT = 2
    """Perform a single measurement but do not include it into the result averaging.
    The measurement result will also not be forwarded to the storage module.

    A typical use-case are two consecutive measurements where the first one is only
    used internally and will result in a state estimation on which the sequencer can
    react. The second one is then to obtain a measurement result of the experiment.
    """

    START_CONTINUOUS = 6
    """Continuously perform consecutive measurements and return the values to the
    storage module.

    This mode can be used to obtain a seamless stream of demodulated results without
    the need of the sequencer to trigger each single measurement. The continuous
    mode will continue until a `STOP_CONTINUOUS` trigger is received. This mode
    provides the basis for continuous operation over long periods, e.g. to observe
    state changes of the qubit over time (quantum jumps).
    """

    STOP_CONTINUOUS = 7
    """Stop a continuous measurement after finishing the currently running single
    measurement.
    """

    RESET = 14
    """Reset all internal data of the module, including the averaged result."""

    NCO_SYNC = 15
    """Synchronize the internal reference oscillation by resetting its phase."""


@platform_attribute_collector
class Recording(PlatformComponent):
    """A signal recorder within a digital unit cell of the QiController."""

    def __init__(
        self, name: str, connection, controller, qkit_instrument=True, index: int = 0
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.RecordingStub(self._conn.channel)
        self._index = index
        self._component = dt.EndpointIndex(value=self._index)

    def load_configuration(self, sample, no_warn: bool = False):
        """Load the recording module configuration from a (legacy) sample object.

        .. deprecated::
            `sample` will be removed in future. Therefore, this method becomes obsolete.
            Please use the new QiCode syntax (see `qiclib.code`) instead.

        :param sample:
            The sample object containing the relevant properties.
        :type sample: qiclib.packages.qkit_polyfill.SampleObject
        :param no_warn:
            if warnings should be printed, by default False

        :raises AttributeError:
            if needed values are not properties of the sample
        """
        try:
            self.interferometer_mode = sample.rec_interferometer_mode
        except AttributeError:
            # We just keep it the same as before
            pass

        try:
            self.recording_duration = sample.rec_duration
            self.trigger_offset = sample.rec_offset
        except AttributeError as e:
            raise AttributeError(
                "Recording configuration has to be defined in the sample object! Please configure the readout"
            ) from e

        if self.interferometer_mode:
            try:
                self.reference_delay = sample.rec_ref_delay
            except AttributeError as e:
                raise AttributeError(
                    "Interferometer mode requires a reference delay to be defined in the sample object! "
                    "Please configure it"
                ) from e

        try:
            if self.interferometer_mode:
                self.reference_frequency = sample.rec_if_frequency
            else:
                self.internal_frequency = sample.rec_if_frequency
        except AttributeError as e:
            if not no_warn:
                warnings.warn(
                    "Recording IF frequency is not set in sample object. "
                    + "The current settings will be used. Be aware."
                    + f"\n({e})"
                )

    @ServiceHubCall
    def reset(self):
        """Resets the signal recorder. This will also interrupt ongoing measurements."""
        self._stub.Reset(self._component)

    def check_status(self, raise_exceptions: bool = True) -> bool:
        """Check if any status flags are set and report them, if any.

        :param raise_exceptions: bool, optional
            if assigned status flags will result in an exception or just in a warning
            output.

        :raises Warning:
            if a status flag was set and `raise_exceptions` was set to True.
        """
        response = self._stub.ReportStatus(self._component)
        status_report = response.report
        status_ok = not response.failure

        # Workaround: Do not consider clipping of ADC as error
        # TODO Think of more practical solution (detect shot noise vs. permanent clipping)
        filtered_report = []
        for line in status_report.splitlines():
            if (
                "channel input exceeds the valid range. Please reduce the voltage level at the ADC!"
                not in line
            ):
                filtered_report.append(line)
            else:
                warnings.warn(
                    "The following Recording module error is filtered out without interrupting the execution:\n"
                    + line
                )
        status_report = "\n".join(filtered_report)
        if status_report:
            status_ok = False
            status_report += "\n"  # Add final new line again
        else:
            status_ok = True

        if not status_ok:
            status_report += (
                f"The last accepted trigger signal was: {self.last_trigger}"
            )
            self.reset_status_report()
            if raise_exceptions:
                raise Warning(status_report)
            warnings.warn(status_report)

        return status_ok

    @ServiceHubCall
    def get_status_report(self) -> str:
        """Returns a hardware status report of the signal recorder."""
        return self._stub.ReportStatus(self._component).report

    @ServiceHubCall
    def reset_status_report(self):
        """Resets the status flags of the signal recorder.

        This does not affect ADC over range settings! Use qic.rfdc.reset_status()
        to reset this flag. Be aware that status flags of other signal recorders
        will also be discarded in that case, so better check all before!
        """
        self._stub.ResetStatus(self._component)

    @property
    @ServiceHubCall
    def last_trigger(self) -> RecordingTrigger | int:
        """The last trigger processed by the module."""
        trigger: int = self._stub.GetLastTrigger(self._component).value
        try:
            return RecordingTrigger(trigger)
        except ValueError:
            return trigger

    @ServiceHubCall
    def trigger_manually(self, trigger: RecordingTrigger | int):
        """Manually triggers the signal recorder."""
        if not isinstance(trigger, RecordingTrigger):
            # This will throw a ValueError if trigger is not valid
            trigger = RecordingTrigger(trigger)
        self._stub.TriggerManually(
            proto.Trigger(index=self._component, value=trigger.value)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def interferometer_mode(self) -> bool:
        """If the interferometer operation mode of the signal recorder is active.

        In the interferometer mode, the signal input for I acts as data, Q as reference
        signal. There, you have to specify `Recording.reference_frequency` and
        `Recording.reference_delay` according to your signals.

        In the normal/default mode (value is False), the internal reference is used for
        down conversion of the signal and `Recording.internal_frequency` and
        `Recording.phase_offset` need to be configured.
        """
        return self._stub.IsInterferometerMode(self._component).is_interferometer

    @interferometer_mode.setter
    @ServiceHubCall
    def interferometer_mode(self, interferometer_mode: bool = True):
        """Changes the operation mode of the recording module between:
        * Normal Mode (if False): Internal Reference is used for down conversion
          * Specify `internal_frequency` and `phase_offset` to configure
        * Interferometer Mode: Signal input for I acts as data, Q as reference signal
          * Specify `reference_frequency` and `reference_delay` according to your signals
        """
        self._stub.SetInterferometerMode(
            proto.InterferometerMode(
                index=self._component, is_interferometer=interferometer_mode
            )
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def trigger_offset(self) -> float:
        """The trigger offset in seconds.

        This is the time in the signal recorder between receiving a trigger and starting
        the internal data recording. Typically, readout pulse generation and signal
        recorder are triggered simultaneously. Therefore, this value needs to be
        adjusted to compensate for the electrical delay of the pulse through the setup
        and experiment.
        """
        return self._stub.GetTriggerOffset(self._component).value

    @trigger_offset.setter
    @ServiceHubCall
    def trigger_offset(self, trigger_offset: float):
        self._stub.SetTriggerOffset(
            proto.TriggerOffset(index=self._component, value=trigger_offset)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def recording_duration(self) -> float:
        """The recording duration in seconds.

        This is the duration over which the returned signal is evaluated and reduced
        using a digital-down-conversion and an accumulation stage. The duration will
        always be rounded to the nearest integer 4ns step.
        """
        return self._stub.GetRecordingDuration(self._component).value

    @recording_duration.setter
    @ServiceHubCall
    def recording_duration(self, recording_duration: float):
        self._stub.SetRecordingDuration(
            proto.RecordingDuration(index=self._component, value=recording_duration)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def value_shift(self) -> int:
        """The number of bits each single result value is shifted to the right in the
        hardware, corresponding to a division by `2 ** value_shift`.

        .. warning::
            Usually, one would change the `Recording.value_shift_offset` instead of directly
            setting the value shift here. The offset will also take into account the length
            of the recording and is therefore more robust.

        Remarks
        -------
        Inside the hardware, the result values will first be calculated as 32bit values
        to provide high accuracy during the evaluation. However, afterwards, the values
        will be reduced back to 16bit internally. Using the value shift, it can be
        prevented that the resulting value exceeds the valid 16bit range.

        By default, this value shift is automatically calculated by the drivers based on
        the recording duration so an overflow cannot happen (see
        `Recording.value_shift_offset`). Especially if the digital input range of the
        ADC is not maxed out, however, it can be beneficial for the signal quality to
        intentionally reduce this shift to increase the obtained signal strength.

        A status flag will indicate if an overflow happened when reducing the bit size
        after the value shift. This gives the user the feedback that the obtained data
        is corrupted and the value shift should be increased.
        """
        return self._stub.GetValueShift(self._component).value

    @value_shift.setter
    @ServiceHubCall
    def value_shift(self, value_shift: int):
        if value_shift < 0:
            raise ValueError("value_shift must not be negative!")
        self._stub.SetValueShift(
            proto.ValueShift(index=self._component, value=value_shift)
        )

    @property
    @ServiceHubCall
    def value_factor(self) -> int:
        return 2**self.value_shift

    @property
    @platform_attribute
    @ServiceHubCall
    def expected_highest_signal_amplitude(self) -> int:
        """
        Return the highest amplitude that the recording module expects in ADC units.
        By default, this is `2 ** 15 - 1`.
        Decreasing this value from its initial may increase the signal quality
        as there might be fewer bits that are cut when evaluating the input signal.
        """
        return self._stub.GetExpectedHighestSignalAmplitude(self._component).value

    @expected_highest_signal_amplitude.setter
    @ServiceHubCall
    def expected_highest_signal_amplitude(self, amplitude: int):
        self._stub.SetExpectedHighestSignalAmplitude(
            dt.IndexedInt(index=self._component, value=abs(amplitude))
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def average_shift(self) -> int:
        """The number of bits the averaged result value is shifted to the right in the
        hardware, corresponding to a division by `2 ** average_shift`.

        This might be necessary if the number of performed averages (see
        `Sequencer.averages`) becomes too large. For normal operation with QiCode, the
        average result is not used at all, and the average_shift does not have any
        influence on the result data (as only single results are used in normal
        operation).

        An average overflow can happen if the sum of the single results which is
        calculated to get the average result exceeds the range of 32bit.
        In this case, increasing the average_shift can help.
        """
        return self._stub.GetAverageShift(self._component).value

    @average_shift.setter
    @ServiceHubCall
    def average_shift(self, average_shift: int):
        if average_shift < 0:
            raise ValueError("average_shift must not be negative!")
        self._stub.SetAverageShift(
            proto.AverageShift(index=self._component, value=average_shift)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def internal_frequency(self) -> float:
        """The frequency in Hz of the internal reference oscillator. It is used for the
        digital down-conversion of the input signal.

        If a previously created pulse from a signal generator should be processed, the
        same frequency as set in `qiclib.hardware.pulsegen.PulseGen.internal_frequency`
        can be used. (The required negation of the frequency to be used for the
        down-conversion is handled within the hardware.)
        """
        return self._stub.GetInternalFrequency(self._component).value

    @internal_frequency.setter
    @ServiceHubCall
    def internal_frequency(self, frequency: float):
        self._stub.SetInternalFrequency(
            proto.Frequency(index=self._component, value=frequency)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def phase_offset(self) -> float:
        """The phase offset in radian of the internal reference oscillator.

        It can be adapted to rotate the down-converted signal in the I/Q plane to a
        desired position (e.g. to be located on one of the axes).
        """
        return self._stub.GetInternalPhaseOffset(self._component).value

    @phase_offset.setter
    @ServiceHubCall
    def phase_offset(self, phase_offset: float):
        self._stub.SetInternalPhaseOffset(
            proto.PhaseOffset(index=self._component, value=phase_offset)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def reference_frequency(self) -> float:
        """The reference input frequency (typically the IF readout frequency). It is
        only used when the `Recording.interferometer_mode` is active.

        This specification is necessary in order to determine the pi/2 shift.
        It is important that the shift is a multiple of the sample time
        (e.g. 1ns for 1GHz sampling rate -> frequency of 250 MHz / n).
        """
        return self._stub.GetReferenceFrequency(self._component).value

    @reference_frequency.setter
    @ServiceHubCall
    def reference_frequency(self, reference_frequency: float):
        self._stub.SetReferenceFrequency(
            proto.Frequency(index=self._component, value=reference_frequency)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def reference_delay(self) -> float:
        """The relative offset between the referance and the signal path. It is only
        used when the `Recording.interferometer_mode` is active.

        Typically, the reference path is shorter than the signal path. Using this value,
        the reference can be delayed by the given time so both signal and reference
        arrive at the same time within the demodulation part. The minimum delay is
        2 cycles (8ns), and normal operation starts from 4 cycles (16ns).
        """
        return self._stub.GetReferenceDelay(self._component).value

    @reference_delay.setter
    @ServiceHubCall
    def reference_delay(self, reference_delay: float):
        self._stub.SetReferenceDelay(
            proto.ReferenceDelay(index=self._component, value=reference_delay)
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def conditioning_matrix(self) -> tuple[float, float, float, float]:
        """A matrix `CM` to condition the incoming raw IQ signal.
        Amplitude modifications and/or rotations on the IQ plane are possible.

        Due to mixer and other imperfections in the analog setup, the raw I and Q data
        from the converters might not be well balanced in amplitude or have a 90° phase
        relation. To correct for this, a signal conditioning is performed on the raw
        input data. It consists of a multiplication with a 2x2 conditioning matrix CM
        following after an offset subtraction to remove a potential DC offset. For the
        latter, refer to `Recording.conditioning_offset`.

        .. code-block:: python

            CM = (CM_II, CM_IQ, CM_QI, CM_QQ)

            IQ_out = CM * IQ_in

            ( I_out )     ( CM_II  CM_IQ )   ( I_in )
            ( Q_out )  =  ( CM_QI  CM_QQ ) * ( Q_in )

        """
        matrix = self._stub.GetConditioningMatrix(self._component)
        return matrix.ii, matrix.iq, matrix.qi, matrix.qq

    @conditioning_matrix.setter
    @ServiceHubCall
    def conditioning_matrix(
        self, matrix: npt.NDArray[np.float64] | tuple[float, float, float, float]
    ):
        if isinstance(matrix, np.ndarray) and np.shape(matrix) == (2, 2):
            # Accept numpy matrix
            matrix = np.ndarray.ravel(matrix)
        if len(matrix) != 4 or any(not isinstance(n, Number) for n in matrix):
            raise ValueError("Only a matrix with four numeric elements is accepted!")
        self._stub.SetConditioningMatrix(
            proto.ConditioningMatrix(
                index=self._component,
                ii=matrix[0],
                iq=matrix[1],
                qi=matrix[2],
                qq=matrix[3],
            )
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def conditioning_offset(self) -> tuple[int, int]:
        """A vector `IQ_offs` specifying an offset that will be substracted from the
        incoming raw IQ signal to correct for a potential DC offset.

        This will happen before a following matrix multiplication. For more details,
        see `Recording.conditioning_matrix`.

        .. code-block:: python

            IQ_offs = (I_offs, Q_offs)

            IQ_out = IQ_in - IQ_offs

            (I_out)(I_in)(I_offs)
            (Q_out) = (Q_in) - (Q_offs)
        """
        offset = self._stub.GetConditioningOffset(self._component)
        return offset.i, offset.q

    @conditioning_offset.setter
    @ServiceHubCall
    def conditioning_offset(self, offset: tuple[int, int]):
        self._stub.SetConditioningOffset(
            proto.ConditioningOffset(
                index=self._component,
                i=round(offset[0]),
                q=round(offset[1]),
            )
        )

    @property
    @platform_attribute
    @ServiceHubCall
    def state_config(self) -> tuple[int, int, int]:
        r"""The configuration for the state discrimination as triplet (a_I, a_Q, b).

        To distinguish between states 0 and 1, in most cases, it is sufficient to
        determine a linear discriminant of the form :math:`\vec{a}^T \vec{m} + b = 0`
        for the I/Q plane of the result values. By checking on which side of the
        discriminant a measurement result :math:`\vec{m} = (I,Q)^T` is located, the
        qubit state can then be inferred. If a result is located directly on the
        discrimination line, it is attributed to the positive semi-plane.

        The values :math:`\vec{a} = (a_\mathrm{I}, a_\mathrm{Q})^T)` and :math:`b`
        have to be calibrated and can then be configured here as 32bit signed integers.
        For this, `qiclib.packages.utility.calculate_stater_config` might be helpful.

        As only integers are allowed, special care has to be taken that rounding errors
        do not play an important role. This can be easily prohibited by multiplying the
        coefficients by a common factor. This will not change the discrimination line
        and the resulting coefficients can be chosen so that the relative errors when
        rounding become small.

        .. todo:: Ilustration of qubit state estimation
        """
        config = self._stub.GetStateConfig(self._component)
        return config.value_ai, config.value_aq, config.value_b

    @state_config.setter
    @ServiceHubCall
    def state_config(self, state_config: tuple[int, int, int]):
        if len(state_config) != 3:
            raise ValueError(
                "State configuration has to be passed as triplet (a_I, a_Q, b)!"
            )
        self._stub.SetStateConfig(
            proto.StateConfig(
                index=self._component,
                value_ai=int(state_config[0]),
                value_aq=int(state_config[1]),
                value_b=int(state_config[2]),
            )
        )

    @property
    def state_config_ai(self) -> int:
        """The direction vector's I component of the state discrimination configuration.

        See `Recording.state_config` for more details on the state discrimination.
        """
        return self.state_config[0]

    @property
    def state_config_aq(self) -> int:
        """The direction vector's Q component of the state discrimination configuration.

        See `Recording.state_config` for more details on the state discrimination.
        """
        return self.state_config[1]

    @property
    def state_config_b(self) -> int:
        """The offset value of the state discrimination configuration.

        See `Recording.state_config` for more details on the state discrimination.
        """
        return self.state_config[2]

    @ServiceHubCall
    def get_averaged_result(self, verify: bool = True) -> tuple[int, int]:
        """Returns the averaged result of a previous experiment as I and Q tuple.

        These resemble the complex fourier coefficient of the input signal at the
        `Recording.internal_frequency` (due to the digital-down-conversion).

        Single results obtained from the accumulator will be further summed up until the
        module is reset externally. This is especially helpful if a single measurement
        should be performed and repeated many times to obtain an averaged I and Q result
        value. In normal operation, the averaging functionality is not used as it does
        not support parameter variations and multiple results per sequencer execution.

        .. note::
            Using `qiclib.hardware.sequencer.Sequencer.averages`, the number of averages can
            be defined. The returned averaged result values will also have to be divided by
            the number of averages, as only the sum is calculated on the hardware.

        :param verify:
            if errors that happened previously on the QiController should raise an
            exception and cause the platform to stop, by default True

        :return:
            the averaged result as I and Q value
        """
        self._qip.check_errors(verify, verify)
        result = self._stub.GetAveragedResult(self._component)
        return result.i_value, result.q_value

    @ServiceHubCall
    def get_single_result(self, verify: bool = True) -> tuple[int, int]:
        """Returns the last single result of a previous experiment as I and Q tuple.

        These resemble the complex fourier coefficient of the input signal at the
        `Recording.internal_frequency` (due to the digital-down-conversion).

        This is only the last single result. To obtain all single results of the last
        experiment, refer to `Recording.get_result_memory`.

        :param verify:
            if errors that happened previously on the QiController should raise an
            exception and cause the platform to stop

        :return:
            the single result as I and Q value
        """
        self._qip.check_errors(verify, verify)
        result = self._stub.GetSingleResult(self._component)
        return result.i_value, result.q_value

    @property
    @ServiceHubCall
    def result_memory_is_full(self) -> bool:
        """If the result memory is full."""
        return self._stub.GetResultMemoryStatus(self._component).full

    @property
    @ServiceHubCall
    def result_memory_is_empty(self) -> bool:
        """If the result memory is empty."""
        return self._stub.GetResultMemoryStatus(self._component).empty

    @property
    @ServiceHubCall
    def result_memory_size(self) -> int:
        """The number of recorded values (16bit I + 16bit Q each) inside the result
        memory.

        The memory can hold up to 1024 values.
        """
        return self._stub.GetResultMemorySize(self._component).size

    @ServiceHubCall
    def get_result_memory(
        self, size: int = 0, verify: bool = True
    ) -> tuple[list[int], list[int]]:
        """Returns the result memory containing a list of all single results obtained
        during the last experiment execution.

        See `Recording.get_single_result` for information on the kind of information the
        single result values hold.

        :param size: int, optional
            how many results to collect from the memory, by default the size is
            automatically determined to return all recorded results
        :param verify: bool, optional
            if errors that happened previously on the QiController should raise an
            exception and cause the platform to stop, by default True

        :return:
            two lists with the single results where I and Q values are separated
        """
        self._qip.check_errors(verify, verify)
        lists = self._stub.GetResultMemory(
            proto.MemorySize(index=self._component, size=size)
        )
        return lists.result_i, lists.result_q

    @ServiceHubCall
    def get_raw_timetrace(
        self, size: int = 0, verify: bool = True
    ) -> tuple[list[int], list[int]]:
        """Returns the last raw time as I/Q values trace obtained during a previous
        experiment execution.

        .. note::
            The obtained data already passed through the conditioning module, so its
            influence can be observed in the data, see `Recording.conditioning_matrix` for
            more information on this module.

        :param size: int, optional
            how many samples to collect from the memory, by default the whole memory is
            fetched (1024ns of data)

        :param verify: bool, optional
            if errors that happened previously on the QiController should raise an
            exception and cause the platform to stop, by default True

        :return:
            two lists with the raw time trace of the I and Q channel
        """
        self._qip.check_errors(verify, verify)
        trace = self._stub.GetRawMemory(
            proto.MemorySize(index=self._component, size=size)
        )
        return trace.raw_i, trace.raw_q

    def get_configuration_dict(self) -> dict[str, Any]:
        """Returns a dictionary containing all configuration values which will not be
        automatically overwritten for each experiments (esp. calibration values).

        :return:
            containing configuration and calibration values of this signal generator.
        """
        return {
            "value_shift": self.value_shift,
            "expected_highest_signal_amplitude": self.expected_highest_signal_amplitude,
            "phase_offset": self.phase_offset,
            "reference_delay": self.reference_delay,
            "conditioning_matrix": self.conditioning_matrix,
            "conditioning_offset": self.conditioning_offset,
            "interferometer_mode": self.interferometer_mode,
            "average_shift": self.average_shift,
            "reference_frequency": self.reference_frequency,
            "state_config": self.state_config,
        }

    ### DEPRECATED FUNCTION REGION ###

    @property
    def recording_length(self):
        """The recording duration in seconds.

        .. deprecated::
            Use recording_duration instead!
        """
        # TODO: Remove occurrences of recording_length in qiclib package
        warnings.warn(
            "Deprecation Warning: recording_length is deprecated, please use recording_duration instead."
        )
        return self.recording_duration

    @recording_length.setter
    def recording_length(self, recording_length):
        warnings.warn(
            "Deprecation Warning: recording_length is deprecated, please use recording_duration instead."
        )
        self.recording_duration = recording_length

    @property
    def nco_frequency(self):
        """The internal frequency in Hz used for the down-conversion of the input signal.

        .. deprecated::
            Use internal_frequency instead!
        """
        warnings.warn(
            "Deprecation Warning: nco_frequency is deprecated, please use internal_frequency instead."
        )
        return self.internal_frequency

    @nco_frequency.setter
    def nco_frequency(self, nco_frequency):
        warnings.warn(
            "Deprecation Warning: nco_frequency is deprecated, please use internal_frequency instead."
        )
        self.internal_frequency = nco_frequency

    def read_iq_fourier(self):
        """Returns the averaged fourier coefficients at the `internal_frequency` for I and Q.

        .. deprecated::
            Use get_averaged_result() instead!
        """
        warnings.warn(
            "Deprecation Warning: read_iq_fourier() is deprecated, please use get_averaged_result() instead."
        )
        return self.get_averaged_result()

    @property
    def stater_config_ai(self):
        """The direction vector's I component of the state discrimination configuration.

        .. deprecated::
            Use state_config_ai instead!
        """
        warnings.warn(
            "Deprecation Warning: stater_config_ai is deprecated, please use state_config_ai instead."
        )
        return self.state_config_ai

    @property
    def stater_config_aq(self):
        """The direction vector's Q component of the state discrimination configuration.

        .. deprecated::
            Use state_config_aq instead!
        """
        warnings.warn(
            "Deprecation Warning: stater_config_aq is deprecated, please use state_config_aq instead."
        )
        return self.state_config_aq

    @property
    def stater_config_b(self):
        """The offset value of the state discrimination configuration.

        .. deprecated::
            Use state_config_b instead!
        """
        warnings.warn(
            "Deprecation Warning: stater_config_b is deprecated, please use state_config_b instead."
        )
        return self.state_config_ai

    def set_stater_config(self, stater_cfg):
        """Sets the configuration for the state discrimination. Expects a triplet (a_I, a_Q, b).
        This method will cast all floating point numbers to integers without rounding.

        .. deprecated:
            Use assignment to state_config instead!
        """
        warnings.warn(
            "Deprecation Warning: set_stater_config(...) is deprecated, please use state_config instead."
        )
        self.state_config = stater_cfg

    def read_stater_config(self):
        """Returns the configuration for the state discrimination as a triplet (a_I, a_Q, b).

        .. deprecated::
            Read value of state_config instead!"""
        warnings.warn(
            "Deprecation Warning: read_stater_config() is deprecated, please use state_config instead."
        )
        return self.state_config
