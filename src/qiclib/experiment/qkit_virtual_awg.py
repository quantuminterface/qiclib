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
from __future__ import annotations

import warnings
from collections.abc import Iterable, Sized
from typing import Any

import numpy as np
import numpy.typing as npt
from qkit.measure.timedomain.pulse_sequence import (
    Pulse,
    PulseSequence,
    PulseType,
    ShapeLib,
)
from qkit.measure.timedomain.VirtualAWG import VirtualAWG

from qiclib import QiController
from qiclib.coding.sequencercode import SequencerCode
from qiclib.experiment.base import BaseExperiment
from qiclib.hardware.pulsegen import TriggerSet
from qiclib.packages.constants import CONTROLLER_SAMPLE_FREQUENCY_IN_HZ as samplerate
from qiclib.packages.qkit_polyfill import QKIT_ENABLED

if not QKIT_ENABLED:
    raise ImportError("Qkit is required to use the QkitVirtualAWG loader...")


class QkitVirtualAWG(BaseExperiment):
    """
    This experiment class loads the PulseSequences stored in a Qkit VirtualAWG instance
    onto the QiController. It also supports execution of the sequence with the variables
    given inside the VirtualAWG class.

    :param controller:
        First parameter is the QiController itself
    :param awg:
        Instance of Qkit's VirtualAWG class containing PulseSequences and Variables

    :raises NotImplementedError:
        If more than one channel is loaded
    :raises NotImplementedError:
        If interleaved sequences are use
    :raises NotImplementedError:
        If more than one sequence is loaded
    :raises Exception:
        If a parameterized pulse is skipped
    :raises Exception:
        If other than rectangular pulses and waits are parameterized
    :raises Exception:
        If the number of parameterized pulses exceeds 29
    :raises Exception:
        If more than one pulse of the same type is executed simultainously
    :raises Exception:
        If fixed pulses of the same type overlap

    Usage
    -----
    If you have a QiController instance `qic` which is already initialized:
    .. code-block:: python

        import numpy as np
        from qkit.measure.timedomain.sequence_library import t1
        from qkit.measure.timedomain.VirtualAWG import VirtualAWG

        seq = t1(qic.sample)
        awg = VirtualAWG(qic.sample)

        delays = np.arange(0, 200e-9, 20e-9)
        awg.add_sequence(seq, t=delays)

        exp = ql.exp.QkitVirtualAWG(qic, awg)
        data = exp.run()

    or if you use Qkit to collect the data, the last line can be replaced by:
    .. code-block:: python

        from qkit.measure.timedomain.measure_td import Measure_td

        m = Measure_td(qic.sample, exp.readout)
        m.set_x_parameters(delays, "delay", None, "s")
        m.dirname = "t1"
        m.measure_1D_AWG(iterations=5)  # How often to repeat the whole measurement

    Current limitations
    -------------------
    - Parametrized lengths need to be zero or not zero at the same time (not independently)
    - Pulses of the same type (readout/manipulation) cannot overlap
    - Parametrized pulses need to be of rectangular shape and cannot be skipped
    - A maximum of 16 parametrized pulses/waits can be loaded
    - A maximum of 13 readout and 13 manipulation pulses can be loaded
    - No two readout pulses can be played within the recording time of the first one
    - Variable amplitudes are not yet supported
    """

    def __init__(self, controller: QiController, awg: VirtualAWG):
        super().__init__(controller)

        self.awg = awg  # the Qkit VirtualAWG
        if awg.channel_count != 1:
            raise NotImplementedError("Currently, only 1 channel can be loaded!")
        chan = self.awg.channels[1]
        if chan.is_interleaved:
            raise NotImplementedError(
                "Currently, interleaved sequences are not possible!"
            )
        if chan.sequence_count != 1:
            raise NotImplementedError("Currently, only 1 sequence can be loaded!")
        sequence, variables = chan.get_sequence(0)
        self.sequence: PulseSequence = sequence
        self.variables: dict[str, float | list[float]] = variables

        # performs a overlap check if only fix pulses are present.
        readout_timer = 0
        pulse_timer = 0
        timer = 0
        # stores the parametrized pulses and the number of the delay register where the duration will be written in.
        self.delay_register: dict[Pulse, int] = {}
        self.iterations = 1  # three if a parametrized pulse is present
        self.parametrized = False  # True if a parametrized Pulse is present
        register_counter = 1
        # an overlap test will be performed if the sequence contains only fix pulses.
        overlap_test = True
        for item in sequence.sequence:
            for pulse in item:
                if pulse.is_parametrized:
                    self.parametrized = True
                    self.iterations = 3
                    if pulse != item[-1]:
                        raise RuntimeError("a parametrized pulse can not be skipped")
                    if pulse.shape != ShapeLib.rect and pulse.type != PulseType.Wait:
                        raise RuntimeError(
                            "only rectangular shaped pulses and waits can be parametrized."
                        )
                    if pulse not in self.delay_register:
                        self.delay_register[pulse] = register_counter
                        register_counter += 1
                    # using a fixed pulse parallel to a parametrized pulse can cause to overwriting one of them.
                    if len(item) > 1:
                        warnings.warn(
                            "when setting the variable values be aware triggering two pulses of the same type at the same time is not supported"
                        )
                if register_counter > 29:
                    raise RuntimeError(
                        "number of parametrized Pulses exceeded 29. Your Sequence got too many parametrized Pulses."
                    )
        if self.delay_register:
            # test can not be performed if a parametrized pulse is present due to unknown length.
            overlap_test = False
        for item in sequence.sequence:
            pulse_types = [pulse.type for pulse in item]
            if (
                pulse_types.count(PulseType.Pulse) > 1
                or pulse_types.count(PulseType.Readout) > 1
            ):
                raise RuntimeError(
                    "Executing more than one pulse of the same type simultaneously is not supported"
                )
            # this is a sanity check for fixed sequences
            if overlap_test:
                pulse_durations = [pulse.length() for pulse in item]
                if readout_timer > timer and PulseType.Readout in pulse_types:
                    raise RuntimeError(
                        "A readout is overlapped by a previous one. Please check your sequence"
                    )
                if pulse_timer > timer and PulseType.Pulse in pulse_types:
                    raise RuntimeError(
                        "A Pulse is overlapped by a previous one. Please check your sequence"
                    )
                try:
                    readout_timer += pulse_durations[
                        pulse_types.index(PulseType.Readout)
                    ]  # point of time where the last readout ends
                except (ValueError, KeyError):
                    pass
                try:
                    pulse_timer += pulse_durations[
                        pulse_types.index(PulseType.Pulse)
                    ]  # point of time where the last pulse ends
                except (ValueError, KeyError):
                    pass
                timer += min(pulse_durations)
                if readout_timer > timer:
                    pass
                else:
                    readout_timer = timer
                if pulse_timer > timer:
                    pass
                else:
                    pulse_timer = timer

    def _configure_readout(self, no_warn=False):
        """overwrites the _configure_readout method of BaseExperiment class.
        Loads readout pulses of a sequence in successive readout triggersets.

        :param no_warn: bool, optional
            if false there will be no warning if not set parameters in qic.sample are set to default , by default False

        :raises AttributeError:
            if the length or if frequency of the recording pulse is not set in qic.sample
        :raises Exception:
            if one uses more than 13 different readout pulses within the sequence.

        """
        # Test if values to configure the readout are in the sample object
        try:
            self.qic.sample.rec_pulselength
        except AttributeError as e:
            raise AttributeError(
                "Readout pulse length has to be defined in the sample object! Please configure the readout"
            ) from e

        # If phase offset is unset initialize by default value
        try:
            self.qic.sample.rec_phase
        except AttributeError:
            self.qic.sample.rec_phase = 0
        readout_pulses = [
            pulse
            for pulse in self.sequence.pulses.values()
            if pulse.type == PulseType.Readout
        ]  # store all readout pulses
        if len(readout_pulses) > 13:
            raise RuntimeError(
                "Number of readouts exceeded 13. Your sequence got to many different pulses."
            )
        self._readout_dict = {}
        triggerset_counter = 1
        self.qic.readout.reset_env_mem()
        for pulse in readout_pulses:
            self._load_pulse(
                pulse, self.qic.readout.triggerset[triggerset_counter]
            )  # loads the readout pulses in triggersets
            # stores pulse name and triggerset number for later use
            self._readout_dict[pulse.name] = triggerset_counter
            if pulse.is_parametrized:
                # special pulse to end a parametrized readout
                choke_pulse = Pulse(4e-09, amplitude=0)
                # chocke pulse uses triggerset 14
                self._load_pulse(choke_pulse, self.qic.readout.triggerset[14])
            triggerset_counter += 1
        try:
            self.qic.readout.if_frequency = self.qic.sample.rec_if_frequency
        except AttributeError as e:
            if not no_warn:
                warnings.warn(
                    "Recording IF frequency is not set in sample object. "
                    + "The current settings will be used. Be aware."
                    + f"\n({e})"
                )

        self.qic.recording.load_configuration(self.qic.sample, no_warn=no_warn)

    def _configure_drive_pulses(self):
        """overwrites the _configure_drive_pulses method of BaseExperiment class.
        loads manipulation pulses of a pulssequence in successive manipulation triggersets.

        :raises Exception:
            if one uses more than 13 different manipulation pulses within the sequence.
        """
        manipulation_pulses = [
            pulse
            for pulse in self.sequence.pulses.values()
            if pulse.type == PulseType.Pulse
        ]  # stores manipulation pulses
        if len(manipulation_pulses) > 13:
            raise RuntimeError(
                "Number of pulses exceeded 13. Your sequence got to many different pulses."
            )
        self._manipulation_dict = {}
        triggerset_counter = 1
        self.qic.manipulation.reset_env_mem()
        for pulse in manipulation_pulses:
            self._load_pulse(
                pulse, self.qic.manipulation.triggerset[triggerset_counter]
            )  # loads manipulation pulses in triggersets
            # stores pulse name and triggerset number for later use
            self._manipulation_dict[pulse.name] = triggerset_counter
            if pulse.is_parametrized:
                # special pulse to end a parametrized manipulation pulse
                choke_pulse = Pulse(4e-09, amplitude=0)
                self._load_pulse(
                    choke_pulse, self.qic.manipulation.triggerset[14]
                )  # choke pulse uses triggerset 14
            triggerset_counter += 1

    def _configure_sequences(self):
        """overwrites the _configure_sequences method of BaseExperiment class.
        this function uses the already in triggersets loaded pulses to produce the pulse pattern of a predefined qkit
        PulseSequence Instance. For enabeling length zero parametrized pulses a second sequence without those
        parametrized pulses has to be loaded. Which Sequence is played by the sequencer will be determined after using
        the set_value method.
        """
        try:
            repetition_time = self.qic.sample.T_rep
        except AttributeError:
            repetition_time = 2e-6

        remember = False  # remember triggersets of last item if a fixed pulse is skipped and the next pulse is parallel with length 0
        # store the keyword of two different sequences and the sequencer command number at which they start.
        self._pc_dict: dict[str, int] = {}
        sequence_names = ["normal", "short", "zero"]  # names of the sequences
        code = SequencerCode(self._pc_dict)
        last_pulse = None  # will contain the last pulse.
        readout_set = 0  # storing readout, manipulation and recording triggerset
        manipulation_set = 0
        recording_set = 0
        for iteration_counter in range(self.iterations):
            # returns the number of the next sequencer command
            code.reference(sequence_names[iteration_counter])
            code.trigger_nco_sync()
            # loops through lists of pulses. every pulse in a list will be played at the same time.
            for item in self.sequence.sequence:
                # remember triggersets of the last item if item[-1] pulse has lenght zero
                if remember:
                    remember = False
                else:
                    readout_set = (
                        0  # storing readout, manipulation and recording triggerset
                    )
                    manipulation_set = 0
                    recording_set = 0
                for pulse in item:  # looping through item to set the triggersets
                    if pulse.type == PulseType.Readout:
                        readout_set = self._readout_dict[pulse.name]
                        recording_set = 1  # Normal recording
                    if pulse.type == PulseType.Pulse:
                        manipulation_set = self._manipulation_dict[pulse.name]
                if iteration_counter != 2 and last_pulse and last_pulse.is_parametrized:
                    # ending a parametrized readout by triggering another readout or choke pulse in the next iteration
                    if last_pulse.type == PulseType.Readout:
                        readout_set = readout_set or 14
                    elif last_pulse.type == PulseType.Pulse:
                        # ending a parametrized manipulation pulse by triggering another manipulation pulse
                        # or choke pulse in the next iteration
                        manipulation_set = manipulation_set or 14
                if item[-1].is_parametrized:
                    if (
                        iteration_counter == 0
                    ):  # trigger parametrized pulses and set delay_register later for sequence with length != 0
                        # for all parametrized pulses
                        code.trigger_registered(
                            register=self.delay_register[item[-1]],
                            readout=readout_set,
                            recording=recording_set,
                            manipulation=manipulation_set,
                        )
                    elif iteration_counter == 1:
                        # Pulse is one cycle long: Trigger without any delay
                        code.trigger(
                            readout=readout_set,
                            recording=recording_set,
                            manipulation=manipulation_set,
                        )
                    else:  # skip parametrized pulses for sequence where they have length zero
                        # if fixed parallel pulses are present the triggersets are stored
                        # and triggered in the next item.
                        if len(item) > 1:
                            remember = True
                        if item[-1].type == PulseType.Readout:
                            readout_set = 0
                        if item[-1].type == PulseType.Pulse:
                            manipulation_set = 0
                else:
                    code.trigger_immediate(
                        delay=item[-1].length(),
                        readout=readout_set,
                        recording=recording_set,
                        manipulation=manipulation_set,
                    )
                last_pulse = item[-1]
            # if the last pulse in the sequence is parametrized it will be ended.
            if (
                self.sequence.sequence[-1][-1].is_parametrized
                and iteration_counter != 2
            ):
                if self.sequence.sequence[-1][-1].type == PulseType.Pulse:
                    code.trigger(manipulation=14)
                if self.sequence.sequence[-1][-1].type == PulseType.Readout:
                    code.trigger(readout=14)
            if remember:
                code.trigger(
                    readout=readout_set,
                    recording=recording_set,
                    manipulation=manipulation_set,
                )
            code.end_of_experiment(repetition_time)
        self.qic.sequencer.load_program(code)

    def _load_pulse(self, pulse: Pulse, triggerset: TriggerSet):
        """loads qkit pulse() in the triggerset of the QiController

        :param pulse  Pulse
            the qkit Pulse() instance.
        :param triggerset: TriggerSet
            Instance of class TriggerSet of the Pulsegenerator.

        :raises Exception:
            if IQ_frequency is given. Thus it has to be modified in the pulse_generator
        :raises Exception:
            if given wait
        """

        if pulse.iq_frequency != 0:
            raise RuntimeError(
                "IQ frequency is modified in the pulse generator, thus your setting will be ignored"
            )
        if pulse.type == PulseType.Wait:
            raise RuntimeError("expected ptype=Pulse or Readout given wait")
        if pulse.is_parametrized:
            # parametrized pulses are hold till ended by another pulse, so no need to use correct length
            envelope = np.array([pulse.amplitude()] * 4)
            # loading with correct phase and holding the last value of the amplitude array.
            triggerset.load_pulse(envelope, phase=pulse.phase, hold=True)
        else:
            envelope = pulse(samplerate)
            if (
                len(envelope) % 4 != 0
            ):  # adds zeroes to the end of the pulse if it's not multiple of 4
                envelope = np.append(envelope, [0.0] * (4 - len(envelope) % 4))
            triggerset.load_pulse(envelope, phase=pulse.phase)

    def overwrite_variables(self, **variables: Any):
        """overwrites the values of the parametrized Pulse Variables if needed.
        Variables values can be array or a single values. But Dimensions need to match.

        If not used, the variables given to the VirtualAWG are used.

        :param variables:
            the variables used to parametrize the pulses of the sequence.

        :raises Exception:
            if Dimension of the variables do not match.
        :raises Exception:
            if no variables given.
        """
        if self.parametrized:
            if not variables:
                raise RuntimeError("no variables given")
            value_list = list(variables.values())
            for value in value_list:
                # checks if variables have different types by using XOR
                if isinstance(value, Iterable) ^ isinstance(value_list[0], Iterable):
                    raise RuntimeError(
                        "the size of the variable values have to be the same"
                    )
                # checks if variables have different length
                if isinstance(value_list[0], Sized) and len(value_list[0]) != len(
                    value
                ):
                    raise RuntimeError(
                        "the size of the variable values have to be the same"
                    )
            self.variables = variables
        else:  # ignores variables if sequence does not need them
            pass

    def _single_execution(
        self, value_dict: dict[str, float]
    ) -> dict[str, int | list[int]]:
        """sets delay registers and starting points for the sequencer

        :param value_dict:
            the variables used for describing the pulse.

        """
        delays = [0] * 29  # array containing register values. Index is registers number
        for pulse, register in self.delay_register.items():
            # wtr command needs 8ns
            delays[register - 1] = pulse.length(**value_dict)
        register_used = delays[: len(self.delay_register)]  # used registers
        # checks if registers are all zero or not zero
        if 0 < register_used.count(0) < len(self.delay_register):
            raise RuntimeError(
                "A variable pulse can not be length zero if another one is not length zero"
            )

        if delays[0] < 2e-09:
            return {"sequencer_start": self._pc_dict["zero"], "delay_registers": delays}
        elif delays[0] > 2e-09 and delays[0] < 6e-09:
            return {
                "sequencer_start": self._pc_dict["short"],
                "delay_registers": delays,
            }
        else:
            return {
                "sequencer_start": self._pc_dict["normal"],
                "delay_registers": delays,
            }

    def _record_internal(
        self,
    ) -> (
        list[tuple[float, float]]
        | list[tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]]
    ):
        """overwrites the record internal of the base class. This method plays the right sequence for given values for
        the variables.
        Note that Variables can be given as single value or array

        :return: If two recordings two amplitude and phase tuples are returned in an array. otherwise only one tuple.

        :raises Exception:
            If Keyword zero not found in _pc_dict
        """
        if self.variables and isinstance(
            next(iter(self.variables.values())), Iterable
        ):  # for arrays as variable values
            dict_list = []  # each element is a dictionary containing a single value of the given arrays
            for counter in range(len(next(iter(self.variables.values())))):
                single_value_dict = {
                    name: list(value_list)[counter]
                    for name, value_list in self.variables.items()
                }
                dict_list.append(single_value_dict)
            # calling recording method to loop over array
            return self._record_internal_1d(dict_list, "values", self._single_execution)
        elif not self.variables:  # for sequence containing only fixed pulses
            self.qic.sequencer.start_at(self._pc_dict.get("default", 0))
            return self._measure_amp_pha()
        else:  # for parametrized pulses but single variable value
            length = None
            for pulse, register in self.delay_register.items():
                # calculating pulse length
                length = pulse.length(**self.variables)
                # setting delay register.
                self.qic.sequencer.set_delay_register(register=register, delay=length)
            if length is not None and length < 2e-09:
                if "zero" not in self._pc_dict:
                    raise RuntimeError(
                        "your Sequence was not loaded properly. Keyword zero is not in _pc_dict"
                    )
                self.qic.sequencer.start_at(self._pc_dict.get("zero"))
            else:
                self.qic.sequencer.start_at(self._pc_dict.get("normal", 0))
            return self._measure_amp_pha()
