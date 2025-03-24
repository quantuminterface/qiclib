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
"""This module contains the base class for all QiController platform components.

All modules representing a part of the QiController should be derived from it. It also
includes automatic integration of the component into the Qkit framework.
"""

from __future__ import annotations

import abc
from typing import Any, ClassVar

from qiclib.packages.qkit_polyfill import QKIT_ENABLED, Instrument, qkit
from qiclib.packages.servicehub import Connection


class PlatformComponent(abc.ABC):
    """Base class for components on the QiController.

    All QiController platform components share a common constructor
    (`qiclib.hardware.platform_component.PlatformComponent`).

    The user does not create this class directly.
    Instead, existing instances of it can be accessed using the `qiclib.hardware.controller.QiController`
    and its properties.

    :param name:
        The name of the component as it will be referred to by the driver
    :param connection:
        The connection to the ServiceHub of the QiController
    :param controller:
        The QiController instance to which this component belongs
    :param qkit_instrument:
        If this component should be added to Qkit as instrument (if available),
        by default True
    """

    platform_attributes: ClassVar[set[str]] = set()
    """Set of all platform attributes in the component which are visible e.g. for Qkit.

    Using Qkit, they will be stored at the beginning of each measurement and appended
    to the measurement data (in the settings object).
    """

    def __init__(
        self,
        name: str,
        connection: Connection,
        controller,
        qkit_instrument=True,
    ):
        self._name = name
        self._qip = controller
        self._conn = connection

        # Create a virtual instrument to relay information for Qkit
        if qkit_instrument:
            self._qkit_proxy = QkitInstrumentProxy(self)

    @property
    def name(self):
        """Name of the Platform Component"""
        return self._name


class QkitInstrumentProxy(Instrument):
    """Class providing instrument parameters for Qkits settings object."""

    def __init__(self, component: PlatformComponent):
        self.component = component
        if QKIT_ENABLED:
            super().__init__(self.component.name, tags="PlatformComponent")
            try:
                qkit.instruments.add(self)
            except AttributeError:
                pass  # Qkit has not been started with qkit.start() so this fails
        self._params: dict[str, Any] = {}

    def get_parameters(self) -> dict:
        """Collects the parameters of the qkit_attributes

        :return:
            The parameters in a dictionary
        """
        self._params = {}
        for attribute_name in self.component.__class__.platform_attributes:
            self._params[attribute_name] = getattr(self.component, attribute_name)
        return self._params

    def get(self, parameter, query=True, **kwargs):
        """Gets a single parameter of parameter dictionary

        :param parameter: str
            The name of key of the parameter
        :param query: bool, optional
            if the value of the parameter should be fetched

        :return:
            the value of the parameter
        """
        if query:
            return getattr(self.component, parameter)
        else:
            return self._params[parameter]


attribute_set = set()
"""Global variable that collects platform attributes during class creation.

.. note::
    This variable should not be altered externally. Use the `platform_attribute` decorator
    for class properties and the `platform_attribute_collector` decorator for the classes
    themselves.
"""


def platform_attribute(func):
    """Decorator for class properties to indicate that these hold properties of the
    platform.

    The property name will be stored in the static :python:`platform_attributes` property of the
    class. It can be read by other frameworks, like Qkit, to determine which relevant
    platform properties exist and should be logged, stored, etc. for this platform
    component.

    Qkit, for example, will store the values of these attributes at the beginning of an
    experiment within the settings object of the data container.
    """
    attribute_set.add(func.__name__)
    return func


def platform_attribute_collector(class_):
    """Class decorator for platform components containing decorated platform attributes.

    This decorator adds the decorated platform attributes to the class set. During class
    creation, they will be collected in a global variable (as the class itself does not
    exist yet) and then copied into the static :python:`platform_attributes` class property.
    """
    attrs = set()
    attrs.update(attribute_set)
    class_.platform_attributes = attrs
    attribute_set.clear()
    return class_
