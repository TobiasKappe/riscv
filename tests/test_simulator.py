import math

import pytest

from ouca.riscv.data import RiscInteger
from ouca.riscv.simulator import RiscSimulator


class TestRiscSimulator:
    @pytest.mark.parametrize('value', [8, 9, 10, 71, 169])
    def test_square_root(self, value):
        instructions = [
            'add x2, x0, x0',
            'add x3, x0, x0',
            'addi x4, x0, 1',
            'start:',
            'add x5, x3, x4',
            'blt x1, x5, end',
            'add x3, x3, x4',
            'addi x4, x4, 2',
            'addi x2, x2, 1',
            'blt x0, x1, start',
            'end:',
        ]

        s = RiscSimulator(instructions)
        s.machine.registers[1] = RiscInteger(value)
        s.simulate()

        assert s.machine.registers[2] == \
            RiscInteger(math.floor(math.sqrt(value)))
