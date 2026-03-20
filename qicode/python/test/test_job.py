import pathlib
import tempfile
from io import BytesIO, StringIO

import pytest

from qicode import QiJob


def test_write_to_file_string():
    job = QiJob()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        job.serialize_to_file(tmp.name)
        assert tmp.read() == job.serialize()


def test_write_to_file_pathlib():
    job = QiJob()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = pathlib.Path(tmp.name)
        job.serialize_to_file(path)
        assert path.read_bytes() == job.serialize()


def test_write_to_file_bufferedio():
    job = QiJob()
    buffer = BytesIO()
    job.serialize_to_file(buffer)
    assert buffer.getvalue() == job.serialize()


def test_write_to_file_textio_raises_assertion_error():
    job = QiJob()
    textio = StringIO()
    with pytest.raises(AssertionError):
        job.serialize_to_file(textio)
