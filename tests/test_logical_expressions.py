import itertools
import textwrap
from collections.abc import Callable

import pytest

from qiclib.logical_expr import (
    LBinary,
    LBinaryOp,
    LConst,
    Lexpr,
    LUnary,
    LVar,
    LVec,
    TruthTable,
    all_same,
    all_true,
    always,
    iff,
)


def assert_evaluates_like(
    expression: Lexpr, variables: list[LVar], reference: Callable[..., bool]
):
    """
    Asserts that `expression` evaluates to `reference` for every possible
    assignment of `variables`.
    """
    for combination in itertools.product([False, True], repeat=len(variables)):
        environment = dict(zip(variables, combination, strict=True))
        assert expression.eval(environment) == LConst.from_bool(
            reference(*combination)
        ), f"{expression} evaluated at {combination}"


class TestOperators:
    def test_operators_build_logical_expressions(self):
        lhs, rhs = LVar("a"), LVar("b")
        assert lhs & rhs == LBinary(lhs, rhs, "&")
        assert lhs | rhs == LBinary(lhs, rhs, "|")
        assert lhs ^ rhs == LBinary(lhs, rhs, "^")
        assert ~lhs == LUnary(lhs, "~")

    def test_booleans_are_cast(self):
        a = LVar("a")
        assert a & True == LBinary(a, LConst.TRUE, "&")
        assert True & a == LBinary(LConst.TRUE, a, "&")

        assert a | True == LBinary(a, LConst.TRUE, "|")
        assert True | a == LBinary(LConst.TRUE, a, "|")

        assert a ^ True == LBinary(a, LConst.TRUE, "^")
        assert True ^ a == LBinary(LConst.TRUE, a, "^")

    def test_reflected_operators_keep_the_operand_order(self):
        a = LVar("a")
        assert (False ^ a).eval({a: True}) == LConst.TRUE
        assert (True & a).eval({a: True}) == LConst.TRUE
        assert (False | a).eval({a: False}) == LConst.FALSE

    def test_cast_rejects_unknown_values(self):
        a = LVar("a")
        with pytest.raises(AssertionError, match="Unknown value"):
            a ^ "foo"

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            (LConst.TRUE, "[True]"),
            (LConst.FALSE, "[False]"),
            (LVar("a"), "a"),
            (LVec.with_width("d", 2), "d"),
            (LConst.from_int(0b01, 2), "[True, False]"),
            (~LVar("a"), "~ a"),
            (~(LVar("a") & LVar("b")), "~ (a & b)"),
            (~~LVar("a"), "~ ~ a"),
            (LVar("a") & LVar("b") | LVar("c"), "a & b | c"),
        ],
    )
    def test_repr(self, expression: Lexpr, expected: str):
        assert repr(expression) == expected


NESTED_EXPRESSIONS: list[Callable[..., Lexpr]] = [
    lambda a, b, c: (a & b) | c,
    lambda a, b, c: a & (b | c),
    lambda a, b, c: (a | b) & c,
    lambda a, b, c: a | (b & c),
    lambda a, b, c: (a ^ b) & c,
    lambda a, b, c: a ^ (b & c),
    lambda a, b, c: (a & b) ^ c,
    lambda a, b, c: a & (b ^ c),
    lambda a, b, c: (a | b) ^ c,
    lambda a, b, c: a | (b ^ c),
    lambda a, b, c: (a ^ b) | c,
    lambda a, b, c: a ^ (b | c),
    lambda a, b, c: ~(a & b) | c,
    lambda a, b, c: ~a & (b | ~c),
    lambda a, b, c: ~(a | b) ^ ~(a & c),
    lambda a, b, c: (a & (b | c)) ^ (~a | (b & c)),
]


