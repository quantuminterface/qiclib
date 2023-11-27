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
import logging
from typing import Union, Callable, Any
import numpy as np
import qiclib.packages.utility as util
from .qi_var_definitions import QiExpression, _QiVariableBase
from .qi_types import QiType, _TypeDefiningUse


class Shape(np.vectorize):
    """
    A vectorized function describing a possible shape
    defined on the standardized interval [0,1).
    """

    def __init__(
        self, name: str, func: Callable[[float], float], *args: Any, **kwargs: Any
    ):
        self.name = name
        super().__init__(func, *args, **kwargs)

    def __mul__(self, other):
        return Shape(self.name, lambda x: self.pyfunc(x) * other.pyfunc(x))

    def __str__(self) -> str:
        return f"Shape({self.name})"


class ShapeLibClass:
    """
    Object containing pre-defined pulse shapes.
    Currently implemented: rect, gauss
    """

    def __init__(self):
        self.zero = Shape("", lambda x: 0)
        self.rect = Shape("rect", lambda x: np.where(0 <= x < 1, 1, 0))
        self.gauss = (
            Shape("gauss", lambda x: np.exp(-0.5 * np.power((x - 0.5) / 0.166, 2.0)))
            * self.rect
        )
        self.ramp = Shape("ramp", lambda x: x) * self.rect
        self.sqrfct = Shape("sqrfct", lambda x: x**2) * self.rect

        self.l_sphere: Shape = (
            Shape("l_sphere", lambda x: np.sqrt(1 - x**2)) * self.rect
        )
        self.r_sphere: Shape = (
            Shape("r_sphere", lambda x: np.sqrt(1 - (x - 1) ** 2)) * self.rect
        )
        self.gauss_up: Shape = (
            Shape(
                "gauss_up", lambda x: np.exp(-0.5 * np.power((x - 1) / 2 / 0.166, 2.0))
            )
            * self.rect
        )
        self.gauss_down: Shape = (
            Shape("gauss_down", lambda x: np.exp(-0.5 * np.power(x / 2 / 0.166, 2.0)))
            * self.rect
        )


# Make ShapeLib a singleton:
ShapeLib = ShapeLibClass()


class QiPulse:
    """
    Class to describe a single pulse.

    :param length: length of the pulse. This can also be a QiVariable for variable pulse lengths.
    :param shape: pulse shape (i.e. rect, gauss, ...)
    :param amplitude: relative amplitude of your pulse. This can also be a QiVariable for variable pulse amplitudes. NOT IMPLEMENTED
    :param phase: phase of the pulse in deg. (i.e. 90 for pulse around y-axis of the bloch sphere)
    :param frequency: Frequency of your pulse, which is loaded to the PulseGen
    """

    Type = Union[float, _QiVariableBase]

    def __init__(
        self,
        length: Union[float, _QiVariableBase, str],
        shape: Shape = ShapeLib.rect,
        amplitude: Union[float, _QiVariableBase] = 1.0,
        phase: float = 0.0,
        frequency: Union[float, QiExpression, None] = None,
        hold=False,
    ):
        from .qi_jobs import QiCellProperty

        if isinstance(length, str):
            mode = length.lower()
            if not mode in ["cw", "off"]:
                raise ValueError("QiPulse with str length only accepts 'cw' or 'off'.")
            length = util.conv_cycles_to_time(1)
            if mode == "cw":
                hold = True
            else:
                amplitude = 0
        else:
            mode = "normal"

        self.mode = mode
        self.shape = shape
        self.amplitude = amplitude
        self.phase = phase
        self._length = length
        self.frequency = (
            QiExpression._from(frequency) if frequency is not None else None
        )
        self.hold = hold
        self.shift_phase = False

        if self.frequency is not None:
            self.frequency._type_info.set_type(
                QiType.FREQUENCY, _TypeDefiningUse.PULSE_FREQUENCY
            )

        self.var_dict = {}

        if isinstance(length, QiExpression):
            length._type_info.set_type(QiType.TIME, _TypeDefiningUse.PULSE_LENGTH)

        if isinstance(length, _QiVariableBase):
            self.var_dict["length"] = length
            if shape != ShapeLib.rect:
                raise NotImplementedError(
                    "Variable pulse lengths are only supported for rectangular pulses"
                )
        elif isinstance(length, QiCellProperty):
            pass
        elif util.conv_time_to_cycles(length) >= 2**32:
            raise RuntimeError(
                f"Pulse length exceeds possible wait time, cycles {util.conv_time_to_cycles(length)}"
            )

        if isinstance(amplitude, _QiVariableBase):
            raise NotImplementedError("Variable Amplitude not implemented yet")
            # self.var_dict["amplitude"] = amplitude

    def _are_variable_length(self, other) -> bool:
        return self.is_variable_length and other.is_variable_length

    def _are_same_length(self, other) -> bool:
        return (
            not isinstance(self._length, _QiVariableBase)
            and not isinstance(other._length, _QiVariableBase)
            and (self._length is other._length)
        )

    def _are_same_amplitude(self, other) -> bool:
        return (
            not isinstance(self.amplitude, _QiVariableBase)
            and not isinstance(other.amplitude, _QiVariableBase)
            and (self.amplitude == other.amplitude)
        )

    def __eq__(self, o: object) -> bool:
        equal_length: bool = isinstance(o, QiPulse) and (
            self._are_variable_length(o) or self._are_same_length(o)
        )
        equal_amplitude: bool = isinstance(o, QiPulse) and self._are_same_amplitude(o)

        return (
            isinstance(o, QiPulse)
            and equal_length
            and equal_amplitude
            and (self.hold == o.hold)
            and (self.shape == o.shape)
            and (self.phase == o.phase)
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
        from .qi_jobs import QiCellProperty

        if self.is_variable_length:
            # variable pulses are hold till ended by another pulse, so no need to use correct length
            return np.array([self.amplitude] * 4)

        length = (
            self._length() if isinstance(self._length, QiCellProperty) else self._length
        )

        if (
            util.conv_time_to_cycles(length) >= 2**32
        ):  # check value again, QiCellproperty might be used
            raise RuntimeError(
                f"Pulse length exceeds possible wait time, cycles {util.conv_time_to_cycles(length)}"
            )

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

        return envelope

    @property
    def length(self):
        return self.var_dict.get("length", self._length)

    @property
    def variables(self):
        return list(self.var_dict.values())

    @property
    def is_variable_length(self):
        return isinstance(self._length, _QiVariableBase)

    def _stringify_args(self) -> str:
        """Determines non-default args to explicitly stringify"""
        arg_strings = []
        defaults = self.__init__.__defaults__

        if self.mode == "normal":
            arg_strings.append(str(self.length))
        else:
            arg_strings.append(f'"{self.mode}"')

        if self.shape != defaults[0]:
            arg_strings.append(f"shape={self.shape}")
        if not _equal(self.amplitude, defaults[1]) and self.mode != "off":
            arg_strings.append(f"amplitude={self.amplitude}")
        if not _equal(self.phase, defaults[2]):
            arg_strings.append(f"phase={self.phase}")
        if not _equal(self.frequency, defaults[3]):
            arg_strings.append(f"frequency={self.frequency}")

        return ", ".join(arg_strings)

    def _stringify(self) -> str:
        return f"QiPulse({self._stringify_args()})"


def _equal(a, b):
    """Helper function to compare QiPulse arguments.
    Because the arguments can be QiCellProperty, which is a QiExpression
    and therefore has an overloaded __eq__ function, we can not rely
    on the normal comparison operator.
    """
    from .qi_var_definitions import _QiConstValue, QiCellProperty

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
