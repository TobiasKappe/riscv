from typing import Tuple

from multimethod import multimethod

from ouca.riscv.data import RiscInteger
from ouca.riscv.instruction import RiscInstruction
from ouca.riscv.machine import RiscMachine


@RiscInstruction.register_instruction('lw')
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


@RiscInstruction.register_instruction('sw')
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