class TestReprPrecedence:
    @pytest.mark.parametrize(
        ("build", "expected"),
        [
            (lambda a, b, c: (a & b) | c, "a & b | c"),
            (lambda a, b, c: (a & b) ^ c, "a & b ^ c"),
            (lambda a, b, c: (a ^ b) | c, "a ^ b | c"),
            (lambda a, b, c: a | (b & c), "a | b & c"),
            (lambda a, b, c: ~a & b, "~ a & b"),
            (lambda a, b, c: ~a | ~b, "~ a | ~ b"),
            (lambda a, b, c: a & (b | c), "a & (b | c)"),
            (lambda a, b, c: a & (b ^ c), "a & (b ^ c)"),
            (lambda a, b, c: a ^ (b | c), "a ^ (b | c)"),
            (lambda a, b, c: (a | b) & c, "(a | b) & c"),
            (lambda a, b, c: (a | b) ^ c, "(a | b) ^ c"),
            (lambda a, b, c: (a ^ b) & c, "(a ^ b) & c"),
            (lambda a, b, c: ~(a | b), "~ (a | b)"),
            (lambda a, b, c: ~(a & b), "~ (a & b)"),
            (lambda a, b, c: ~~a, "~ ~ a"),
            (lambda a, b, c: ~(~a & b), "~ (~ a & b)"),
            (lambda a, b, c: (a & b) & c, "a & b & c"),
            (lambda a, b, c: a & (b & c), "a & b & c"),
        ],
    )
    def test_repr_parenthesizes_by_precedence(
        self, build: Callable[..., Lexpr], expected: str
    ):
        a, b, c = LVar("a"), LVar("b"), LVar("c")
        assert repr(build(a, b, c)) == expected

    def test_different_groupings_do_not_share_a_repr(self):
        a, b, c = LVar("a"), LVar("b"), LVar("c")
        assert repr((a & b) | c) != repr(a & (b | c))

    @pytest.mark.parametrize("build", NESTED_EXPRESSIONS)
    def test_repr_round_trips_through_python(self, build: Callable[..., Lexpr]):
        variables = [LVar("a"), LVar("b"), LVar("c")]
        expression = build(*variables)
        reparsed = eval(
            repr(expression), dict(zip([v.name for v in variables], variables))
        )
        assert_evaluates_like(
            reparsed,
            variables,
            lambda *values: expression.eval(dict(zip(variables, values, strict=True)))[
                0
            ],
        )


