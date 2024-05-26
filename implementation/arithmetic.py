from ouca.riscv.instruction import \
    ITypeRiscInstruction, RTypeRiscInstruction, RiscInstruction
from ouca.riscv.machine import RiscMachine


@RiscInstruction.register_instruction('add')
class AddRiscInstruction(RTypeRiscInstruction):
    OPCODE = 0b0110011
    FUNCT3 = 0b000
    FUNCT7 = 0b0000000

    def run(self, machine: RiscMachine) -> None:
        machine.write_register(
            self.rd,
            machine.read_register(self.rs1) +
            machine.read_register(self.rs2)
        )
        machine.program_counter += 4


@RiscInstruction.register_instruction('addi')
class AddImmediateRiscInstruction(ITypeRiscInstruction):
    OPCODE = 0b0010011
    FUNCT3 = 0b000

    def run(self, machine: RiscMachine) -> None:
        machine.write_register(
            self.rd,
            machine.read_register(self.rs1) + self.n
        )
        machine.program_counter += 4
