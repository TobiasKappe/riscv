import re
from multimethod import multimethod
from typing import List, Dict, Tuple

from ouca.riscv.machine import RiscMachine
from ouca.riscv.data import RiscInteger


class RiscInstructionException(BaseException):
    pass


class RiscParseException(BaseException):
    pass


class RiscInstruction:
    INSTRUCTIONS = {}

    @multimethod
    def __init__(self, code: RiscInteger, *args, **kwargs): # noqa
        if code[:7] != self.OPCODE:
            raise RiscInstructionException('Wrong opcode')

        self.decode(code, *args, **kwargs)

    @multimethod
    def __init__(self, parts: Tuple[str, str, str], *args): # noqa
        return self.parse_args(parts, *args)

    @multimethod
    def __init__(self, *args, **kwargs): # noqa
        return self.initialize(*args, **kwargs)

    def parse_args(self, parts, *args):
        raise NotImplementedError

    def run(self, machine: RiscMachine) -> None:
        raise NotImplementedError

    def assembly(self) -> str:
        raise NotImplementedError

    def decode(self, code: RiscInteger, *args, **kwargs):
        raise NotImplementedError

    def encode(self) -> RiscInteger:
        raise NotImplementedError

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} "{self.assembly()}">'

    @staticmethod
    def parse_register(name: str) -> int:
        if name[0] == 'x':
            try:
                return int(name[1:])
            except ValueError:
                raise RiscParseException(f'Unknown register name: "{name}"')
        else:
            raise RiscParseException('Register names should start with "x"')

    @staticmethod
    def parse_immediate(immediate: str) -> RiscInteger:
        try:
            return RiscInteger(int(immediate))
        except ValueError:
            raise RiscParseException(
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
    ) -> 'RiscInstruction':
        if not line.strip():
            return None

        locations = locations or {}

        try:
            instr, args = line.strip().split(' ', 1)
        except ValueError:
            raise RiscParseException(f'Could not parse line "{line}"')

        instr = instr.lower()
        if instr not in RiscInstruction.INSTRUCTIONS:
            raise RiscParseException(f'Unknown instruction "{instr}"')

        impl = cls.INSTRUCTIONS[instr]
        match = re.match(impl.FORMAT, args.strip())
        if match is None:
            raise RiscParseException(f'Could not parse instruction "{line}"')

        return impl(match.groups(), locations, location)

    @classmethod
    def parse(cls, lines: List[str]) -> List['RiscInstruction']:
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
            instruction = RiscInstruction.parse_line(
                line,
                locations,
                RiscInteger(i * 4)
            )
            if not instruction:
                continue

            instructions.append(instruction)

        return instructions


class RTypeRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*([a-z0-9]+),\s*([a-z0-9]+)'

    def initialize(self, rd: int, rs1: int, rs2: int):
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2

    def decode(self, code: RiscInteger): # noqa
        self.rd = code[7:12]

        if code[12:15] != self.FUNCT3:
            raise RiscInstructionException('Wrong funct3')

        self.rs1 = code[15:20]
        self.rs2 = code[20:25]

        if code[25:] != self.FUNCT7:
            raise RiscInstructionException('Wrong funct7')

    def parse_args(self, parts: Tuple[str, str, str], *args): # noqa
        self.rd = RiscInstruction.parse_register(parts[0])
        self.rs1 = RiscInstruction.parse_register(parts[1])
        self.rs2 = RiscInstruction.parse_register(parts[2])

    def assembly(self) -> str:
        return f'{self.mnemonic} x{self.rd}, x{self.rs1}, x{self.rs2}'

    def encode(self) -> RiscInteger:
        return RiscInteger([
            (self.OPCODE, 7),
            (self.rd, 5),
            (self.FUNCT3, 3),
            (self.rs1, 5),
            (self.rs2, 5),
            (self.FUNCT7, 7),
        ])


class ITypeRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*([a-z0-9]+),\s*(-?[0-9]+)'

    def initialize(self, rd: int, rs1: int, n: RiscInteger):
        self.rd = rd
        self.rs1 = rs1
        self.n = n

    def decode(self, code: RiscInteger): # noqa
        self.rd = code[7:12]

        if code[12:15] != self.FUNCT3:
            raise RiscInstructionException('Wrong funct3')

        self.rs1 = code[15:20]
        self.n = RiscInteger([
            code.bits[20:],
            code.bits[31:32] * 20
        ])

    def parse_args(self, parts: Tuple[str, str, str], *args): # noqa
        self.rd = RiscInstruction.parse_register(parts[0])
        self.rs1 = RiscInstruction.parse_register(parts[1])
        self.n = RiscInstruction.parse_immediate(parts[2])

    def assembly(self) -> str:
        return f'{self.mnemonic} x{self.rd}, x{self.rs1}, {self.n}'

    def encode(self) -> RiscInteger:
        return RiscInteger([
            (self.OPCODE, 7),
            (self.rd, 5),
            (self.FUNCT3, 3),
            (self.rs1, 5),
            (self.n, 12),
        ])


class SBTypeRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*([a-z0-9]+),\s*([a-zA-Z_][a-zA-Z_0-9]*|-?[0-9]+)'

    def initialize(self, rs1: int, rs2: int, offset: RiscInteger):
        self.rs1 = rs1
        self.rs2 = rs2
        self.offset = offset

    def decode(self, code: RiscInteger, swirl=True): # noqa
        if swirl:
            self.offset = RiscInteger([
                [False],
                code.bits[8:12],
                code.bits[25:31],
                code.bits[7:8],
                code.bits[31:] * 20,
            ])
        else:
            self.offset = RiscInteger([
                code[7:12],
                code[25:],
                code[31:] * 20
            ])

        if code[12:15] != self.FUNCT3:
            raise RiscInstructionException('Wrong funct3')

        self.rs1 = code[15:20]
        self.rs2 = code[20:25]

    def parse_args( # noqa
        self,
        parts: Tuple[str, str, str],
        locations: Dict[str, RiscInteger],
        location: RiscInteger,
        *args
    ):
        self.rs1 = RiscInstruction.parse_register(parts[0])
        self.rs2 = RiscInstruction.parse_register(parts[1])

        try:
            self.offset = RiscInstruction.parse_immediate(parts[2])
        except RiscParseException:
            try:
                self.offset = locations[parts[2]] - location
            except KeyError:
                raise RiscParseException(
                    f'Unable to resolve location "{parts[2]}"'
                )

    def assembly(self) -> str:
        return f'{self.mnemonic} x{self.rs1}, x{self.rs2}, {self.offset}'

    def encode(self, swirl=True) -> RiscInteger:
        if swirl:
            return RiscInteger([
                (self.OPCODE, 7),
                self.offset.bits[11:12],
                self.offset.bits[1:5],
                (self.FUNCT3, 3),
                (self.rs1, 5),
                (self.rs2, 5),
                self.offset.bits[5:11],
                self.offset.bits[12:13],
            ])
        else:
            return RiscInteger([
                (0b1100011, 7),
                self.offset.bits[1:6],
                (self.FUNCT3, 3),
                (self.rs1, 5),
                (self.rs2, 5),
                self.offset.bits[6:13],
            ])


class STypeRiscInstruction(RiscInstruction):
    FORMAT = r'([a-z0-9]+),\s*(-?[0-9]+)\(([a-z0-9]+)\)'

    def initialize(self, rs1: int, rs2: int, n: RiscInteger):
        self.rs1 = rs1
        self.rs2 = rs2
        self.n = n

    def decode(self, code: RiscInteger, swirl=True): # noqa
        self.n = RiscInteger([
            code.bits[7:12],
            code.bits[25:],
            code.bits[31:] * 20
        ])

        if code[12:15] != self.FUNCT3:
            raise RiscInstructionException('Wrong funct3')

        self.rs1 = code[15:20]
        self.rs2 = code[20:25]

    def encode(self) -> RiscInteger:
        return RiscInteger([
            (self.OPCODE, 7),
            self.n.bits[0:5],
            (self.FUNCT3, 3),
            (self.rs1, 5),
            (self.rs2, 5),
            self.n.bits[5:12],
        ])
