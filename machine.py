from ouca.riscv.data import RiscInteger


class RiscMachine:
    def __init__(self, memory: dict = None, protected_registers={0}):
        self.registers = {i: RiscInteger(0) for i in range(32)}
        self.program_counter = 0
        self.memory = memory or {}
        self.protected_registers = protected_registers
        self.protected_registers_written = set()

    def write_register(self, index: int, value: int) -> None:
        if index in self.protected_registers:
            self.protected_registers_written |= {index}
            return

        if index < 0 or index > 31:
            raise Exception('Write to unknown register')

        self.registers[index] = value

    def read_register(self, index: int) -> int:
        if index < 0 or index > 31:
            raise Exception('Read from unknown register')

        return self.registers[index]

    def write_memory(self, address: int, value: int) -> None:
        if address.bits[0:2] != [False, False]:
            raise Exception('Unaligned memory write')

        self.memory[address.to_int()] = value

    def read_memory(self, address: int) -> int:
        if address.bits[0:2] != [False, False]:
            raise Exception('Unaligned memory read')

        return self.memory[address.to_int()]
