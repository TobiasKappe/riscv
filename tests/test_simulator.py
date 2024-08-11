import pytest

from riscv.data import RiscInteger
from riscv.simulator import RiscSimulator


class TestRiscSimulator:
    @pytest.mark.parametrize('value', range(20))
    def test_fibonnacci(self, value):
        def fib_rec(n):
            if n == 0:
                return 0
            elif n == 1:
                return 1
            else:
                return fib_rec(n-1) + fib_rec(n-2)

        instructions = [
            'addi x2, x0, 1',
            'addi x3, x0, 0',
            'addi x4, x0, 1',
            'blt x0, x1, check',
            'addi x2, x0, 0',
            'blt x0, x1, exit',
            'loop:',
            'add x5, x2, x3',
            'add x3, x0, x2',
            'add x2, x0, x5',
            'addi x4, x4, 1',
            'check:',
            'blt x4, x1, loop',
            'exit:',
        ]

        s = RiscSimulator(instructions)
        s.machine.registers[1] = RiscInteger(value)
        s.simulate()

        assert s.machine.registers[2] == RiscInteger(fib_rec(value))
