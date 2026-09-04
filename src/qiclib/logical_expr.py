"""
Creation of logical / boolean expressions using Python operators:

>>> from qiclib.logical_expr import LVar
>>> LVar("x0") & LVar("x1")
x0 & x1
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import ClassVar, Literal


class Lexpr(ABC):
    """
    Any logical expression.
    """

    @abstractmethod
    def variables(self) -> set[LVar]:
        """
        Set of variables that are part of this expression
        """

    @abstractmethod
    def eval(self, variables: dict[LVar, bool]) -> LConst:
        """
        Evaluate the expression given the set of variables
        """

    @abstractmethod
    def truth_table(self) -> TruthTable:
        """
        Returns the expression as truth table
        """

    @abstractmethod
    def bit_width(self) -> int:
        """
        Returns the bit-width of the result this expression produces
        """

    def __and__(self, rhs):
        return LBinary(self, _cast(rhs), "&")

    def __rand__(self, lhs):
        return LBinary(_cast(lhs), self, "&")

    def __or__(self, rhs):
        return LBinary(self, _cast(rhs), "|")

    def __ror__(self, lhs):
        return LBinary(_cast(lhs), self, "|")

    def __xor__(self, rhs):
        return LBinary(self, _cast(rhs), "^")

    def __rxor__(self, lhs):
        return LBinary(_cast(lhs), self, "^")

    def __invert__(self):
        return LUnary(self, "~")


def _combinational_product(bits: int) -> Iterator[tuple[bool, ...]]:
    """
    Return the combinational product for N bits in the same order that they would
    appear in the `TruthTable`
    >>> list(_combinational_product(2))
    [(False, False), (True, False), (False, True), (True, True)]
    """
    for row in itertools.product([False, True], repeat=bits):
        yield row[::-1]


@dataclass(frozen=True)
class TruthTable(Lexpr):
    """
    A Truth table encodes a logical expression as enumeration over all possible input combinations.

    :param l_vars:
        The variables on which the truth table operates
    :param elements:
        The result. The size must be 2 ** len(l_vars),
        and all elements must have the same bit-width.
    """

    l_vars: tuple[LVar, ...]
    elements: tuple[LConst, ...]

    def __post_init__(self):
        assert len(self.elements) == 2 ** len(self.l_vars), (
            f"A truth table over {len(self.l_vars)} variables needs "
            f"{2 ** len(self.l_vars)} elements, but {len(self.elements)} were given"
        )
        widths = {len(element) for element in self.elements}
        assert len(widths) == 1, (
            f"All elements must have the same bit-width, but got {sorted(widths)}"
        )

    def __getitem__(self, row) -> LConst:
        """
        get a result at a row in the truth table
        >>> from qiclib.logical_expr import LConst, LVar, TruthTable
        >>> t = TruthTable([LVar("din")], [LConst.FALSE, LConst.TRUE])
        >>> t[True]
        [True]
        >>> t[False]
        [False]
        """
        row_index = LConst.from_any(row, bit_width=len(self.l_vars))
        return self.elements[int(row_index)]

    def variables(self) -> set[LVar]:
        return set(self.l_vars)

    def eval(self, variables: dict[LVar, bool]) -> LConst:
        return self[tuple(variables[variable] for variable in self.l_vars)]

    def truth_table(self) -> TruthTable:
        return self

    def bit_width(self) -> int:
        return len(self.elements[0])

    def _with_inverted_results(self) -> TruthTable:
        """
        Helper that inverts all results. Used internally for the unary expression.
        """
        return TruthTable(
            l_vars=self.l_vars,
            elements=tuple(
                LConst.from_iterable(not element for element in result)
                for result in self.elements
            ),
        )

    def pretty_str(self) -> str:
        """Return the truth table in markdown format."""
        headers = [variable.name for variable in self.l_vars] + ["Result"]
        separator = ["---"] * len(headers)
        lines = [
            f"| {' | '.join(headers)} |",
            f"| {' | '.join(separator)} |",
        ]

        for row in _combinational_product(len(self.l_vars)):
            values = [str(value) for value in row] + [str(self[row])]
            lines.append(f"| {' | '.join(values)} |")

        return "\n".join(lines)

    def pretty_print(self):
        """Pretty-print the truth table in markdown format."""
        print(self.pretty_str())


def _cast(val) -> Lexpr:
    if isinstance(val, Lexpr):
        return val
    elif isinstance(val, bool):
        return LConst.from_bool(val)
    elif isinstance(val, int):
        raise ValueError(
            "int cannot be cast to a logical expression. Use 'LConst.from_int(value, bit_width)' instead"
        )
    raise AssertionError(f"Unknown value {val}")


@dataclass(frozen=True)
class LConst(Lexpr):
    values: tuple[bool, ...]

    TRUE: ClassVar[LConst]
    FALSE: ClassVar[LConst]

    def __getitem__(self, index) -> bool:
        return self.values[index]

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[bool]:
        return iter(self.values)

    def __int__(self) -> int:
        result = 0
        for i, v in enumerate(self.values):
            if v:
                result |= 1 << i
        return result

    def variables(self) -> set[LVar]:
        return set()

    def eval(self, variables: dict[LVar, bool]) -> LConst:
        return self

    def truth_table(self) -> TruthTable:
        return TruthTable((), (self,))

    def bit_width(self) -> int:
        return len(self)

    def __repr__(self):
        return str(list(self.values))

    @classmethod
    def from_int(cls, value: int, bit_width: int) -> LConst:
        if value >= 2**bit_width:
            raise ValueError(f"value {value} does not fit in {bit_width} bits")
        if value < 0:
            raise ValueError("value must be greater than zero")
        return cls(tuple(bool((value >> i) & 1) for i in range(bit_width)))

    @classmethod
    def from_bool(cls, value: bool) -> LConst:
        return cls((value,))

    @classmethod
    def from_any(cls, value: int | bool | Iterable[bool], **kwargs) -> LConst:
        if isinstance(value, bool):
            return cls.from_bool(value)
        if isinstance(value, int):
            return cls.from_int(value, kwargs["bit_width"])
        if isinstance(value, tuple):
            return cls(value)
        if isinstance(value, Iterable):
            return cls.from_iterable(value)
        raise AssertionError("from_any only takes int or bool")

    @classmethod
    def from_iterable(cls, iterable: Iterable[bool]) -> LConst:
        return LConst(tuple(iterable))

    @classmethod
    def of(cls, *values: bool) -> LConst:
        """
        Construct a constant from its bits, little-endian.

        >>> from qiclib.logical_expr import LConst
        >>> LConst.of(True, False, False) == LConst.from_int(0b001, 3)
        True
        """
        return cls(values)


LConst.TRUE = LConst.from_bool(True)
LConst.FALSE = LConst.from_bool(False)


@dataclass(frozen=True, eq=False)
class LVar(Lexpr):
    name: str

    def __repr__(self):
        return self.name

    def variables(self) -> set[LVar]:
        return {self}

    def eval(self, variables: dict[LVar, bool]) -> LConst:
        return LConst.from_bool(variables[self])

    def truth_table(self) -> TruthTable:
        return TruthTable((self,), (LConst.FALSE, LConst.TRUE))

    def bit_width(self) -> int:
        return 1


@dataclass(frozen=True)
class LVec(Lexpr):
    name: str
    bits: tuple[LVar, ...]

    @classmethod
    def from_iterable(cls, name: str, values: Iterable[LVar]):
        return cls(name, tuple(values))

    @classmethod
    def with_width(cls, name: str, bit_width: int):
        return cls.from_iterable(name, (LVar(f"{name}_{i}") for i in range(bit_width)))

    def __repr__(self):
        return self.name

    def __len__(self):
        return len(self.bits)

    def __iter__(self):
        return iter(self.bits)

    def variables(self) -> set[LVar]:
        return set(self.bits)

    def eval(self, variables: dict[LVar, bool]) -> LConst:
        return LConst.from_iterable(variables[var] for var in self)

    def truth_table(self) -> TruthTable:
        return TruthTable(
            self.bits,
            tuple(LConst(row) for row in _combinational_product(len(self))),
        )

    def __getitem__(self, index: int) -> LVar:
        return self.bits[index]

    def expr_eq(self, other: LVec | LConst | int) -> Lexpr:
        if isinstance(other, int):
            if not 0 <= other < 2 ** len(self):
                raise ValueError(
                    f"{other} does not fit into the {len(self)} bits of {self.name}"
                )
            _other = LConst.from_int(other, len(self))
        else:
            _other = other
        if len(_other) != len(self):
            raise ValueError(
                f"Cannot compare {len(self)} bits against {len(_other)} bits"
            )
        return all_true(*[~(lhs ^ rhs) for lhs, rhs in zip(self, _other, strict=True)])

    def expr_ne(self, other: LVec | LConst | int) -> Lexpr:
        return ~self.expr_eq(other)

    def when(
        self,
        cases: dict[int | LConst, Lexpr],
        default: Lexpr | None = None,
    ) -> Lexpr:
        normalized: dict[LConst, Lexpr] = {}
        for key, case in cases.items():
            value = LConst.from_int(key, len(self)) if isinstance(key, int) else key
            if value in normalized:
                raise ValueError(f"Duplicate case {value}")
            normalized[value] = case

        if default is None:
            assert len(normalized) == 2 ** len(self)
        else:
            assert len(normalized) <= 2 ** len(self)
            normalized = {
                value: normalized.get(value, default)
                for value in (
                    LConst.from_int(i, len(self)) for i in range(2 ** len(self))
                )
            }
        result: Lexpr = LConst.FALSE
        for value, case in normalized.items():
            selector: Lexpr = LConst.TRUE
            for bit, variable in enumerate(self):
                selector = selector & (variable if value[bit] else ~variable)
            result = result | (selector & _cast(case))
        return result

    def bit_width(self) -> int:
        return len(self)


_PRECEDENCE: dict[LUnaryOp | LBinaryOp, int] = {"|": 1, "^": 2, "&": 3, "~": 4}


def _operand_repr(operand: Lexpr, min_precedence: int) -> str:
    if isinstance(operand, (LUnary, LBinary)):
        if _PRECEDENCE[operand.op] < min_precedence:
            return f"({operand!r})"
    return repr(operand)


LUnaryOp = Literal["~"]


@dataclass(frozen=True)
class LUnary(Lexpr):
    value: Lexpr
    op: LUnaryOp

    def __repr__(self):
        return f"{self.op} {_operand_repr(self.value, _PRECEDENCE[self.op])}"

    def variables(self) -> set[LVar]:
        return self.value.variables()

    def eval(self, variables: dict[LVar, bool]) -> LConst:
        evaluated = self.value.eval(variables)
        match self.op:
            case "~":
                return LConst.from_iterable(not value for value in evaluated)
            case _:
                raise AssertionError(f"Unknown unary op {self.op}")

    def truth_table(self) -> TruthTable:
        assert self.op == "~"
        return self.value.truth_table()._with_inverted_results()

    def bit_width(self) -> int:
        return self.value.bit_width()


LBinaryOp = Literal["&", "|", "^"]


def _check_and_get_binary_width(op: LBinary):
    lhs_width = op.lhs.bit_width()
    rhs_width = op.rhs.bit_width()
    if lhs_width == 1:
        return rhs_width
    if rhs_width == 1:
        return lhs_width
    assert lhs_width == rhs_width, "Binary expression must have same widths"
    return lhs_width


@dataclass(frozen=True)
class LBinary(Lexpr):
    lhs: Lexpr
    rhs: Lexpr
    op: LBinaryOp

    def __post_init__(self):
        _check_and_get_binary_width(self)

    def __repr__(self):
        precedence = _PRECEDENCE[self.op]
        return (
            f"{_operand_repr(self.lhs, precedence)} {self.op} "
            f"{_operand_repr(self.rhs, precedence)}"
        )

    def variables(self) -> set[LVar]:
        return self.lhs.variables() | self.rhs.variables()

    def eval(self, variables: dict[LVar, bool]) -> LConst:
        lhs_evaluated: LConst = self.lhs.eval(variables)
        rhs_evaluated: LConst = self.rhs.eval(variables)
        # A single-bit operand is broadcast over the bits of a multi-bit one.
        if len(lhs_evaluated) == 1 and len(rhs_evaluated) != 1:
            lhs_evaluated = LConst.from_iterable(
                [lhs_evaluated[0]] * len(rhs_evaluated)
            )
        elif len(rhs_evaluated) == 1 and len(lhs_evaluated) != 1:
            rhs_evaluated = LConst.from_iterable(
                [rhs_evaluated[0]] * len(lhs_evaluated)
            )
        match self.op:
            case "&":
                return LConst.from_iterable(
                    lhs & rhs
                    for lhs, rhs in zip(lhs_evaluated, rhs_evaluated, strict=True)
                )
            case "|":
                return LConst.from_iterable(
                    lhs | rhs
                    for lhs, rhs in zip(lhs_evaluated, rhs_evaluated, strict=True)
                )
            case "^":
                return LConst.from_iterable(
                    lhs ^ rhs
                    for lhs, rhs in zip(lhs_evaluated, rhs_evaluated, strict=True)
                )
            case _:
                raise AssertionError(f"Unknown binary op {self.op}")

    def truth_table(self) -> TruthTable:
        # A set has no defined order, so sort to get a reproducible variable order.
        variables = sorted(self.variables(), key=lambda variable: variable.name)
        results = []
        for comb in _combinational_product(len(variables)):
            results.append(self.eval(dict(zip(variables, comb, strict=True))))
        return TruthTable(tuple(variables), tuple(results))

    def bit_width(self) -> int:
        return _check_and_get_binary_width(self)


def always(value: bool | int, bit_width: int | None = None) -> Lexpr:
    return LConst.from_any(value, bit_width=bit_width)


def iff(condition: Lexpr, then: Lexpr, else_then: Lexpr) -> Lexpr:
    return condition & then | ~condition & else_then


def all_same(*conditions: Lexpr) -> Lexpr:
    if not conditions:
        return always(True)

    result: Lexpr = always(True)
    reference = conditions[0]
    for condition in conditions[1:]:
        result = result & ~(reference ^ condition)
    return result


def all_true(*conditions: Lexpr) -> Lexpr:
    if not conditions:
        return always(True)

    result = conditions[0]
    for condition in conditions[1:]:
        result = result & condition
    return result
