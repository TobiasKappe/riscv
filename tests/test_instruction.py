import pytest

from ouca.riscv import sim


class TestAddRiscInstruction:
    def test_run(self):
        machine = sim.RiscMachine()
        machine.registers[1] = sim.RiscInteger(123)
        machine.registers[2] = sim.RiscInteger(456)

        add = sim.AddRiscInstruction(3, 1, 2)
        add.run(machine)

        assert machine.registers[3] == sim.RiscInteger(579)

    def test_encode(self):
        add = sim.AddRiscInstruction(7, 10, 27)
        assert add.encode() == \
            sim.RiscInteger(0b1101101010000001110110011)


class TestAddImmediateRiscInstruction:
    def test_run(self):
        machine = sim.RiscMachine()
        machine.registers[1] = sim.RiscInteger(123)

        add = sim.AddImmediateRiscInstruction(3, 1, sim.RiscInteger(456))
        add.run(machine)

        assert machine.registers[3] == sim.RiscInteger(579)

    def test_encode(self):
        addi = sim.AddImmediateRiscInstruction(8, 17, sim.RiscInteger(1755))
        assert addi.encode() == \
            sim.RiscInteger(0b01101101101110001000010000010011)


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
        machine = sim.RiscMachine()
        machine.registers[1] = sim.RiscInteger(rs1)
        machine.registers[2] = sim.RiscInteger(rs2)
        machine.program_counter = 220

        blt = sim.BranchLessThanRiscInstruction(1, 2, sim.RiscInteger(780))
        blt.run(machine)

        assert machine.program_counter == 1000 if jump else 224

    def test_run_above(self):
        machine = sim.RiscMachine()
        machine.registers[1] = sim.RiscInteger(123)
        machine.registers[2] = sim.RiscInteger(456)
        machine.program_counter = 220

        blt = sim.BranchLessThanRiscInstruction(1, 2, sim.RiscInteger(780))
        blt.run(machine)

        assert machine.program_counter == 1000

    def test_encode(self):
        blt = sim.BranchLessThanRiscInstruction(11, 23, sim.RiscInteger(-2928))
        assert blt.encode() == \
            sim.RiscInteger(0b11001001011101011100100001100011, signed=False)


class TestLoadWordRiscInstruction:
    @pytest.mark.parametrize(
        'address, base, offset, value',
        [
            (120, 100, 20, 456),
            (160, 200, -40, 789),
        ]
    )
    def test_run(self, address, base, offset, value):
        machine = sim.RiscMachine()
        machine.registers[1] = sim.RiscInteger(base)
        machine.memory[address] = sim.RiscInteger(value)

        lw = sim.LoadWordRiscInstruction(2, sim.RiscInteger(offset), 1)
        lw.run(machine)

        assert machine.registers[2] == sim.RiscInteger(value)

    def test_encode(self):
        lw = sim.LoadWordRiscInstruction(14, sim.RiscInteger(-586), 22)
        assert lw.encode() == \
            sim.RiscInteger(0b11011011011010110010011100000011, signed=False)


class TestStoreWordRiscInstruction:
    @pytest.mark.parametrize(
        'address, base, offset, value',
        [
            (120, 100, 20, 456),
            (160, 200, -40, 789),
        ]
    )
    def test_run(self, address, base, offset, value):
        machine = sim.RiscMachine()
        machine.registers[1] = sim.RiscInteger(base)
        machine.registers[2] = sim.RiscInteger(value)

        sw = sim.StoreWordRiscInstruction(2, sim.RiscInteger(offset), 1)
        sw.run(machine)

        assert address in machine.memory
        assert machine.memory[address] == sim.RiscInteger(value)

    def test_encode(self):
        sw = sim.StoreWordRiscInstruction(19, sim.RiscInteger(1365), 29)
        assert sw.encode() == \
            sim.RiscInteger(0b01010101001111101010101010100011)