class TestEval:
    def test_const(self):
        assert LConst.TRUE.eval({}) == LConst.TRUE
        assert LConst.FALSE.eval({}) == LConst.FALSE

    def test_variable(self):
        variable = LVar("a")
        assert variable.eval({variable: True}) == LConst.TRUE
        assert variable.eval({variable: False}) == LConst.FALSE

    def test_variables_are_identified_by_object_not_by_name(self):
        assert LVar("a") != LVar("a")
        with pytest.raises(KeyError):
            LVar("a").eval({LVar("a"): True})

    def test_and(self):
        a, b = LVar("a"), LVar("b")
        expr: Lexpr = a & b
        assert expr.eval({a: True, b: True}) == LConst.TRUE
        assert expr.eval({a: True, b: False}) == LConst.FALSE
        assert expr.eval({a: False, b: True}) == LConst.FALSE
        assert expr.eval({a: False, b: False}) == LConst.FALSE

    def test_or(self):
        a, b = LVar("a"), LVar("b")
        expr = a | b
        assert expr.eval({a: True, b: True}) == LConst.TRUE
        assert expr.eval({a: True, b: False}) == LConst.TRUE
        assert expr.eval({a: False, b: True}) == LConst.TRUE
        assert expr.eval({a: False, b: False}) == LConst.FALSE

    def test_xor(self):
        a, b = LVar("a"), LVar("b")
        expr = a ^ b
        assert expr.eval({a: True, b: True}) == LConst.FALSE
        assert expr.eval({a: True, b: False}) == LConst.TRUE
        assert expr.eval({a: False, b: True}) == LConst.TRUE
        assert expr.eval({a: False, b: False}) == LConst.FALSE

    def test_not(self):
        a = LVar("a")
        expr = ~a
        assert expr.eval({a: True}) == LConst.FALSE
        assert expr.eval({a: False}) == LConst.TRUE

    def test_nested_expression(self):
        a, b, c = LVar("a"), LVar("b"), LVar("c")
        expression = (a & ~b) | (b ^ c)
        assert_evaluates_like(
            expression, [a, b, c], lambda a, b, c: (a and not b) or (b != c)
        )

    @pytest.mark.parametrize("op", ["&", "|", "^"])
    def test_single_bit_operand_is_broadcast(self, op: LBinaryOp):
        multi = LConst.from_int(0b101, 3)
        single_true = LConst.from_int(0b1, 1)
        expected = {
            "&": LConst.of(True, False, True),
            "|": LConst.of(True, True, True),
            "^": LConst.of(False, True, False),
        }[op]
        assert LBinary(multi, single_true, op).eval({}) == expected
        assert LBinary(single_true, multi, op).eval({}) == expected

    def test_mismatched_widths_are_rejected(self):
        with pytest.raises(
            AssertionError, match=r"Binary expression must have same widths"
        ):
            (LConst.from_int(0b01, 2) & LConst.from_int(0b001, 3)).eval({})

    def test_unknown_binary_op(self):
        with pytest.raises(AssertionError, match="Unknown binary op"):
            LBinary(
                LConst.TRUE,
                LConst.TRUE,
                "nand",  # ty: ignore[invalid-argument-type]
            ).eval({})

    def test_unknown_unary_op(self):
        with pytest.raises(AssertionError, match="Unknown unary op"):
            LUnary(LConst.TRUE, "!").eval({})  # ty: ignore[invalid-argument-type]


class TestVariables:
    def test_constants_have_no_variables(self):
        assert LConst.TRUE.variables() == set()
        assert LConst.from_int(0b11, 2).variables() == set()

    def test_variable_has_single_variable(self):
        variable = LVar("a")
        assert variable.variables() == {variable}

    def test_binary_variable(self):
        binary_variable = LVec.with_width("d", 3)
        assert binary_variable.variables() == {
            binary_variable[0],
            binary_variable[1],
            binary_variable[2],
        }

    def test_binary_expression_contains_variables_of_their_children(self):
        a, b = LVar("a"), LVar("b")
        assert (a & b).variables() == {a, b}
        assert (a & a).variables() == {a}
        assert (a & True).variables() == {a}

    def test_unary_contains_variables_of_their_child(self):
        a = LVar("a")
        assert (~a).variables() == {a}


class TestLBinaryConst:
    def test_bits_are_stored_little_endian(self):
        constant = LConst.from_int(0b110, 3)
        assert constant == LConst.of(False, True, True)
        assert constant[0] is False
        assert constant[2] is True

    def test_len_is_the_bit_count(self):
        assert len(LConst.from_int(0, 4)) == 4

    def test_eval_ignores_the_environment(self):
        assert LConst.from_int(0b01, 2).eval({}) == LConst.of(True, False)

    def test_value_wider_than_the_bit_count_is_denied(self):
        with pytest.raises(ValueError, match=r"value \d does not fit in \d bits"):
            LConst.from_int(0b111, 2)


