from multimethod import multimethod
from typing import List


from riscv.instruction import RiscInstruction
from riscv.machine import RiscMachine


class RiscSimulator:
    @multimethod
    def __init__(self, instructions: List[RiscInstruction], **kwargs):
        self.machine = RiscMachine(**kwargs)
        self.instructions = instructions

    @multimethod
    def __init__(self, instructions: List[str], **kwargs): # noqa
        self.machine = RiscMachine(**kwargs)
        self.instructions = RiscInstruction.parse(instructions)

    def simulate(self) -> None:
        while self.machine.program_counter < len(self.instructions) * 4:
            instruction = self.instructions[self.machine.program_counter >> 2]
            instruction.run(self.machine)
