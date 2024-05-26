from multimethod import multimethod


class RiscIntegerException(Exception):
    pass


class RiscInteger:
    @multimethod
    def __init__(self, value: int, signed: bool = True):
        if signed and (value < -2**31 or value >= 2**31):
            raise RiscIntegerException(
                f'Value "{value}" out of range for a signed RISC integer'
            )
        elif not signed and (value < 0 or value >= 2**32):
            raise RiscIntegerException(
                f'Value "{value}" out of range for an unsigned RISC integer'
            )

        self.bits = []
        for _ in range(32):
            self.bits.append(value & 1 > 0)
            value = value >> 1

    @multimethod
    def __init__( # noqa
        self,
        pattern: list
    ):
        bits = []
        for value in pattern:
            if isinstance(value, bool):
                bits.append(value)
                continue
            elif isinstance(value, tuple) and len(value) == 2:
                if isinstance(value[0], int) and isinstance(value[1], int):
                    value, length = value
                    for i in range(length):
                        bits.append(value & 1 > 0)
                        value = value >> 1
                    continue
                elif (isinstance(value[0], RiscInteger) and
                      isinstance(value[1], int)):
                    value, length = value
                    bits += value.bits[:length]
                    continue
            elif (isinstance(value, list) and
                  all(isinstance(v, bool) for v in value)):
                bits += value
                continue

            raise RiscIntegerException(
                f'Cannot decode "{value}" as RISC integer part'
            )

        if len(bits) != 32:
            raise RiscIntegerException('Bitvector must be 32 bits long')

        self.bits = bits

    @property
    def sign_bit(self) -> bool:
        return self.bits[31]

    @multimethod
    def __add__(self, other: 'RiscInteger'):
        carry = False
        bits = []
        for i in range(32):
            bit = self.bits[i] ^ other.bits[i] ^ carry
            carry = self.bits[i] and other.bits[i] or \
                carry and (self.bits[i] ^ other.bits[i])
            bits.append(bit)

        return RiscInteger(bits)

    @multimethod
    def __add__(self, other: int) -> 'RiscInteger':  # noqa
        return self + RiscInteger(other)

    def __neg__(self) -> 'RiscInteger':
        return RiscInteger([not b for b in self.bits]) + RiscInteger(1)

    def __sub__(self, other: 'RiscInteger') -> 'RiscInteger':
        return self + (-other)

    def compare_unsigned(self, other: 'RiscInteger') -> bool:
        for i in reversed(range(32)):
            if self.bits[i] < other.bits[i]:
                return True
            elif self.bits[i] > other.bits[i]:
                return False

        return False

    @multimethod
    def __lt__(self, other: 'RiscInteger') -> bool:
        unsigned_comp = self.compare_unsigned(other)
        return unsigned_comp ^ self.sign_bit ^ other.sign_bit

    @multimethod
    def __lt__(self, other: int) -> bool: # noqa
        return self < RiscInteger(other)

    def __ge__(self, other) -> bool:
        return not (self < other)

    def to_int(self, signed=True):
        as_int = 0
        for i in range(31):
            if self.bits[i]:
                as_int += 2**i

        if self.sign_bit:
            if signed:
                as_int += -2**31
            else:
                as_int += 2**31

        return as_int

    def to_bitstring(self):
        return ''.join('1' if b else '0' for b in self.bits[::-1])

    def to_hex(self):
        return f'0x{self.to_int(False):08X}'

    def __str__(self):
        return str(self.to_int())

    def __repr__(self):
        return f'RiscInteger({self.to_int()})'

    def __rshift__(self, positions):
        if positions > 32:
            # Do not fill in too many zeroes
            positions = 32

        return RiscInteger(self.bits[positions:] + [False] * positions)

    def __lshift__(self, positions):
        if positions == 0:
            # Slicing self.bits[:0] is a special case
            return self
        elif positions > 32:
            # Do not fill in too many zeroes
            positions = 32

        return RiscInteger([False] * positions + self.bits[:-positions])

    def __or__(self, other):
        return RiscInteger([self.bits[i] or other.bits[i] for i in range(32)])

    def __and__(self, other):
        return RiscInteger([self.bits[i] and other.bits[i] for i in range(32)])

    def __eq__(self, other):
        return self.bits == other.bits

    def __hash__(self):
        return hash(tuple(self.bits))
