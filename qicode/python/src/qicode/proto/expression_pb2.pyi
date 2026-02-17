from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

from qicode.proto import cell_pb2 as _cell_pb2
from qicode.proto import types_pb2 as _types_pb2
from qicode.proto import variables_pb2 as _variables_pb2

DESCRIPTOR: _descriptor.FileDescriptor

class CellProperty(_message.Message):
    __slots__ = ("cell", "defaultValue", "name")
    CELL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFAULTVALUE_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    name: str
    defaultValue: Expression
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        name: str | None = ...,
        defaultValue: Expression | _Mapping | None = ...,
    ) -> None: ...

class Expression(_message.Message):
    __slots__ = (
        "binary",
        "indexed",
        "literal",
        "property",
        "typeCast",
        "unary",
        "variable",
    )
    class Binary(_message.Message):
        __slots__ = ("lhs", "op", "rhs")
        class Operator(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            Plus: _ClassVar[Expression.Binary.Operator]
            Minus: _ClassVar[Expression.Binary.Operator]
            Mult: _ClassVar[Expression.Binary.Operator]
            Div: _ClassVar[Expression.Binary.Operator]
            Lsh: _ClassVar[Expression.Binary.Operator]
            Rsh: _ClassVar[Expression.Binary.Operator]
            And: _ClassVar[Expression.Binary.Operator]
            Or: _ClassVar[Expression.Binary.Operator]
            Xor: _ClassVar[Expression.Binary.Operator]
            Lt: _ClassVar[Expression.Binary.Operator]
            Le: _ClassVar[Expression.Binary.Operator]
            Gt: _ClassVar[Expression.Binary.Operator]
            Ge: _ClassVar[Expression.Binary.Operator]
            Eq: _ClassVar[Expression.Binary.Operator]
            Ne: _ClassVar[Expression.Binary.Operator]

        Plus: Expression.Binary.Operator
        Minus: Expression.Binary.Operator
        Mult: Expression.Binary.Operator
        Div: Expression.Binary.Operator
        Lsh: Expression.Binary.Operator
        Rsh: Expression.Binary.Operator
        And: Expression.Binary.Operator
        Or: Expression.Binary.Operator
        Xor: Expression.Binary.Operator
        Lt: Expression.Binary.Operator
        Le: Expression.Binary.Operator
        Gt: Expression.Binary.Operator
        Ge: Expression.Binary.Operator
        Eq: Expression.Binary.Operator
        Ne: Expression.Binary.Operator
        LHS_FIELD_NUMBER: _ClassVar[int]
        OP_FIELD_NUMBER: _ClassVar[int]
        RHS_FIELD_NUMBER: _ClassVar[int]
        lhs: Expression
        op: Expression.Binary.Operator
        rhs: Expression
        def __init__(
            self,
            lhs: Expression | _Mapping | None = ...,
            op: Expression.Binary.Operator | str | None = ...,
            rhs: Expression | _Mapping | None = ...,
        ) -> None: ...

    class Unary(_message.Message):
        __slots__ = ("expr", "op")
        class Operator(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            Plus: _ClassVar[Expression.Unary.Operator]
            Minus: _ClassVar[Expression.Unary.Operator]
            Not: _ClassVar[Expression.Unary.Operator]

        Plus: Expression.Unary.Operator
        Minus: Expression.Unary.Operator
        Not: Expression.Unary.Operator
        EXPR_FIELD_NUMBER: _ClassVar[int]
        OP_FIELD_NUMBER: _ClassVar[int]
        expr: Expression
        op: Expression.Unary.Operator
        def __init__(
            self,
            expr: Expression | _Mapping | None = ...,
            op: Expression.Unary.Operator | str | None = ...,
        ) -> None: ...

    class Index(_message.Message):
        __slots__ = ("base", "value")
        BASE_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        base: Expression
        value: Expression
        def __init__(
            self,
            base: Expression | _Mapping | None = ...,
            value: Expression | _Mapping | None = ...,
        ) -> None: ...

    class TypeCast(_message.Message):
        __slots__ = ("expr", "targetType")
        EXPR_FIELD_NUMBER: _ClassVar[int]
        TARGETTYPE_FIELD_NUMBER: _ClassVar[int]
        expr: Expression
        targetType: _types_pb2.Type
        def __init__(
            self,
            expr: Expression | _Mapping | None = ...,
            targetType: _types_pb2.Type | _Mapping | None = ...,
        ) -> None: ...

    class Literal(_message.Message):
        __slots__ = ("arrayLiteral", "floatLiteral", "intLiteral")
        class Array(_message.Message):
            __slots__ = ("values",)
            VALUES_FIELD_NUMBER: _ClassVar[int]
            values: _containers.RepeatedCompositeFieldContainer[Expression.Literal]
            def __init__(
                self, values: _Iterable[Expression.Literal | _Mapping] | None = ...
            ) -> None: ...

        INTLITERAL_FIELD_NUMBER: _ClassVar[int]
        FLOATLITERAL_FIELD_NUMBER: _ClassVar[int]
        ARRAYLITERAL_FIELD_NUMBER: _ClassVar[int]
        intLiteral: int
        floatLiteral: float
        arrayLiteral: Expression.Literal.Array
        def __init__(
            self,
            intLiteral: int | None = ...,
            floatLiteral: float | None = ...,
            arrayLiteral: Expression.Literal.Array | _Mapping | None = ...,
        ) -> None: ...

    LITERAL_FIELD_NUMBER: _ClassVar[int]
    PROPERTY_FIELD_NUMBER: _ClassVar[int]
    VARIABLE_FIELD_NUMBER: _ClassVar[int]
    BINARY_FIELD_NUMBER: _ClassVar[int]
    UNARY_FIELD_NUMBER: _ClassVar[int]
    TYPECAST_FIELD_NUMBER: _ClassVar[int]
    INDEXED_FIELD_NUMBER: _ClassVar[int]
    literal: Expression.Literal
    property: CellProperty
    variable: _variables_pb2.Variable
    binary: Expression.Binary
    unary: Expression.Unary
    typeCast: Expression.TypeCast
    indexed: Expression.Index
    def __init__(
        self,
        literal: Expression.Literal | _Mapping | None = ...,
        property: CellProperty | _Mapping | None = ...,
        variable: _variables_pb2.Variable | _Mapping | None = ...,
        binary: Expression.Binary | _Mapping | None = ...,
        unary: Expression.Unary | _Mapping | None = ...,
        typeCast: Expression.TypeCast | _Mapping | None = ...,
        indexed: Expression.Index | _Mapping | None = ...,
    ) -> None: ...
