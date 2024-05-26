from typing import Tuple, Dict

from multimethod import multimethod

from ouca.riscv.assembler import RiscAssembler, AssemblerException
from ouca.riscv.data import RiscInteger
from ouca.riscv.instruction import RiscInstruction
from ouca.riscv.machine import RiscMachine


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
