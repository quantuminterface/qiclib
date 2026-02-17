from __future__ import annotations

from typing import Any

from qicode.proto.types_pb2 import Type


class QiArrayType:
    def __init__(self, type: Type.Array) -> None:
        self._type = type

    @property
    def len(self) -> int | None:
        if self._type.HasField("length"):
            return self._type.length
        else:
            return None

    @property
    def element_type(self) -> QiType:
        return QiType(self._type.type)

    def matches(self, other: QiType) -> bool:
        if (other_as_array := other.as_array()) is None:
            return False

        if self.len is not None and other_as_array.len is not None:
            if self.len != other_as_array.len:
                return False

        # One length is not defined => match purely on type.
        return other_as_array.element_type.matches(self.element_type)

    def __str__(self) -> str:
        length_str = str(self.len) if self.len is not None else "?"
        return f"Array[{self.element_type}, {length_str}]"


class QiType:
    def __init__(self, _type: Type) -> None:
        self._type = _type

    @staticmethod
    def from_any(value: Any) -> QiType:
        if value is int:
            return QiType.NORMAL
        if isinstance(value, QiType):
            return value
        raise TypeError(
            f"value {value} of type {value.__class__.__name__} cannot be converted to a Type"
        )

    def _proto(self) -> Type:
        return self._type

    TIME: QiType
    STATE: QiType
    NORMAL: QiType
    FREQUENCY: QiType
    PHASE: QiType
    AMPLITUDE: QiType
    UNKNOWN: QiType

    @classmethod
    def ARRAY(cls, element_type: QiType, length: None | int = None) -> QiType:
        return cls(
            Type(
                array=Type.Array(
                    type=element_type._proto(),
                    length=length,
                )
            )
        )

    def as_array(self) -> QiArrayType | None:
        if self._type.HasField("array"):
            return QiArrayType(self._type.array)
        else:
            return None

    def is_array(self) -> bool:
        return self._type.HasField("array")

    def is_unknown(self) -> bool:
        if self._type.HasField("unknown"):
            return True
        elif self._type.HasField("scalar"):
            return False
        else:
            assert self._type.HasField("array")
            return QiArrayType(self._type.array).element_type.is_unknown()

    def is_scalar(self) -> bool:
        return self._type.HasField("scalar")

    def __str__(self) -> str:
        if self._type.HasField("scalar"):
            return {
                Type.Scalar.Time: "TIME",
                Type.Scalar.State: "STATE",
                Type.Scalar.Normal: "NORMAL",
                Type.Scalar.Frequency: "FREQUENCY",
                Type.Scalar.Phase: "PHASE",
                Type.Scalar.Amplitude: "AMPLITUDE",
            }[self._type.scalar]
        elif self._type.HasField("unknown"):
            return "UNKNOWN"
        else:
            assert self._type.HasField("array")
            arr = self._type.array
            if arr.HasField("length"):
                length_str = str(arr.length)
            else:
                length_str = "?"
            return f"Array[{QiType(arr.type)}, {length_str}]"

    def __eq__(self, value: object) -> bool:
        return isinstance(value, QiType) and self._type == value._type

    def matches(self, other: QiType) -> bool:
        if other.is_scalar() or other.is_unknown():
            return other == self
        else:
            other_arr = other.as_array()
            assert other_arr is not None
            return other_arr.matches(self)

    def __hash__(self) -> int:
        if self._type.HasField("scalar"):
            return hash(("s", self._type.scalar))
        elif self._type.HasField("unknown"):
            return hash("u")
        else:
            assert self._type.HasField("array")
            return hash(("a", QiType(self._type.array.type), self._type.array.length))


QiType.TIME = QiType(Type(scalar=Type.Scalar.Time))
QiType.STATE = QiType(Type(scalar=Type.Scalar.State))
QiType.NORMAL = QiType(Type(scalar=Type.Scalar.Normal))
QiType.FREQUENCY = QiType(Type(scalar=Type.Scalar.Frequency))
QiType.PHASE = QiType(Type(scalar=Type.Scalar.Phase))
QiType.AMPLITUDE = QiType(Type(scalar=Type.Scalar.Amplitude))
QiType.UNKNOWN = QiType(Type(unknown=Type.Unknown()))