class TestLBinaryVar:
    def test_construction_from_bit_count_names_the_bits(self):
        binary_variable = LVec.with_width("d", 3)
        assert [variable.name for variable in binary_variable] == ["d_0", "d_1", "d_2"]

    def test_construction_from_variable_list(self):
        variables = [LVar("x"), LVar("y")]
        binary_variable = LVec.from_iterable("d", variables)
        assert list(binary_variable) == variables

    def test_eval_returns_the_bits_in_order(self):
        binary_variable = LVec.with_width("d", 2)
        assert binary_variable.eval(
            {binary_variable[0]: True, binary_variable[1]: False}
        ) == LConst.of(True, False)

    def test_eq_against_an_integer(self):
        binary_variable = LVec.with_width("d", 2)
        expression = binary_variable.expr_eq(0b10)
        assert_evaluates_like(
            expression,
            list(binary_variable),
            lambda bit0, bit1: not bit0 and bit1,
        )

    def test_ne_is_the_inverse_of_eq(self):
        binary_variable = LVec.with_width("d", 2)
        expression = binary_variable.expr_ne(0b10)
        assert_evaluates_like(
            expression,
            list(binary_variable),
            lambda bit0, bit1: not (not bit0 and bit1),
        )

    def test_eq_against_a_binary_constant(self):
        binary_variable = LVec.with_width("d", 2)
        expression = binary_variable.expr_eq(LConst.from_int(0b01, 2))
        assert_evaluates_like(
            expression, list(binary_variable), lambda bit0, bit1: bit0 and not bit1
        )

    def test_eq_against_another_binary_variable(self):
        lhs, rhs = LVec.with_width("d", 2), LVec.with_width("e", 2)
        expression = lhs.expr_eq(rhs)
        for combination in itertools.product([False, True], repeat=4):
            expected = combination[:2] == combination[2:]
            assert expression.eval(
                dict(
                    zip([*lhs, *rhs], combination),
                )
            ) == LConst.from_bool(expected)

    def test_eq_against_a_value_that_does_not_fit(self):
        with pytest.raises(ValueError, match="does not fit into the 2 bits of d"):
            LVec.with_width("d", 2).expr_eq(4)

    def test_eq_against_a_negative_value(self):
        with pytest.raises(ValueError, match="does not fit into the 2 bits of d"):
            LVec.with_width("d", 2).expr_eq(-1)

    def test_eq_against_a_different_width(self):
        with pytest.raises(ValueError, match="Cannot compare 2 bits against 3 bits"):
            LVec.with_width("d", 2).expr_eq(LConst.from_int(0, 3))


class TestWhen:
    def test_all_cases_enumerated(self):
        binary_variable = LVec.with_width("d", 2)
        expression = binary_variable.when(
            {
                0b00: LConst.FALSE,
                0b01: LConst.TRUE,
                0b10: LConst.TRUE,
                0b11: LConst.FALSE,
            }
        )
        assert_evaluates_like(
            expression, list(binary_variable), lambda bit0, bit1: bit0 != bit1
        )

    def test_missing_cases_use_the_default(self):
        binary_variable = LVec.with_width("d", 2)
        expression = binary_variable.when(
            {0b01: LConst.TRUE},
            default=LConst.FALSE,
        )
        assert_evaluates_like(
            expression, list(binary_variable), lambda bit0, bit1: bit0 and not bit1
        )

    def test_cases_may_be_binary_constants(self):
        binary_variable = LVec.with_width("d", 2)
        expression = binary_variable.when(
            {LConst.from_int(0b01, 2): LConst.TRUE},
            default=LConst.FALSE,
        )
        assert_evaluates_like(
            expression, list(binary_variable), lambda bit0, bit1: bit0 and not bit1
        )

    def test_cases_may_select_multi_bit_results(self):
        selector = LVec.with_width("d", 2)
        state = LVec.with_width("st", 2)
        expression = selector.when(
            {
                0b01: LConst.from_int(0b10, 2),
                0b10: LConst.from_int(0b01, 2),
            },
            # Keep the previous state for the remaining cases.
            default=state,
        )
        environment = {
            selector[0]: True,
            selector[1]: False,
            state[0]: True,
            state[1]: True,
        }
        assert expression.eval(environment) == LConst.of(False, True)

        environment[selector[1]] = True  # 0b11 -> default
        assert expression.eval(environment) == LConst.of(True, True)

    def test_missing_default_requires_all_cases(self):
        binary_variable = LVec.with_width("d", 2)
        with pytest.raises(AssertionError):
            binary_variable.when({0b00: LConst.TRUE})

    def test_case_out_of_range(self):
        binary_variable = LVec.with_width("d", 2)
        with pytest.raises(ValueError, match="value 4 does not fit in 2 bits"):
            binary_variable.when(
                {4: LConst.TRUE},
                default=LConst.FALSE,
            )

    def test_duplicate_case(self):
        binary_variable = LVec.with_width("d", 2)
        with pytest.raises(ValueError, match="Duplicate case"):
            binary_variable.when(
                {
                    0b01: LConst.TRUE,
                    LConst.from_int(0b01, 2): LConst.FALSE,
                },
                default=LConst.FALSE,
            )


