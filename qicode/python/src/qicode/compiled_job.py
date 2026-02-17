from pathlib import Path
from typing import Literal

from qicode.proto.compiled_job_pb2 import AssembledJob, BinaryJob


class CompiledJob:
    def __init__(self, job: AssembledJob | BinaryJob) -> None:
        self._job = job

    @classmethod
    def from_file(cls, path: Path, mode: Literal["binary", "assembly"]):
        with open(path, "rb") as infile:
            return cls.from_bytes(infile.read(), mode)

    @classmethod
    def from_bytes(cls, value: bytes, mode: Literal["binary", "assembly"]):
        if mode == "binary":
            job = BinaryJob()
            job.ParseFromString(value)
        elif mode == "assembly":
            job = AssembledJob()
            job.ParseFromString(value)
        else:
            raise AssertionError("Need 'assembly' or 'binary'")
        return cls(job)

    def proto(self) -> AssembledJob | BinaryJob:
        return self._job

    def __str__(self) -> str:
        if isinstance(self._job, BinaryJob):
            return (
                f"CompiledJob(binary, size={len(self._job.SerializeToString())} bytes)"
            )
        else:  # AssembledJob
            return f"CompiledJob(assembly, size={len(self._job.SerializeToString())} bytes)"
