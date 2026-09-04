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
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, ClassVar

import numpy as np

import qiclib.packages.constants as const
import qiclib.packages.utility as util
import qicode
from qiclib.code.qi_types import QiType, _TypeDefiningUse
from qiclib.code.qi_var_definitions import (
    QiExpression,
    QiVariableSet,
    _QiVariableBase,
)


class Shape(np.vectorize):
    """
    A vectorized function describing a possible shape
    defined on the standardized interval [0,1).
    """

    REGISTRY: ClassVar[dict[int, Shape]] = {}

    def __init__(
        self, name: str, ident: int, func: Callable[..., Any], *args: Any, **kwargs: Any
    ):
        self.name = name
        self._id = ident
        super().__init__(func, *args, **kwargs)
        Shape.REGISTRY[ident] = self

    def __mul__(self, other):
        return Shape(self.name, self._id, lambda x: self.pyfunc(x) * other.pyfunc(x))

    def __str__(self) -> str:
        return f"Shape({self.name})"

    def id(self) -> int:
        return self._id


class ShapeLibClass:
    """
    Object containing pre-defined pulse shapes.
    Currently implemented: rect, gauss
    """

    def __init__(self) -> None:
        self.zero = Shape("", 0, lambda x: 0)
        self.rect = Shape("rect", 1, lambda x: np.where(0 <= x < 1, 1, 0))
        self.gauss = (
            Shape(
                "gauss",
                0x8000,
                lambda x: np.exp(-0.5 * np.power((x - 0.5) / 0.166, 2.0)),
            )
            * self.rect
        )
        self.ramp = Shape("ramp", 0x8001, lambda x: x) * self.rect
        self.sqrfct = Shape("sqrfct", 0x8002, lambda x: x**2) * self.rect

        self.l_sphere: Shape = (
            Shape("l_sphere", 0x8003, lambda x: np.sqrt(1 - x**2)) * self.rect
        )
        self.r_sphere: Shape = (
            Shape("r_sphere", 0x8004, lambda x: np.sqrt(1 - (x - 1) ** 2)) * self.rect
        )
        self.gauss_up: Shape = (
            Shape(
                "gauss_up",
                0x8005,
                lambda x: np.exp(-0.5 * np.power((x - 1) / 2 / 0.166, 2.0)),
            )
            * self.rect
        )
        self.gauss_down: Shape = (
            Shape(
                "gauss_down",
                0x8006,
                lambda x: np.exp(-0.5 * np.power(x / 2 / 0.166, 2.0)),
            )
            * self.rect
        )


# Make ShapeLib a singleton:
ShapeLib = ShapeLibClass()

QiPulse = qicode.QiPulse