class TestTruthTable:
    def test_element_count_must_match_the_variable_count(self):
        with pytest.raises(AssertionError, match="needs 4 elements, but 2 were given"):
            TruthTable(
                (LVar("a"), LVar("b")),
                (LConst.FALSE, LConst.TRUE),
            )

    def test_elements_must_share_one_bit_width(self):
        with pytest.raises(AssertionError, match=r"same bit-width, but got \[1, 2\]"):
            TruthTable(
                (LVar("a"),),
                (LConst.FALSE, LConst.from_int(0b01, 2)),
            )

    def test_bit_width_is_the_width_of_the_elements(self):
        assert LVar("a").truth_table().bit_width() == 1
        assert (LVar("a") & LVar("b")).truth_table().bit_width() == 1
        assert LVec.with_width("d", 3).truth_table().bit_width() == 3
        assert LConst.from_int(0b01, 2).truth_table().bit_width() == 2

    def test_can_be_used_as_an_operand(self):
        a = LVar("a")
        expression = a.truth_table() & LVec.with_width("d", 2)
        assert expression.bit_width() == 2

    def test_indexing_a_single_variable(self):
        table = TruthTable((LVar("din"),), (LConst.FALSE, LConst.TRUE))
        # A single index does not have to be a tuple.
        assert table[False] == table[(False,)]
        assert {table[False][0], table[True][0]} == {False, True}

    def test_variables(self):
        a, b = LVar("a"), LVar("b")
        assert TruthTable((a, b), tuple([LConst.FALSE] * 4)).variables() == {a, b}

    def test_of_a_binary_variable_enumerates_all_bit_patterns(self):
        # The table of a binary variable is the identity: every row reports the bit
        # pattern that addresses it.
        binary_variable = LVec.with_width("d", 2)
        table = binary_variable.truth_table()
        assert table.variables() == {binary_variable[0], binary_variable[1]}
        assert table[True, True] == LConst.of(True, True)
        assert table[3] == LConst.of(True, True)
        assert table[True, False] == LConst.of(True, False)
        assert table[1] == LConst.of(True, False)
        assert table[False, True] == LConst.of(False, True)
        assert table[2] == LConst.of(False, True)
        assert table[False, False] == LConst.of(False, False)
        assert table[0] == LConst.of(False, False)

    def test_the_first_variable_is_the_least_significant_bit_of_the_row(self):
        binary_variable = LVec.with_width("d", 3)
        table = binary_variable.truth_table()
        for row in itertools.product([False, True], repeat=3):
            index = sum(bit << position for position, bit in enumerate(row))
            assert table[row] == table[index] == LConst(row)

    def test_truth_table_of_a_truth_table_is_itself(self):
        table = TruthTable((LVar("a"),), (LConst.FALSE, LConst.TRUE))
        assert table.truth_table() is table

    def test_constants_produce_a_table_without_variables(self):
        assert LConst.TRUE.truth_table()[()] == LConst.TRUE
        assert LConst.from_int(0b01, 2).truth_table()[()] == LConst.of(True, False)

    def test_negation_keeps_the_variables(self):
        variable = LVar("a")
        assert (~variable).truth_table().variables() == {variable}

    def test_negation_inverts_all_results(self):
        variable = LVar("a")
        table = variable.truth_table()
        assert table[True] == LConst.TRUE
        assert table[False] == LConst.FALSE
        inverted = (~variable).truth_table()
        assert inverted[True] == LConst.FALSE
        assert inverted[False] == LConst.TRUE

    def test_eval_matches_indexing(self):
        a, b = LVar("a"), LVar("b")
        table = (a & ~b).truth_table()
        for row in itertools.product([False, True], repeat=2):
            assert table.eval({a: row[0], b: row[1]}) == table[row]

    def test_pretty_print(self):
        a = LVar("a")
        assert a.truth_table().pretty_str() == textwrap.dedent("""\
                | a | Result |
                | --- | --- |
                | False | [False] |
                | True | [True] |""")

    def test_pretty_print_counts_up_with_the_first_variable_as_lowest_bit(self):
        a, b = LVar("a"), LVar("b")
        assert (a & ~b).truth_table().pretty_str() == textwrap.dedent("""\
                | a | b | Result |
                | --- | --- | --- |
                | False | False | [False] |
                | True | False | [True] |
                | False | True | [False] |
                | True | True | [False] |""")

    def test_lookup_returns_the_element_of_that_row(self):
        a, b = LVar("a"), LVar("b")
        # Asymmetric, so that swapping `a` and `b` would be caught.
        elements = (LConst.FALSE, LConst.TRUE, LConst.FALSE, LConst.FALSE)
        table = TruthTable((a, b), elements)
        assert [table[index] for index in range(4)] == list(elements)
        # Row 1 is `a` set and `b` clear, as `a` is the least significant bit.
        assert table[True, False] == LConst.TRUE

    @pytest.mark.parametrize("build", NESTED_EXPRESSIONS)
    def test_truth_table_agrees_with_eval(self, build: Callable[..., Lexpr]):
        variables = [LVar("a"), LVar("b"), LVar("c")]
        expression = build(*variables)
        table = expression.truth_table()
        for row in itertools.product([False, True], repeat=len(table.l_vars)):
            environment = dict(zip(table.l_vars, row, strict=True))
            assert table[row] == expression.eval(environment)


