from __future__ import annotations

import io
import os
from collections.abc import Sequence
from itertools import count
from typing import TYPE_CHECKING

from google.protobuf.internal.containers import RepeatedCompositeFieldContainer

from qicode.proto.commands_pb2 import Command
from qicode.proto.job_pb2 import Job
from qicode.proto.variables_pb2 import Variable

if TYPE_CHECKING:
    from qicode.qi_cell import QiCell, QiCoupler


class QiJob:
    """
    Container holding program, cells and qi_result containers for execution of program.
    Builds the job with its properties

    :param skip_nco_sync:
        If the NCO synchronization at the beginning should be skipped

    :param nco_sync_length:
        How long to wait after the nco synchronization
    """

    _CURRENT_JOB: QiJob | None = None

    def __init__(self, skip_nco_sync: bool = False, nco_sync_length: int = 0) -> None:
        # Internal Job representation
        self._job = Job(skipNcoSync=skip_nco_sync, ncoSyncLength=nco_sync_length)
        # Used to store commands for context managers (i.e., If, Else, While, ...)
        self._context_stack: list[RepeatedCompositeFieldContainer[Command]] = []
        # Used to generate unique variable IDs. Defined here instead of at the QiVariable site
        # to start with 0 each time (enables reproducability and testability)
        self._var_id = count()

    def register_cells(self, cells: list[QiCell]):
        if len(self._job.cells) > 0:
            raise RuntimeError("Can only register one set of cells at a QiJob.")
        self._job.cells.extend(cell._proto() for cell in cells)

    def register_couplers(self, couplers: list[QiCoupler]):
        if len(self._job.cells) > 0:
            raise RuntimeError("Can only register one set of cells at a QiJob.")
        self._job.couplers.extend(coupler._proto() for coupler in couplers)

    def proto(self) -> Job:
        return self._job

    @staticmethod
    def _current() -> QiJob:
        if QiJob._CURRENT_JOB is None:
            raise RuntimeError("Can not use command outside QiJob context.")
        return QiJob._CURRENT_JOB

    def __enter__(self):
        QiJob._CURRENT_JOB = self
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        QiJob._CURRENT_JOB = None

    def _add_command(self, **kwargs) -> Command:
        if len(self._context_stack) == 0:
            return self._job.commands.add(**kwargs)
        else:
            return self._context_stack[-1].add(**kwargs)

    def _insertion_block(self) -> RepeatedCompositeFieldContainer:
        if len(self._context_stack) == 0:
            return self._job.commands
        else:
            return self._context_stack[-1]

    def _add_new_context(self, container: RepeatedCompositeFieldContainer):
        self._context_stack.append(container)

    def _close_context(self):
        return self._context_stack.pop()

    @property
    def commands(self) -> Sequence[Command]:
        return self._job.commands

    def request_variable(self) -> Variable:
        return Variable(id=next(self._var_id))

    def __str__(self) -> str:
        num_commands = len(self._job.commands)
        num_cells = len(self._job.cells)
        num_couplers = len(self._job.couplers)
        return f"QiJob(commands={num_commands}, cells={num_cells}, couplers={num_couplers}, skipNcoSync={self._job.skipNcoSync})"

    def serialize(self) -> bytes:
        return self.proto().SerializeToString()

    def serialize_to_file(self, file: str | os.PathLike | io.BufferedIOBase):
        if isinstance(file, io.BufferedIOBase):
            file.write(self.serialize())
        elif isinstance(file, io.TextIOBase):
            raise AssertionError("File must be opened in binary mode!")
        else:
            with open(file, "wb+") as outfile:
                outfile.write(self.serialize())

    @classmethod
    def deserialize(cls, data: bytes):
        job = cls()
        job._job = Job.FromString(data)
        return job

    @classmethod
    def deserialize_from_file(cls, file: str | os.PathLike | io.BufferedIOBase):
        if isinstance(file, io.BufferedIOBase):
            return cls.deserialize(file.read())
        elif isinstance(file, io.TextIOBase):
            raise AssertionError("File must be opened in binary mode!")
        else:
            with open(file, "rb") as infile:
                return cls.deserialize(infile.read())
