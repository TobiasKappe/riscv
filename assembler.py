import re
from typing import List, Dict

from ouca.riscv.data import RiscInteger
from ouca.riscv.instruction import RiscInstruction


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
