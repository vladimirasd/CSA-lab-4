import struct

from vm.alu.alu import Alu
from vm.cu.control_unit import CU
from vm.cu.rob import ROB
from vm.cu.rs import RS
from vm.io.inputinterface import InputInterface
from vm.io.outputinterface import OutputInterface
from vm.mem.memory import Memory
from vm.mem.mux import Mux
from vm.mem.registers import (
    AdressRegister,
    DataRegister,
    ImmRegister,
    ProgramCounter,
    ZeroRegister,
)


class CPU:
    def __init__(self, bin_file, start, input_file=None, log_file=None, log_level=3):
        self._data_registers = {}

        reg = ZeroRegister("x0", None)
        self._data_registers["x0"] = reg

        for i in range(1, 32):
            reg = DataRegister(f"x{i}", None)
            self._data_registers[f"x{i}"] = reg

        self._s0 = self._data_registers["x0"]
        self._s1 = self._data_registers["x1"]
        self._s2 = self._data_registers["x2"]
        self._s3 = self._data_registers["x3"]
        self._s4 = self._data_registers["x4"]
        self._s5 = self._data_registers["x5"]
        self._s6 = self._data_registers["x6"]
        self._s7 = self._data_registers["x7"]

        self._ir1 = DataRegister("ir1", None)
        self._ir2 = DataRegister("ir2", None)
        self._ir3 = DataRegister("ir3", None)
        self._ir4 = DataRegister("ir4", None)  # Instruction Registers
        self._dr = DataRegister("dr", None)  # Data Register
        self._ar = AdressRegister("ar", None)  # Address Register
        self._pc = ProgramCounter("pc", None)  # Program Counter

        self._imm1 = ImmRegister("imm1", None)
        self._imm2 = ImmRegister("imm2", None)
        self._imm3 = ImmRegister("imm3", None)
        self._imm4 = ImmRegister("imm4", None)

        self._data_registers["ir1"] = self._ir1
        self._data_registers["ir2"] = self._ir2
        self._data_registers["ir3"] = self._ir3
        self._data_registers["ir4"] = self._ir4

        self._data_registers["imm1"] = self._imm1
        self._data_registers["imm2"] = self._imm2
        self._data_registers["imm3"] = self._imm3
        self._data_registers["imm4"] = self._imm4

        self._rob = ROB()
        self._rs = RS()

        self._mem = Memory(self._ar, self._dr)

        left_sources = {}
        for name, reg in self._data_registers.items():
            left_sources[name] = reg
        left_sources["dr"] = self._dr
        left_sources["pc"] = self._pc
        left_sources["ROB"] = self._rob
        left_sources["RS"] = self._rs

        right_sources = {}
        for name, reg in self._data_registers.items():
            right_sources[name] = reg
        right_sources["ROB"] = self._rob
        right_sources["dr"] = self._dr
        right_sources["RS"] = self._rs

        self._mux_alu_1_left = Mux("mux_alu_1_left", left_sources)
        self._mux_alu_1_right = Mux("mux_alu_1_right", right_sources)
        self._alu1 = Alu("ALU_1", self._mux_alu_1_left, self._mux_alu_1_right)

        self._mux_alu_2_left = Mux("mux_alu_2_left", left_sources)
        self._mux_alu_2_right = Mux("mux_alu_2_right", right_sources)
        self._alu2 = Alu("ALU_2", self._mux_alu_2_left, self._mux_alu_2_right)

        self._mux_alu_3_left = Mux("mux_alu_3_left", left_sources)
        self._mux_alu_3_right = Mux("mux_alu_3_right", right_sources)
        self._alu3 = Alu("ALU_3", self._mux_alu_3_left, self._mux_alu_3_right)

        self._mux_alu_4_left = Mux("mux_alu_4_left", left_sources)
        self._mux_alu_4_right = Mux("mux_alu_4_right", right_sources)
        self._alu4 = Alu("ALU_4", self._mux_alu_4_left, self._mux_alu_4_right)

        self._i0 = InputInterface([0] * 32, "i0")
        self._o0 = OutputInterface("o0", {"ROB": self._rob})

        self._cu = CU(
            ir1=self._ir1,
            ir2=self._ir2,
            ir3=self._ir3,
            ir4=self._ir4,
            imm1=self._imm1,
            imm2=self._imm2,
            imm3=self._imm3,
            imm4=self._imm4,
            alu1=self._alu1,
            alu2=self._alu2,
            alu3=self._alu3,
            alu4=self._alu4,
            registers=self._data_registers,
            inputs={"i0": self._i0},
            outputs={"o0": self._o0},
            dr=self._dr,
            pc=self._pc,
            ar=self._ar,
            muxs=[
                self._mux_alu_1_left,
                self._mux_alu_1_right,
                self._mux_alu_2_left,
                self._mux_alu_2_right,
                self._mux_alu_3_left,
                self._mux_alu_3_right,
                self._mux_alu_4_left,
                self._mux_alu_4_right,
            ],
            mem=self._mem,
            rob=self._rob,
            rs=self._rs,
            log_file=log_file,
            log_level=log_level,
        )

        self._data_registers["x27"]._value = [0, 0, 1, 0, 0, 1, 0, 1] + 24 * [0]
        self._data_registers["x26"]._value = [1, 1, 0, 0, 0, 1, 0, 0] + 24 * [0]
        self._data_registers["x29"]._value = [0, 0, 1, 0, 0, 1, 0, 0] + 24 * [0]
        self._data_registers["x28"]._value = [0, 0, 1, 0, 0, 1, 0, 0] + 24 * [0]
        self._data_registers["x31"]._value = [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
        ] + 8 * [0]
        self._data_registers["x30"]._value = [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            0,
        ] + 8 * [0]

        self._connect_registers()

        self._pc._value = start
        self.load_binary_to_memory(bin_file)

        if input_file is not None:
            with open(input_file) as f:
                data = f.read().split(";")[:-1]
                for i in data:
                    tick, ch = i.split()
                    tick = int(tick)
                    ch = self.int_to_bits(ord(ch), 8) if ch[0] != "\\" else self.int_to_bits(int(ch[1:]))
                    self._i0.add(tick, ch)

    def _connect_registers(self):
        alu_results = {
            "ALU_1": self._alu1,
            "ALU_2": self._alu2,
            "ALU_3": self._alu3,
            "ALU_4": self._alu4,
        }

        data_sources = {}
        data_sources.update(alu_results)
        data_sources["dr"] = self._dr
        data_sources["mem"] = self._mem
        data_sources["ROB"] = self._rob

        for reg in self._data_registers.values():
            reg.set_connections(data_sources)

        addr_sources = {}
        addr_sources.update(alu_results)
        addr_sources["dr"] = self._dr
        addr_sources["pc"] = self._pc
        addr_sources["ROB"] = self._rob

        self._ir1.set_connections({"mem": self._mem})
        self._ir2.set_connections({"mem": self._mem})
        self._ir3.set_connections({"mem": self._mem})
        self._ir4.set_connections({"mem": self._mem})

        self._imm1.set_connections({"ir1": self._ir1})
        self._imm2.set_connections({"ir2": self._ir2})
        self._imm3.set_connections({"ir3": self._ir3})
        self._imm4.set_connections({"ir4": self._ir4})

        dr_sources = {"mem": self._mem, "i0": self._i0, "ROB": self._rob}
        dr_sources.update(alu_results)
        self._dr.set_connections(dr_sources)

        ar_sources = {}
        ar_sources.update(alu_results)
        ar_sources["pc"] = self._pc
        ar_sources["dr"] = self._dr
        ar_sources["ROB"] = self._rob
        self._ar.set_connections(ar_sources)

        pc_sources = {}
        pc_sources.update(alu_results)
        pc_sources["dr"] = self._dr
        pc_sources["ROB"] = self._rob
        self._pc.set_connections(pc_sources)

    def write_code(self, addr, data):
        self._mem.write_code(addr, data)

    def int_to_bits(self, val: int, n: int = 32) -> list[int]:
        return [(val >> i) & 1 for i in range(n)]

    def load_binary_to_memory(self, filename: str, base_addr: int = 0):

        with open(filename, "rb") as f:
            data = f.read()

        if len(data) % 4 != 0:
            raise ValueError(f"Размер файла {len(data)} не кратен 4 байтам")

        for offset in range(0, len(data), 4):
            word = struct.unpack("<I", data[offset : offset + 4])[0]
            bits = self.int_to_bits(word, 32)
            self.write_code(base_addr + offset, bits)

    def to_int(self, data):
        res = 0
        for i in range(0, 32):
            res += data[i] << i
        return res

    def run(self):
        while True:
            self._cu.tick()
