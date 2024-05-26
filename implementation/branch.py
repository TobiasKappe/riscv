from ouca.riscv.instruction import SBTypeRiscInstruction, RiscInstruction
from ouca.riscv.machine import RiscMachine


class BranchRiscInstruction(SBTypeRiscInstruction):
    OPCODE = 0b1100011

    def condition(self, machine):
        raise NotImplementedError

    def run(self, machine: RiscMachine) -> None:
        if self.condition(machine):
            machine.program_counter += self.offset.to_int()
        else:
            machine.program_counter += 4


@RiscInstruction.register_instruction('beq')
class BranchEqualRiscInstruction(BranchRiscInstruction):
    FUNCT3 = 0b000

    def condition(self, machine):
        return machine.read_register(self.rs1) == \
               machine.read_register(self.rs2)


@RiscInstruction.register_instruction('bge')
class BranchGreaterEqualRiscInstruction(BranchRiscInstruction):
    FUNCT3 = 0b101

    def condition(self, machine):
        return machine.read_register(self.rs1) >= \
               machine.read_register(self.rs2)


@RiscInstruction.register_instruction('blt')
class BranchLessThanRiscInstruction(BranchRiscInstruction):
    FUNCT3 = 0b100

    def condition(self, machine):
        return machine.read_register(self.rs1) < \
               machine.read_register(self.rs2)
