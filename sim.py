from multimethod import multimethod
from typing import List, Tuple, Dict

import re


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


class RiscMachine:
    def __init__(self, memory: dict = None, protected_registers={0}):
        self.registers = {i: RiscInteger(0) for i in range(32)}
        self.program_counter = 0
        self.memory = memory or {}
        self.protected_registers = protected_registers
        self.protected_registers_written = set()

    def write_register(self, index: int, value: int) -> None:
        if index in self.protected_registers:
            self.protected_registers_written |= {index}
            return

        if index < 0 or index > 31:
            raise Exception('Write to unknown register')

        self.registers[index] = value

    def read_register(self, index: int) -> int:
        if index < 0 or index > 31:
            raise Exception('Read from unknown register')

        return self.registers[index]

    def write_memory(self, address: int, value: int) -> None:
        if address.bits[0:2] != [False, False]:
            raise Exception('Unaligned memory write')

        self.memory[address.to_int()] = value

    def read_memory(self, address: int) -> int:
        if address.bits[0:2] != [False, False]:
            raise Exception('Unaligned memory read')

        return self.memory[address.to_int()]


class RiscInstruction:
    def run(self, machine: RiscMachine) -> None:
        raise NotImplementedError

    def assembly(self) -> str:
        raise NotImplementedError

    def encode(self) -> RiscInteger:
        raise NotImplementedError

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} "{self.assembly()}">'


class AssemblerException(Exception):
    pass


class RiscAssembler:
    INSTRUCTIONS = {}

    @staticmethod
    def parse_register(name: str) -> int:
        if name[0] == 'x':
            try:
                return int(name[1:])
            except ValueError:
                raise AssemblerException(f'Unknown register name: "{name}"')
        else:
            raise AssemblerException('Register names should start with "x"')

    @staticmethod
    def parse_immediate(immediate: str) -> RiscInteger:
        try:
            return RiscInteger(int(immediate))
        except ValueError:
            raise AssemblerException(
                f'Could not parse immediate: "{immediate}"'
            )

    @classmethod
    def register_instruction(cls, name):
        def wrapper(impl):
            cls.INSTRUCTIONS[name] = impl
            impl.mnemonic = name
            return impl
        return wrapper

    @classmethod
    def parse_line(
        cls,
        line: str,
        locations: Dict[str, RiscInteger],
        location: RiscInteger
    ) -> RiscInstruction:
        if not line.strip():
            return None

        locations = locations or {}

        try:
            instr, args = line.strip().split(' ', 1)
        except ValueError:
            raise AssemblerException(f'Could not parse line "{line}"')

        instr = instr.lower()
        if instr not in RiscAssembler.INSTRUCTIONS:
            raise AssemblerException(f'Unknown instruction "{instr}"')

        impl = cls.INSTRUCTIONS[instr]
        match = re.match(impl.FORMAT, args.strip())
        if match is None:
            raise AssemblerException(f'Could not parse instruction "{line}"')

        return impl(match.groups(), locations, location)

    @classmethod
    def parse(cls, lines: List[str]) -> List[RiscInstruction]:
        lines_without_labels = []
        locations = {}
        offset = 0
        for line in lines:
            # Remove comments started with "#", "//", or ";"
            match = re.match('([^;#/]*)(([;#]|//).*)?', line)
            line = match.group(1).strip()

            # Ignore empty lines
            if not line:
                continue

            if re.match('^[a-zA-Z_][a-zA-Z_0-9]*:$', line):
                # If it is a label, store it at the current offset
                locations[line[:-1]] = RiscInteger(offset)
            else:
                # Otherwise, remember the line and increment the offset
                lines_without_labels.append(line)
                offset += 4

        instructions = []
        for i, line in enumerate(lines_without_labels):
            instruction = RiscAssembler.parse_line(
                line,
                locations,
                RiscInteger(i * 4)
            )
            if not instruction:
                continue

            instructions.append(instruction)

        return instructions


