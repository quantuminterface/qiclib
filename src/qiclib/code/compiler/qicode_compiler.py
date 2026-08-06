"""
This module provides means to interact with the MLIR-based QiCode Compiler,
"""

import subprocess
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from subprocess import PIPE
from typing import Literal

from qicode import CompiledJob, QiJob
from qicode.proto import CompiledJob as ProtoCompiledJob
from qicode.proto import SampleablePulse


@dataclass
class Pulse:
    amplitude: int
    index: int
    length: int
    shape: int
    hold: bool
    phase: int
    shiftPhase: bool


class CellCompilation:
    def __init__(self, cell: ProtoCompiledJob.Cell):
        self._cell = cell

    def proto(self) -> ProtoCompiledJob.Cell:
        return self._cell

    @staticmethod
    def _map_pulses(input_pulses: Sequence[SampleablePulse]) -> list[Pulse]:
        return [
            Pulse(
                proto_pulse.amplitude,
                proto_pulse.index,
                proto_pulse.length,
                proto_pulse.shape,
                proto_pulse.hold,
                proto_pulse.phase,
                proto_pulse.shift_phase,
            )
            for proto_pulse in input_pulses
        ]

    def manipulation_pulses(self) -> list[Pulse]:
        return CellCompilation._map_pulses(self.proto().manipulation_pulses)

    def readout_pulses(self) -> list[Pulse]:
        return CellCompilation._map_pulses(self.proto().readout_pulses)

    def recordings(self) -> Sequence[str]:
        return [recording.bucket for recording in self.proto().recordings]


class AssemblyCellCompilation(CellCompilation):
    def assembly(self) -> Sequence[str]:
        return self._cell.code.assembly.code


class BinaryCellCompilation(CellCompilation):
    def binary(self) -> Sequence[int]:
        return self._cell.code.binary.code


class Compilation:
    """
    The result of a compilation.
    """

    def __init__(self, job: CompiledJob, output_mode: Literal["binary", "assembly"]):
        self._job = job
        self._output_mode = output_mode

    def proto(self) -> ProtoCompiledJob:
        """
        Returns the backing protocol buffer message.
        """
        return self._job.proto()

    def cells(self) -> Sequence[CellCompilation]:
        if self._output_mode == "binary":
            return list(map(BinaryCellCompilation, self.proto().cells))
        else:
            return list(map(AssemblyCellCompilation, self.proto().cells))

    def cell(self, at: int) -> CellCompilation:
        if self._output_mode == "binary":
            return BinaryCellCompilation(self.proto().cells[at])
        else:
            return AssemblyCellCompilation(self.proto().cells[at])

    @property
    def cell_count(self) -> int:
        """
        The number of cells in this compilation
        """
        return len(self.proto().cells)


class CompilationFailed(Exception):
    """
    Raised when the compilation failed.
    Includes user-facing error message and the errorcode
    which is the return code from the compiler's execution.
    """

    def __init__(self, errmsg: str, errcode: int):
        super().__init__(errmsg)
        self.errcode = errcode


def serialize_job(job: QiJob) -> bytes:
    """
    Serialize a QiJob to protocol buffers
    """
    return job.proto().SerializeToString()


def deserialize_result(result: bytes) -> CompiledJob:
    """
    Deserialize the result of a compilation
    """
    return CompiledJob.from_bytes(result)


def compile_serialized_job(
    executable: str, serialized: bytes, mode: Literal["binary", "assembly"]
) -> bytes:
    """
    Compile a serialized job to the serialized result.
    Raises CompilationFailed if any error occur.
    """
    proc = subprocess.Popen(
        [executable, mode],
        stdout=PIPE,
        stdin=PIPE,
        stderr=PIPE,
    )

    stdout, stderr = proc.communicate(input=serialized)
    # TODO: Error handling in this way is suboptimal
    if proc.returncode == 0:
        if stderr:
            warnings.warn(f"stderr not empty: {stderr.decode('utf-8')}")
    else:
        if stderr:
            raise CompilationFailed(
                f"stderr output: {stderr.decode('utf-8')}", proc.returncode
            )
        else:
            raise CompilationFailed("unknown reason", proc.returncode)
    return stdout


class QiCodeCompiler:
    """
    MLIR-based QiCode compiler
    """

    def __init__(self, executable: str | None = None) -> None:
        self._executable = executable if executable is not None else "qicode_compiler"

    def compile(
        self, job: QiJob, output_mode: Literal["binary", "assembly"] = "binary"
    ) -> Compilation:
        """
        Compile a job to either binary or assembly
        """
        serialized_job = serialize_job(job)
        serialized_result = compile_serialized_job(
            self._executable, serialized_job, output_mode
        )
        compiled_job = deserialize_result(serialized_result)
        return Compilation(compiled_job, output_mode)
