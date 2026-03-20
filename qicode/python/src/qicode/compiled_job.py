from pathlib import Path

from qicode.proto.compiled_job_pb2 import CompiledJob as ProtoCompiledJob


class CompiledJob:
    def __init__(self, job: ProtoCompiledJob) -> None:
        self._job = job

    @classmethod
    def from_file(cls, path: Path):
        with open(path, "rb") as infile:
            return cls.from_bytes(infile.read())

    @classmethod
    def from_bytes(cls, value: bytes):
        job = ProtoCompiledJob.FromString(value)
        return cls(job)

    def proto(self) -> ProtoCompiledJob:
        return self._job

    def __str__(self) -> str:
        return f"CompiledJob(size={len(self._job.SerializeToString())} bytes)"