@RiscAssembler.register_instruction('add')
class AddRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*([a-z0-9]+),\s*([a-z0-9]+)'

    @multimethod
    def __init__(self, rd: int, rs1: int, rs2: int):
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2

    @multimethod
    def __init__(self, parts: Tuple[str, str, str], *args): # noqa
        self.rd = RiscAssembler.parse_register(parts[0])
        self.rs1 = RiscAssembler.parse_register(parts[1])
        self.rs2 = RiscAssembler.parse_register(parts[2])

    def run(self, machine: RiscMachine) -> None:
        machine.write_register(
            self.rd,
            machine.read_register(self.rs1) +
            machine.read_register(self.rs2)
        )
        machine.program_counter += 4

    def assembly(self) -> str:
        return f'add x{self.rd}, x{self.rs1}, x{self.rs2}'

    def encode(self) -> RiscInteger:
        return RiscInteger([
            (0b0110011, 7),
            (self.rd, 5),
            (0b000, 3),
            (self.rs1, 5),
            (self.rs2, 5),
            (0b0000000, 7),
        ])


@RiscAssembler.register_instruction('addi')
class AddImmediateRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*([a-z0-9]+),\s*(-?[0-9]+)'

    @multimethod
    def __init__(self, rd: int, rs1: int, n: RiscInteger):
        self.rd = rd
        self.rs1 = rs1
        self.n = n

    @multimethod
    def __init__(self, parts: Tuple[str, str, str], *args): # noqa
        self.rd = RiscAssembler.parse_register(parts[0])
        self.rs1 = RiscAssembler.parse_register(parts[1])
        self.n = RiscAssembler.parse_immediate(parts[2])

    def run(self, machine: RiscMachine) -> None:
        machine.write_register(
            self.rd,
            machine.read_register(self.rs1) + self.n
        )
        machine.program_counter += 4

    def assembly(self) -> str:
        return f'addi x{self.rd}, x{self.rs1}, {self.n}'

    def encode(self) -> RiscInteger:
        return RiscInteger([
            (0b0010011, 7),
            (self.rd, 5),
            (0b000, 3),
            (self.rs1, 5),
            (self.n, 12),
        ])


class BranchRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*([a-z0-9]+),\s*([a-zA-Z_][a-zA-Z_0-9]*|-?[0-9]+)'

    @multimethod
    def __init__(self, rs1: int, rs2: int, offset: RiscInteger):
        self.rs1 = rs1
        self.rs2 = rs2
        self.offset = offset

    @multimethod
    def __init__( # noqa
        self,
        parts: Tuple[str, str, str],
        locations: Dict[str, RiscInteger],
        location: RiscInteger
    ):
        self.rs1 = RiscAssembler.parse_register(parts[0])
        self.rs2 = RiscAssembler.parse_register(parts[1])

        try:
            self.offset = RiscAssembler.parse_immediate(parts[2])
        except AssemblerException:
            try:
                self.offset = locations[parts[2]] - location
            except KeyError:
                raise AssemblerException(
                    f'Unable to resolve location "{parts[2]}"'
                )

    def condition(self, machine):
        raise NotImplementedError

    def run(self, machine: RiscMachine) -> None:
        if self.condition(machine):
            machine.program_counter += self.offset.to_int()
        else:
            machine.program_counter += 4

    def assembly(self) -> str:
        return f'{self.mnemonic} x{self.rs1}, x{self.rs2}, {self.offset}'

    def get_funct3(self):
        raise NotImplementedError

    def encode(self, swirl=True) -> RiscInteger:
        if swirl:
            return RiscInteger([
                (0b1100011, 7),
                self.offset.bits[11:12],
                self.offset.bits[1:5],
                (self.get_funct3(), 3),
                (self.rs1, 5),
                (self.rs2, 5),
                self.offset.bits[5:11],
                self.offset.bits[12:13],
            ])
        else:
            return RiscInteger([
                (0b1100011, 7),
                self.offset.bits[1:6],
                (self.get_funct3(), 3),
                (self.rs1, 5),
                (self.rs2, 5),
                self.offset.bits[6:13],
            ])


