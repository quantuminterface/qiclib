import sys

from qicode.proto.commands_pb2 import CallSite


def capture_callsite(skip: int = 2) -> CallSite:
    """
    Capture the caller's location.
    :param skip:
        How many records above the caller's frame to skip.
        Defaults to 2 to get the actual callsite.
    """
    if hasattr(sys, "_getframe"):
        frame = sys._getframe(skip)
        file = frame.f_code.co_filename
        line = frame.f_lineno
        return CallSite(file=file, line=line)
    else:
        # Unknown call site
        return CallSite()
