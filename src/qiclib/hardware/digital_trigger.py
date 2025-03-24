# Copyright© 2024 Quantum Interface (quantuminterface@ipe.kit.edu)
# Lukas Scheller, IPE, Karlsruhe Institute of Technology
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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.digital_trigger_pb2 as proto
import qiclib.packages.grpc.digital_trigger_pb2_grpc as grpc_stub
import qiclib.packages.utility
from qiclib.hardware.platform_component import (
    PlatformComponent,
    platform_attribute_collector,
)

if TYPE_CHECKING:
    from qiclib import QiController
    from qiclib.packages.servicehub import Connection


@dataclass
class TriggerSet:
    """
    A trigger set defines everything that can be configured when triggering a digital trigger.
    """

    duration: float
    """
    How long (in seconds) to hold the output for
    """
    outputs: list[int]
    """
    The indices of the outputs to trigger
    """
    continuous: bool = False
    """
    whether the trigger should be held continuously.
    Only :python:`False` is supported at the moment.
    """


OutputLevel = Literal["active_low", "active_high"]


@dataclass
class OutputConfig:
    """
    Defines how individual outputs are configured.
    This option is static, i.e., it cannot be changed from within a :pythin:`QiJob`
    """

    level: OutputLevel
    """
    Whether the output should be actively low or actively high.
    Note that at the moment, only `active_high` is supported.
    """
    delay: float
    """
    How much time (in seconds) to wait before actually issuing the trigger.
    """


@platform_attribute_collector
class DigitalTrigger(PlatformComponent):
    def __init__(
        self,
        name: str,
        connection: Connection,
        controller: QiController,
        qkit_instrument: bool = True,
        index: int = 0,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._index = index
        self._stub = grpc_stub.DigitalTriggerServiceStub(self._conn.channel)
        self._trigger_sets: list[TriggerSet] = []

    def _endpoint_index(self):
        return dt.EndpointIndex(value=self._index)

    def _trigger_index(self, index: int):
        return proto.TriggerIndex(index=self._endpoint_index(), trigger=index)

    def _output_index(self, index: int):
        return proto.OutputIndex(index=self._endpoint_index(), output=index)

    def set_trigger_set(self, index: int, trig_set: TriggerSet):
        duration = qiclib.packages.utility.conv_time_to_cycles(trig_set.duration)
        self._stub.SetTriggerSet(
            proto.IndexedTriggerSet(
                index=self._trigger_index(index),
                set=proto.TriggerSet(
                    continuous=trig_set.continuous,
                    duration_cycles=duration,
                    output_select=trig_set.outputs,
                ),
            )
        )

    def get_trigger_set(self, index: int) -> TriggerSet:
        """
        Fetches one trigger set from the hardware module
        """
        trig_set = self._stub.GetTriggerSet(self._trigger_index(index))
        return TriggerSet(
            continuous=trig_set.continuous,
            duration=qiclib.packages.utility.conv_cycles_to_time(
                trig_set.duration_cycles
            ),
            outputs=trig_set.output_select,
        )

    def clear_trigger_sets(self):
        """
        Clear all trigger sets that are stored in the hardware module
        """
        self._stub.ClearTriggerSets(self._endpoint_index())
        self._trigger_sets.clear()

    def _set_output_config(self, output: int, config: OutputConfig):
        """
        This method is intentionally protected because changing the output level is not supported at the moment.
        """
        if config.level == "active_low":
            level = proto.OutputLevel.ACTIVE_LOW
        elif config.level == "active_high":
            level = proto.OutputLevel.ACTIVE_HIGH
        else:
            raise AttributeError(
                "Output level must either be 'active_low' or 'active_high'"
            )
        duration = qiclib.packages.utility.conv_time_to_cycles(config.delay)
        self._stub.SetOutputConfig(
            proto.IndexedOutputConfig(
                index=self._output_index(output),
                config=proto.OutputConfig(level=level, duration_cycles=duration),
            )
        )

    def set_delay(self, output: int, value: float):
        """
        Sets a static delay to a digital output.

        :param output: The output to add the delay to
        :param value: The amount of delay in seconds
        """
        self._set_output_config(output, OutputConfig(delay=value, level="active_high"))

    def get_output_config(self, output: int) -> OutputConfig:
        """
        Returns how the output at the given index is currently configured
        """
        config = self._stub.GetOutputConfig(self._output_index(output))
        if config.level == proto.OutputLevel.ACTIVE_LOW:
            level = "active_low"
        elif config.level == proto.OutputLevel.ACTIVE_HIGH:
            level = "active_high"
        else:
            raise RuntimeError(
                f"Internal error: output level should only be ACTIVE_LOW or ACTIVE_HIGH, but is {proto.OutputLevel}"
            )
        delay = qiclib.packages.utility.conv_cycles_to_time(config.duration_cycles)
        return OutputConfig(level=level, delay=delay)

    def reset(self):
        """
        Issues a reset.
        After this operation
        * All currently active triggers are reset
        * All trigger sets are invalidated
        * All output configs are reset
        """
        self._stub.Reset(self._endpoint_index())

    def trigger(self, idx: int):
        """
        Manually trigger a certain trigger set. This is mostly intended for debugging.
        """
        self._stub.Trigger(self._trigger_index(idx))
