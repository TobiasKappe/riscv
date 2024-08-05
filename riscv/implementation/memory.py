from typing import Tuple

from riscv.instruction import \
    ITypeRiscInstruction, STypeRiscInstruction, RiscInstruction
from riscv.machine import RiscMachine


@RiscInstruction.register_instruction('lw')
class LoadWordRiscInstruction(ITypeRiscInstruction):
    OPCODE = 0b0000011
    FUNCT3 = 0b10

    def parse_args(self, parts: Tuple[str, str, str], *args): # noqa
        self.rd = RiscInstruction.parse_register(parts[0])
        self.n = RiscInstruction.parse_immediate(parts[1])
        self.rs1 = RiscInstruction.parse_register(parts[2])

    def run(self, machine: RiscMachine) -> None:
        machine.write_register(
            self.rd,
            machine.read_memory(machine.read_register(self.rs1) + self.n),
        )
        machine.program_counter += 4

    def assembly(self) -> str:
        return f'{self.mnemonic} x{self.rd}, {self.n}(x{self.rs1})'


@RiscInstruction.register_instruction('sw')
class StoreWordRiscInstruction(STypeRiscInstruction):
    OPCODE = 0b0100011
    FUNCT3 = 0b010

    def parse_args(self, parts: Tuple[str, str, str], *args): # noqa
        self.rs2 = RiscInstruction.parse_register(parts[0])
        self.n = RiscInstruction.parse_immediate(parts[1])
        self.rs1 = RiscInstruction.parse_register(parts[2])

    def run(self, machine: RiscMachine) -> None:
        machine.write_memory(
            machine.read_register(self.rs1) + self.n,
            machine.read_register(self.rs2),
        )
        machine.program_counter += 4

    def assembly(self) -> str:
        return f'{self.mnemonic} x{self.rs2}, {self.n}(x{self.rs1})'