class TestHelpers:
    def test_always(self):
        assert always(True).eval({}) == LConst.TRUE
        assert always(False).eval({}) == LConst.FALSE

    def test_iff(self):
        condition, then, else_then = LVar("c"), LVar("t"), LVar("f")
        expression = iff(condition, then, else_then)
        assert_evaluates_like(
            expression,
            [condition, then, else_then],
            lambda c, t, f: t if c else f,
        )

    def test_all_true(self):
        a, b, c = LVar("a"), LVar("b"), LVar("c")
        assert_evaluates_like(
            all_true(a, b, c), [a, b, c], lambda a, b, c: a and b and c
        )

    def test_all_true_of_a_single_condition_is_that_condition(self):
        a = LVar("a")
        assert all_true(a) is a

    def test_all_true_without_conditions(self):
        assert all_true().eval({}) == LConst.TRUE

    def test_all_same(self):
        a, b, c = LVar("a"), LVar("b"), LVar("c")
        assert_evaluates_like(all_same(a, b, c), [a, b, c], lambda a, b, c: a == b == c)

    def test_all_same_of_a_single_condition_is_always_true(self):
        a = LVar("a")
        assert_evaluates_like(all_same(a), [a], lambda a: True)

    def test_all_same_without_conditions(self):
        assert all_same().eval({}) == LConst.TRUE


@pytest.mark.parametrize(
    ("l_val", "int_val"),
    (
        (LConst.FALSE, 0),
        (LConst.TRUE, 1),
        (LConst.from_int(3, 3), 3),
        (LConst.from_int(2361, 32), 2361),
    ),
)
def test_const_to_int_conversion(l_val, int_val):
    assert int(l_val) == int_val
