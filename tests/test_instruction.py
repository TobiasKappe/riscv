import pytest

from riscv.data import RiscInteger
from riscv.machine import RiscMachine
from riscv.implementation.arithmetic import \
    AddRiscInstruction, AddImmediateRiscInstruction
from riscv.implementation.branch import \
    BranchLessThanRiscInstruction
from riscv.implementation.memory import \
    LoadWordRiscInstruction, StoreWordRiscInstruction


class TestAddRiscInstruction:
    def test_run(self):
        machine = RiscMachine()
        machine.registers[1] = RiscInteger(123)
        machine.registers[2] = RiscInteger(456)

        add = AddRiscInstruction(3, 1, 2)
        add.run(machine)

        assert machine.registers[3] == RiscInteger(579)

    def test_decode(self):
        instr = AddRiscInstruction(RiscInteger(0b1101101010000001110110011))
        assert instr.rd == 7
        assert instr.rs1 == 10
        assert instr.rs2 == 27

    def test_encode(self):
        add = AddRiscInstruction(7, 10, 27)
        assert add.encode() == \
            RiscInteger(0b1101101010000001110110011)


class TestAddImmediateRiscInstruction:
    def test_run(self):
        machine = RiscMachine()
        machine.registers[1] = RiscInteger(123)

        add = AddImmediateRiscInstruction(3, 1, RiscInteger(456))
        add.run(machine)

        assert machine.registers[3] == RiscInteger(579)

    def test_decode(self):
        instr = AddImmediateRiscInstruction(
            RiscInteger(0b01101101101110001000010000010011)
        )
        assert instr.rd == 8
        assert instr.rs1 == 17
        assert instr.n == RiscInteger(1755)

    def test_encode(self):
        addi = AddImmediateRiscInstruction(8, 17, RiscInteger(1755))
        assert addi.encode() == \
            RiscInteger(0b01101101101110001000010000010011)


class TestBranchLessThanRiscInstruction:
    @pytest.mark.parametrize(
        'rs1, rs2, jump',
        [
            (123, 456, True),
            (456, 123, False),
            (123, 123, False),
            (-1, 2, True),
            (5, -5, False),
        ]
    )
    def test_run(self, rs1, rs2, jump):
        machine = RiscMachine()
        machine.registers[1] = RiscInteger(rs1)
        machine.registers[2] = RiscInteger(rs2)
        machine.program_counter = 220

        blt = BranchLessThanRiscInstruction(1, 2, RiscInteger(780))
        blt.run(machine)

        assert machine.program_counter == 1000 if jump else 224

    def test_run_above(self):
        machine = RiscMachine()
        machine.registers[1] = RiscInteger(123)
        machine.registers[2] = RiscInteger(456)
        machine.program_counter = 220

        blt = BranchLessThanRiscInstruction(1, 2, RiscInteger(780))
        blt.run(machine)

        assert machine.program_counter == 1000

    def test_decode(self):
        blt = BranchLessThanRiscInstruction(
            RiscInteger(0b11001001011101011100100001100011, signed=False)
        )
        assert blt.rs1 == 11
        assert blt.rs2 == 23
        assert blt.offset == RiscInteger(-2928)

    def test_encode(self):
        blt = BranchLessThanRiscInstruction(11, 23, RiscInteger(-2928))
        assert blt.encode() == \
            RiscInteger(0b11001001011101011100100001100011, signed=False)


class TestLoadWordRiscInstruction:
    @pytest.mark.parametrize(
        'address, base, offset, value',
        [
            (120, 100, 20, 456),
            (160, 200, -40, 789),
        ]
    )
    def test_run(self, address, base, offset, value):
        machine = RiscMachine()
        machine.registers[1] = RiscInteger(base)
        machine.memory[address] = RiscInteger(value)

        lw = LoadWordRiscInstruction(2, 1, RiscInteger(offset))
        lw.run(machine)

        assert machine.registers[2] == RiscInteger(value)

    def test_decode(self):
        lw = LoadWordRiscInstruction(
            RiscInteger(0b11011011011010110010011100000011, signed=False)
        )
        assert lw.rd == 14
        assert lw.rs1 == 22
        assert lw.n == RiscInteger(-586)

    def test_encode(self):
        lw = LoadWordRiscInstruction(14, 22, RiscInteger(-586))
        assert lw.encode() == \
            RiscInteger(0b11011011011010110010011100000011, signed=False)


class TestStoreWordRiscInstruction:
    @pytest.mark.parametrize(
        'address, base, offset, value',
        [
            (120, 100, 20, 456),
            (160, 200, -40, 789),
        ]
    )
    def test_run(self, address, base, offset, value):
        machine = RiscMachine()
        machine.registers[1] = RiscInteger(base)
        machine.registers[2] = RiscInteger(value)

        sw = StoreWordRiscInstruction(1, 2, RiscInteger(offset))
        sw.run(machine)

        assert address in machine.memory
        assert machine.memory[address] == RiscInteger(value)

    def test_decode(self):
        sw = StoreWordRiscInstruction(
            RiscInteger(0b01010101001111101010101010100011)
        )
        assert sw.rs1 == 29
        assert sw.rs2 == 19
        assert sw.n == RiscInteger(1365)

    def test_encode(self):
        sw = StoreWordRiscInstruction(29, 19, RiscInteger(1365))
        assert sw.encode() == \
            RiscInteger(0b01010101001111101010101010100011)