@RiscAssembler.register_instruction('beq')
class BranchEqualRiscInstruction(BranchRiscInstruction):
    def condition(self, machine):
        return machine.read_register(self.rs1) == \
               machine.read_register(self.rs2)

    def get_funct3(self):
        return 0b000


@RiscAssembler.register_instruction('bge')
class BranchGreaterEqualRiscInstruction(BranchRiscInstruction):
    def condition(self, machine):
        return machine.read_register(self.rs1) >= \
               machine.read_register(self.rs2)

    def get_funct3(self):
        return 0b101


@RiscAssembler.register_instruction('blt')
class BranchLessThanRiscInstruction(BranchRiscInstruction):
    def condition(self, machine):
        return machine.read_register(self.rs1) < \
               machine.read_register(self.rs2)

    def get_funct3(self):
        return 0b100


@RiscAssembler.register_instruction('lw')
class LoadWordRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*(-?[0-9]+)\(([a-z0-9]+)\)'

    @multimethod
    def __init__(self, rd: int, n: RiscInteger, rs1: int):
        self.rd = rd
        self.n = n
        self.rs1 = rs1

    @multimethod
    def __init__(self, parts: Tuple[str, str, str], *args): # noqa
        self.rd = RiscAssembler.parse_register(parts[0])
        self.n = RiscAssembler.parse_immediate(parts[1])
        self.rs1 = RiscAssembler.parse_register(parts[2])

    def run(self, machine: RiscMachine) -> None:
        machine.write_register(
            self.rd,
            machine.read_memory(machine.read_register(self.rs1) + self.n),
        )
        machine.program_counter += 4

    def assembly(self) -> str:
        return f'lw x{self.rd}, {self.n}(x{self.rs1})'

    def encode(self) -> RiscInteger:
        return RiscInteger([
            (0b0000011, 7),
            (self.rd, 5),
            (0b010, 3),
            (self.rs1, 5),
            (self.n, 12),
        ])


@RiscAssembler.register_instruction('sw')
class StoreWordRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*(-?[0-9]+)\(([a-z0-9]+)\)'

    @multimethod
    def __init__(self, rs2: int, n: RiscInteger, rs1: int):
        self.rs2 = rs2
        self.n = n
        self.rs1 = rs1

    @multimethod
    def __init__(self, parts: Tuple[str, str, str], *args): # noqa
        self.rs2 = RiscAssembler.parse_register(parts[0])
        self.n = RiscAssembler.parse_immediate(parts[1])
        self.rs1 = RiscAssembler.parse_register(parts[2])

    def run(self, machine: RiscMachine) -> None:
        machine.write_memory(
            machine.read_register(self.rs1) + self.n,
            machine.read_register(self.rs2),
        )
        machine.program_counter += 4

    def assembly(self) -> str:
        return f'sw x{self.rs2}, {self.n}(x{self.rs1})'

    def encode(self) -> RiscInteger:
        return RiscInteger([
            (0b0100011, 7),
            self.n.bits[0:5],
            (0b010, 3),
            (self.rs1, 5),
            (self.rs2, 5),
            self.n.bits[5:12],
        ])


class RiscSimulator:
    @multimethod
    def __init__(self, instructions: List[RiscInstruction], **kwargs):
        self.machine = RiscMachine(**kwargs)
        self.instructions = instructions

    @multimethod
    def __init__(self, instructions: List[str], **kwargs): # noqa
        self.machine = RiscMachine(**kwargs)
        self.instructions = RiscAssembler.parse(instructions)

    def simulate(self) -> None:
        while self.machine.program_counter < len(self.instructions) * 4:
            instruction = self.instructions[self.machine.program_counter >> 2]
            instruction.run(self.machine)
