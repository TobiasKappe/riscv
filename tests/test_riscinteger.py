import pytest

from ouca.riscv.data import RiscInteger, RiscIntegerException


class TestRiscInteger:
    @pytest.mark.parametrize(
        'number, signed, bits, pad',
        [
            (42, True, [False, True, False, True,
                        False, True], False),
            (1337, True, [True, False, False, True,
                          True, True, False, False,
                          True, False, True], False),
            (-13, True, [True, True, False, False], True),
            (2**31-1, True, [True]*31, False),
            (-2**31, True, [False]*31, True),
            (-1, True, [True]*31, True),
            (0, True, [False]*31, False),
            (2**32-1, False, [True]*32, None),
        ]
    )
    def test_constructor_int(self, number, signed, pad, bits):
        integer = RiscInteger(number, signed=signed)
        assert integer.bits == bits + [pad] * (32-len(bits))

    @pytest.mark.parametrize(
        'number, signed',
        [
            (-2**31-1, True),
            (-2**32, True),
            (2**31, True),
            (2**32, True),
            (-1, False),
            (2**32, False)
        ]
    )
    def test_constructor_int_range(self, number, signed):
        with pytest.raises(RiscIntegerException):
            RiscInteger(number, signed=signed)

    @pytest.mark.parametrize('pattern, bits, pad', [
        ([True]*32, [True]*32, None),
        ([False]*32, [False]*32, None),
        ([(RiscInteger(123), 32)], RiscInteger(123).bits, None),
        (
            [(0b101, 3), (0b111, 5), (RiscInteger(0b010), 3)] + [False]*21,
            [True, False, True, True,
             True, True, False, False,
             False, True, False],
            False,
        ),
    ])
    def test_constructor_bits(self, pattern, bits, pad):
        integer = RiscInteger(pattern)
        assert integer.bits == bits + [pad] * (32-len(bits))

    @pytest.mark.parametrize('pattern', [
        [123],
        [(RiscInteger(123), 'foo')],
        [(123, 'foo')],
        [('foo', 10)],
        [(123, 456, 789)],
        [[False, 'test']],
        [(0b0, 3), 123],
    ])
    def test_constructor_bits_types(self, pattern: list):
        with pytest.raises(RiscIntegerException) as exc:
            RiscInteger(pattern)

        assert 'Cannot decode' in str(exc)

    @pytest.mark.parametrize('pattern', [
        [True],
        [False]*33,
        [[False]*16, [True]*15],
        [(RiscInteger(0b101), 3)]*11,
        [(RiscInteger(0b0), 20), (123, 13)],
    ])
    def test_constructor_bits_length(self, pattern: list):
        with pytest.raises(RiscIntegerException) as exc:
            RiscInteger(pattern)

        assert 'must be 32 bits' in str(exc)

    @pytest.mark.parametrize(
        'number, sign',
        [
            (-1, True),
            (1, False),
            (2**31-1, False),
            (-2**31, True)
        ]
    )
    def test_sign_bit(self, number, sign):
        integer = RiscInteger(number)
        assert integer.sign_bit is sign

    @pytest.mark.parametrize(
        'a, b, c',
        [
            (1, 1, 2),
            (123, 456, 579),
            (5, -3, 2),
            (3, -5, -2),
            (2**31-1, 1, -2**31),   # overflow
            (-2**31, -1, 2**31-1),  # underflow
        ]
    )
    def test_add(self, a, b, c):
        a_integer = RiscInteger(a)
        b_integer = RiscInteger(b)
        c_integer = RiscInteger(c)

        assert a_integer + b_integer == c_integer

    @pytest.mark.parametrize(
        'a, b, c',
        [
            (1, 1, 0),
            (2, -3, 5),
            (123, 456, -333),
            (456, 123, 333),
            (-2**31, 1, 2**31-1),   # underflow
            (2**31-1, -1, -2**31),  # overflow
        ]
    )
    def test_sub(self, a, b, c):
        a_integer = RiscInteger(a)
        b_integer = RiscInteger(b)
        c_integer = RiscInteger(c)

        assert a_integer - b_integer == c_integer

    @pytest.mark.parametrize(
        'a, minus_a',
        [
            (0, 0),
            (1, -1),
            (-1, 1),
            (2**31-1, -2**31+1),
            (-2**31, -2**31),
        ]
    )
    def test_neg(self, a, minus_a):
        assert -RiscInteger(a) == RiscInteger(minus_a)

    @pytest.mark.parametrize(
        'bits, signed, as_int',
        [
            ([False]*32, True, 0),
            ([True]*32, True, -1),
            ([False]*31 + [True], True, -2**31),
            ([True]*31 + [False], True, 2**31-1),
            ([True]*32, False, 2**32-1),
        ]
    )
    def test_to_int(self, bits, signed, as_int):
        assert RiscInteger(bits).to_int(signed=signed) == as_int

    @pytest.mark.parametrize(
        'a, b, less_than',
        [
            (0, 1, True),
            (1, 0, False),
            (-1, 0, True),
            (0, -1, False),
            (123, 123, False),
            (-2**31, 2**31-1, True),
            (2**31-1, -2**31, False),
        ]
    )
    def test_compare(self, a, b, less_than):
        assert (RiscInteger(a) < RiscInteger(b)) is less_than

    @pytest.mark.parametrize(
        'bits, amount, outcome',
        [
            (0b0, 4, 0b00000),
            (0b101, 5, 0b10100000),
            (0b01010101010101010101010101010101, 32, 0b0),
            (0b01010101010101010101010101010101, 33, 0b0),
            (0b010, 0, 0b010),  # special case with slicing
        ]
    )
    def test_lshift(self, bits, amount, outcome):
        assert RiscInteger(bits) << amount == RiscInteger(outcome)

    @pytest.mark.parametrize(
        'bits, amount, outcome',
        [
            (0b0, 4, 0b0),
            (0b101, 5, 0b0),
            (0b1001, 2, 0b10),
            (0b10101, 0, 0b10101),
            (0b01010101010101010101010101010101, 32, 0b0),
            (0b01010101010101010101010101010101, 33, 0b0),
        ]
    )
    def test_rshift(self, bits, amount, outcome):
        assert RiscInteger(bits) >> amount == RiscInteger(outcome)

    @pytest.mark.parametrize(
        'a, b, c',
        [
            (0b1010, 0b0101, 0b1111),
            (0b1111, 0b1001, 0b1111),
            (0b0000, 0b0000, 0b0000),
        ]
    )
    def test_or(self, a, b, c):
        assert RiscInteger(a) | RiscInteger(b) == RiscInteger(c)

    @pytest.mark.parametrize(
        'a, b, c',
        [
            (0b1010, 0b0101, 0b0000),
            (0b1111, 0b1001, 0b1001),
            (0b0110, 0b0000, 0b0000),
            (0b0000, 0b0000, 0b0000),
        ]
    )
    def test_and(self, a, b, c):
        assert RiscInteger(a) & RiscInteger(b) == RiscInteger(c)
