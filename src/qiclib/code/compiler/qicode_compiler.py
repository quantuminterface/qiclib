"""
This module provides means to interact with the MLIR-based QiCode Compiler,
"""

import subprocess
import warnings
from collections.abc import Sequence
from subprocess import PIPE
from typing import Literal

from typing_extensions import Self

from qicode import CompiledJob, QiJob
from qicode.proto import CompiledJob as ProtoCompiledJob


class Compilation:
    """
    The result of a compilation.
    """

    def __init__(self, job: CompiledJob):
        self._job = job

    @classmethod
    def deserialize(cls, value: bytes) -> Self:
        """
        Deserialize the result from its proto description
        """
        return cls(CompiledJob.from_bytes(value))

    def binary(self) -> dict[int, Sequence[int]]:
        """
        Get the binary code.
        Note: `binary` and `assembly` are mutually exclusive.
        """
        cells = self._job.proto().cells
        return {cell.id: cell.code.binary.code for cell in cells}

    def assembly(self) -> dict[int, Sequence[str]]:
        """
        Get assembly code.
        Note: `binary` and `assembly` are mutually exclusive.
        """
        cells = self._job.proto().cells
        return {cell.id: cell.code.assembly.code for cell in cells}

    def proto(self) -> ProtoCompiledJob:
        """
        Returns the backing protocol buffer message.
        """
        return self._job.proto()

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
        return Compilation(compiled_job)
