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
import re

import pytest

import qiclib.packages.utility as util
from qiclib.code import Play, QiPhaseVariable, QiSample, QiTimeVariable
from qiclib.code.qi_jobs import (
    QiCells,
    QiJob,
)
from qiclib.code.qi_pulse import QiPulse, ShapeLib, _QiPulse
from qiclib.code.qi_types import QiType
from qiclib.code.qi_var_definitions import _QiVariableBase


@pytest.fixture
def job():
    with QiJob() as job:
        yield job


def test_shape_error(job):
    with pytest.raises(NotImplementedError):
        _QiPulse(length=_QiVariableBase(QiType.UNKNOWN), shape=ShapeLib.gauss)


def test_length_error(job):
    with pytest.raises(RuntimeError):
        _QiPulse(length=util.conv_cycles_to_time(2**32))


def test_state_var_error(job):
    with pytest.raises(TypeError):
        _QiPulse(length=_QiVariableBase(QiType.STATE))


def test_pulse_equal_variable_length(job):
    variable1 = _QiVariableBase(QiType.UNKNOWN)
    variable2 = _QiVariableBase(QiType.UNKNOWN)
    pulse1 = _QiPulse(length=variable1)
    pulse2 = _QiPulse(length=variable2)

    assert pulse1 == pulse2


def test_pulse_equal_length(job):
    pulse1 = _QiPulse(length=40e-9)
    pulse2 = _QiPulse(length=40e-9)

    assert pulse1 == pulse2


def test_pulse_not_equal_length(job):
    pulse1 = _QiPulse(length=40e-9)
    pulse2 = _QiPulse(length=41e-9)

    assert pulse1 != pulse2


def test_pulse_not_equal_length_variable(job):
    variable1 = _QiVariableBase(QiType.UNKNOWN)
    pulse1 = _QiPulse(length=variable1)
    pulse2 = _QiPulse(length=41e-9)

    assert pulse1 != pulse2


def test_get_pulse_length(job):
    pulse = _QiPulse(length=41e-9)

    assert pulse.length == 41e-9


def test_get_pulse_length_variable(job):
    variable = _QiVariableBase(QiType.UNKNOWN)
    pulse = _QiPulse(length=variable)

    length = pulse.length

    assert isinstance(length, _QiVariableBase)
    assert length.id, variable.id


def test_cw_pulse_initialization(job):
    pulse_cw = _QiPulse("cw", amplitude=0.5, frequency=66e6)

    assert pulse_cw.hold
    assert isinstance(pulse_cw.length, float)
    assert pulse_cw.length == util.conv_cycles_to_time(1)
    assert pulse_cw.amplitude == 0.5
    assert pulse_cw.frequency == 66e6

    pulse_off = _QiPulse("OFF")  # Case insensitive check (no exception raised)

    assert not pulse_off.hold
    assert isinstance(pulse_off.length, float)
    assert pulse_off.length == util.conv_cycles_to_time(1)
    assert pulse_off.amplitude == 0
    assert pulse_off.frequency is None


def test_invalid_length_str_at_init(job):
    with pytest.raises(
        ValueError,
        match=re.escape("QiPulse with str length only accepts 'cw' or 'off'."),
    ):
        _QiPulse("test")


def test_two_pulses_with_the_same_parameterized_length_are_same():
    sample = QiSample(1)
    sample[0]["pulse_len"] = 100e6
    with QiJob() as job:
        q = QiCells(1)
        Play(q[0], QiPulse(frequency=100e6, length=q[0]["pulse_len"]))
        Play(q[0], QiPulse(frequency=100e6, length=q[0]["pulse_len"]))

    assert len(job.cells[0].manipulation_pulses) == 1


def test_two_pulses_with_different_parameterized_length_are_different():
    sample = QiSample(1)
    sample[0]["pulse_len1"] = 100e-6
    sample[0]["pulse_len2"] = 200e-6
    with QiJob() as job:
        q = QiCells(1)
        v = QiTimeVariable()
        Play(q[0], QiPulse(frequency=100e6, length=q[0]["pulse_len1"]))
        Play(q[0], QiPulse(frequency=100e6, length=q[0]["pulse_len2"]))
        Play(q[0], QiPulse(frequency=100e6, length=v))
        Play(q[0], QiPulse(frequency=100e6, length=150e-6))

    assert len(job.cells[0].manipulation_pulses) == 4


# In theory, this should work. However, pulses are being stored and checked for equality before properties are resolved.
# Therefore, this is currently skipped.
@pytest.mark.skip(reason="Not implemented")
def test_two_pulses_with_parameterized_length_and_same_constant_are_same():
    sample = QiSample(1)
    sample[0]["pulse_len"] = 100e-6
    with QiJob() as job:
        q = QiCells(1)
        Play(q[0], QiPulse(frequency=100e6, length=q[0]["pulse_len"]))
        Play(q[0], QiPulse(frequency=100e6, length=100e-6))

    assert len(job.cells[0].manipulation_pulses) == 1


def test_pulses_with_different_constant_phases_are_different():
    with QiJob() as job:
        q = QiCells(1)
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=0.0))
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=1.0))

    assert len(job.cells[0].manipulation_pulses) == 2


def test_pulse_with_dynamic_phase_is_not_the_same_as_a_constant_phase():
    with QiJob() as job:
        q = QiCells(1)
        p = QiPhaseVariable()
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=1.0))
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=p))

    assert len(job.cells[0].manipulation_pulses) == 2


def test_pulses_only_differing_in_a_dynamic_phase_share_a_trigger_set():
    # A dynamic phase is applied by the phase register, the trigger set stores a phase
    # of zero for it -- just like for a pulse with a constant phase of zero.
    with QiJob() as job:
        q = QiCells(1)
        p = QiPhaseVariable()
        r = QiPhaseVariable()
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=0.0))
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=p))
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=r))

    assert len(job.cells[0].manipulation_pulses) == 1


def test_trigger_set_phase():
    with QiJob() as job:
        q = QiCells(1)
        p = QiPhaseVariable()
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=1.5))
        Play(q[0], QiPulse(frequency=100e6, length=100e-9, phase=p))

    pulses = job.cells[0].manipulation_pulses
    assert [pulse.has_dynamic_phase for pulse in pulses] == [False, True]
    assert [pulse.trigger_set_phase for pulse in pulses] == [1.5, 0.0]
