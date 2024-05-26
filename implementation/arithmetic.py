from typing import Tuple

from multimethod import multimethod

from ouca.riscv.assembler import RiscAssembler
from ouca.riscv.data import RiscInteger
from ouca.riscv.instruction import RiscInstruction
from ouca.riscv.machine import RiscMachine


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
