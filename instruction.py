from ouca.riscv.machine import RiscMachine
from ouca.riscv.data import RiscInteger


class RiscInstruction:
    def run(self, machine: RiscMachine) -> None:
        raise NotImplementedError

    def assembly(self) -> str:
        raise NotImplementedError

    def encode(self) -> RiscInteger:
        raise NotImplementedError

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} "{self.assembly()}">'