class _QiPulse:
    """
    Class to describe a single pulse.

    :param length: length of the pulse. This can also be a QiVariable for variable pulse lengths.
    :param shape: pulse shape (i.e. rect, gauss, ...)
    :param amplitude: relative amplitude of your pulse. This can also be a QiVariable for variable pulse amplitudes. NOT IMPLEMENTED
    :param phase: phase of the pulse in deg. (i.e. 90 for pulse around y-axis of the bloch sphere)
    :param frequency: Frequency of your pulse, which is loaded to the PulseGen
    """

    def __init__(
        self,
        length: float | QiExpression | str,
        shape: Shape | None = None,
        amplitude: float | _QiVariableBase | QiExpression | None = None,
        phase: float | QiExpression | None = None,
        frequency: float | QiExpression | None = None,
        hold=False,
    ):
        if isinstance(length, str):
            mode = length.lower()
            if mode not in ["cw", "off"]:
                raise ValueError("QiPulse with str length only accepts 'cw' or 'off'.")
            length = util.conv_cycles_to_time(1)
            if mode == "cw":
                hold = True
            else:
                amplitude = 0
        else:
            mode = "normal"

        self.mode = mode

        if shape is not None:
            self.shape = shape
        else:
            self.shape = ShapeLib.rect

        if amplitude is not None:
            self.amplitude = amplitude
        else:
            self.amplitude = 1.0

        if phase is not None:
            self.phase = phase
        else:
            self.phase = 0.0

        self.associated_variables = QiVariableSet()

        if isinstance(self.phase, QiExpression):
            self.phase._type_info.set_type(QiType.PHASE, _TypeDefiningUse.PULSE_PHASE)
            self.associated_variables.update(self.phase.contained_variables)
        self.frequency = (
            QiExpression._from(frequency) if frequency is not None else None
        )
        if self.frequency is not None:
            self.frequency._type_info.set_type(
                QiType.FREQUENCY, _TypeDefiningUse.PULSE_FREQUENCY
            )
            self.associated_variables.update(self.frequency.contained_variables)

        self._length = length

        self.hold = hold
        self.shift_phase = False

        if isinstance(self.amplitude, QiExpression):
            self.amplitude._type_info.set_type(
                QiType.AMPLITUDE, _TypeDefiningUse.PULSE_AMPLITUDE
            )
            self.associated_variables.update(self.amplitude.contained_variables)

        if isinstance(length, QiExpression):
            length._type_info.set_type(QiType.TIME, _TypeDefiningUse.PULSE_LENGTH)
            self.associated_variables.update(length.contained_variables)
            if length.is_dynamic() and self.shape != ShapeLib.rect:
                raise NotImplementedError(
                    "Variable pulse lengths are only supported for rectangular pulses"
                )
        elif isinstance(length, float) and util.conv_time_to_cycles(length) >= 2**32:
            raise RuntimeError(
                f"Pulse length exceeds possible wait time, cycles {util.conv_time_to_cycles(length)}"
            )

    @classmethod
    def cw(
        cls,
        amplitude: float | _QiVariableBase | QiExpression = 1.0,
        phase: float | QiExpression = 0.0,
        frequency: float | QiExpression | None = None,
    ) -> _QiPulse:
        """
        Generates a continuous wave pulse.
        :param amplitude: Amplitude of the pulse.
        :param phase: Phase of the pulse in deg. (i.e. 90 for pulse around y-axis of the bloch sphere)
        :param frequency: Frequency of your pulse, which is loaded to the PulseGen
        :return: QiPulse object
        """
        return cls("cw", ShapeLib.rect, amplitude, phase, frequency)

    @classmethod
    def off(cls) -> _QiPulse:
        """
        Turns a continuous wave pulse off.
        It is only sensible to use this pulse after using `QiPulse.cw()`.
        """
        return cls("off")

    def _are_variable_length(self, other: _QiPulse) -> bool:
        return self.is_variable_length and other.is_variable_length

    def _are_same_length(self, other: _QiPulse) -> bool:
        if isinstance(self._length, QiExpression):
            return self._length._equal_syntax(other._length)
        return self._length == other._length

    def _are_same_amplitude(self, other: _QiPulse) -> bool:
        if isinstance(self.amplitude, QiExpression):
            return self.amplitude._equal_syntax(other.amplitude)
        else:
            return self.amplitude == other.amplitude

    def _are_same_phase(self, other: _QiPulse) -> bool:
        if self.has_dynamic_phase and other.has_dynamic_phase:
            return True
        if self.has_dynamic_phase or other.has_dynamic_phase:
            # A pulse with a constant phase can still share the trigger set as long as
            # that phase is zero, because that is what a dynamic phase stores there.
            constant = other if self.has_dynamic_phase else self
            return _equal(constant.phase, 0.0)

        return _equal(self.phase, other.phase)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, _QiPulse):
            return False
        equal_length = self._are_variable_length(o) or self._are_same_length(o)
        equal_amplitude = self._are_same_amplitude(o)

        return (
            equal_length
            and equal_amplitude
            and (self.hold == o.hold)
            and (self.shape == o.shape)
            and (self.shift_phase == o.shift_phase)
            and self._are_same_phase(o)
            and (
                self.frequency._equal_syntax(o.frequency)
                if self.frequency is not None and o.frequency is not None
                else self.frequency is o.frequency
            )
        )

    def __call__(self, samplerate: float, **variables: Any) -> np.ndarray:
        """
        Returns the pulse envelope for a given frequency.
        :param samplerate: sample rate for calculating the envelope
        :param variables: the variables for the length/amplitude function, if any; legacy of qup_pulses

        :return: envelope of the pulse as numpy array.
        """
        from qiclib.code.qi_jobs import QiCellProperty

        length = (
            self._length() if isinstance(self._length, QiCellProperty) else self._length
        )

        if isinstance(length, QiExpression) and length.is_dynamic():
            # variable pulses are hold till ended by another pulse, so no need to use correct length
            return np.array([self.amplitude] * 4)

        if not isinstance(length, float | int):
            raise ValueError(
                f"spcified length must be a number (was {type(length).__name__})"
            )

        if (
            util.conv_time_to_cycles(length) >= 2**32
        ):  # check value again, QiCellproperty might be used
            raise RuntimeError(
                f"Pulse length exceeds possible wait time, cycles {util.conv_time_to_cycles(length)}"
            )

        if (
            isinstance(self.amplitude, QiExpression) and self.amplitude.is_dynamic()
        ):  # amplitude must be set to 1 for variable amplitude and take the value of self.amplitude otherwise
            amplitude = 1
        elif isinstance(self.amplitude, QiCellProperty):
            amplitude = self.amplitude()
        else:
            amplitude = self.amplitude

        timestep = 1.0 / samplerate

        if length < timestep / 2.0:
            if length != 0:
                logging.warning(
                    "A pulse is shorter than %f ns and thus is omitted.", length * 1e09
                )

            return np.zeros(0)

        time_fractions = np.arange(0, length, timestep) / length

        envelope = amplitude * self.shape(time_fractions)

        # Check if amplitude is too low and might vanish due to 16-bit quantization
        if self.mode != "off" and len(envelope) > 0:
            max_amplitude: float = np.max(np.abs(envelope))
            min_representable_amplitude = 1.0 / const.CONTROLLER_AMPLITUDE_MAX_VALUE
            # A pulse with 0 amplitude is fine and should not trigger a warning
            if max_amplitude > 0 and max_amplitude < min_representable_amplitude:
                import warnings

                warnings.warn(
                    f"Pulse amplitude ({max_amplitude:.2e}) is below the minimum representable value "
                    f"({min_representable_amplitude:.2e}) for 16-bit quantization and will vanish "
                    f"when converted to hardware format.",
                    UserWarning,
                )

        return envelope

    @property
    def length(self) -> QiExpression | float | str:
        return self._length

    @property
    def variables(self):
        return self.associated_variables

    @property
    def is_variable_length(self):
        return is_dynamic(self._length)

    @property
    def has_dynamic_phase(self) -> bool:
        return is_dynamic(self.phase)

    @property
    def trigger_set_phase(self) -> float:
        """The phase that is stored in the trigger set of the signal generator, in rad."""
        from .qi_var_definitions import QiCellProperty, _QiConstValue

        if self.has_dynamic_phase:
            return 0.0
        if isinstance(self.phase, _QiConstValue | QiCellProperty):
            return self.phase.float_value

        assert not isinstance(self.phase, QiExpression)
        return float(self.phase)

    def _stringify_args(self) -> str:
        """Determines non-default args to explicitly stringify"""
        arg_strings = []
        defaults = self.__init__.__defaults__

        if self.mode == "normal":
            arg_strings.append(str(self.length))
        else:
            arg_strings.append(f'"{self.mode}"')

        if self.shape != ShapeLib.rect:
            arg_strings.append(f"shape={self.shape}")
        if not _equal(self.amplitude, 1.0) and self.mode != "off":
            arg_strings.append(f"amplitude={self.amplitude}")
        if not _equal(self.phase, 0.0):
            arg_strings.append(f"phase={self.phase}")
        if not _equal(self.frequency, defaults[3]):
            arg_strings.append(f"frequency={self.frequency}")

        return ", ".join(arg_strings)

    def _stringify(self) -> str:
        return f"QiPulse({self._stringify_args()})"


def is_dynamic(prop) -> bool:
    return isinstance(prop, QiExpression) and prop.is_dynamic()


def _equal(a, b):
    """Helper function to compare QiPulse arguments.
    Because the arguments can be QiCellProperty, which is a QiExpression
    and therefore has an overloaded __eq__ function, we can not rely
    on the normal comparison operator.
    """
    from .qi_var_definitions import QiCellProperty, _QiConstValue

    if isinstance(a, QiExpression):
        if isinstance(a, int):
            return (
                isinstance(a, _QiConstValue)
                and a.type == QiType.NORMAL
                and a.value == b
            )
        elif isinstance(b, float):
            return (
                isinstance(a, _QiConstValue) and a.type == QiType.TIME and a.value == b
            )
        elif isinstance(b, QiCellProperty):
            return a._equal_syntax(b)
        else:
            return False
    else:
        return a == b
