class CU:
    def __init__(
        self,
        ir1,
        ir2,
        ir3,
        ir4,
        imm1,
        imm2,
        imm3,
        imm4,
        alu1,
        alu2,
        alu3,
        alu4,
        registers,
        dr,
        pc,
        ar,
        muxs,
        mem,
        inputs,
        outputs,
        rob,
        rs,
        log_file=None,
        log_level=3,
    ):
        self._registers = registers
        self._dr = dr
        self._pc = pc
        self._ar = ar
        self._muxs = muxs
        self._mem = mem
        self._ir1 = ir1
        self._ir2 = ir2
        self._ir3 = ir3
        self._ir4 = ir4
        self._imm1 = imm1
        self._imm2 = imm2
        self._imm3 = imm3
        self._imm4 = imm4
        self._alu1 = alu1
        self._alu2 = alu2
        self._alu3 = alu3
        self._alu4 = alu4
        self._result_buffer = 32 * [0]
        self._clock = 0
        self._inputs = inputs
        self._outputs = outputs
        self._in_trap = False
        self._pre_trap = False
        self._rob = rob
        self._rs = rs
        self.rename = {
            key: {"ready": True, "from_tag": False, "tag": [0, 0, 0]} for key in registers
        }
        self.mem_rename = {
            key: {"ready": True, "from_tag": False, "tag": [0, 0, 0]} for key in registers
        }
        self._state = 0
        self._i_for_issue = 0
        self._to_trap_state = 0
        self.log_file = log_file
        self.log_level = log_level

    def log(self, str, log_level):
        if self.log_level >= log_level:
            print(str, file=self.log_file)

    def handle_interrupts(self):
        self.log("===========INTER===========", 3)
        self._state = 0

        for input_name in self._inputs:
            inpt = self._inputs[input_name]
            if inpt.is_active(self._clock):
                self.log(f"{input_name} IS ACTIVE", 3)
                if self._in_trap:
                    self.log("BUT ALREADY IN TRAP", 3)
                else:
                    self._pre_trap = True
                    if self._rob.free_slots() == 8 and self._rs.free_slots() == 8:
                        self._state = 4
                        if self._to_trap_state == 0:
                            self.log(f"PC BEFORE TRAP {self.to_int(self._pc._value)}", 3)
                            self.log(self._alu1._left.set("x31"), 3)
                            self.log(self._alu1.decrement(), 3)
                            self._to_trap_state += 1

                        elif self._to_trap_state == 1:
                            self.log(self._registers["x31"].set(self._alu1._name), 3)
                            self.log(self._alu1._left.set("x31"), 3)
                            self.log(self._alu1.pass_value(), 3)
                            self.log(self._ar.set(self._alu1._name), 3)
                            self.log(self._alu1._left.set(self._pc._name), 3)
                            self.log(self._alu1.pass_value(), 3)
                            self.log(self._dr.set(self._alu1._name), 3)
                            self.log(self._mem.set(), 3)
                            self._to_trap_state += 1

                        elif self._to_trap_state == 2:
                            self.log(self._dr.set_interrupt_vector(inpt._name), 3)
                            self.log(self._alu1._left.set(self._dr._name), 3)
                            self.log(self._alu1.pass_value(), 3)
                            self.log(self._ar.set(self._alu1._name), 3)
                            self.log(self._dr.set("mem"), 3)
                            self._to_trap_state += 1
                        elif self._to_trap_state == 3:
                            self.log(self._alu1._left.set(self._dr._name), 3)
                            self.log(self._alu1.pass_value(), 3)
                            self.log(self._pc.set(self._alu1._name), 3)
                            self.log(f"current pc :{self.to_int(self._pc._value)}", 3)
                            self._in_trap = True
                            self._pre_trap = False
                            self._to_trap_state = 0
                            self._to_trap_state = 0
                            self._state = 0
                    else:
                        self.log(
                            "BUT CANT GO IN TRAP : NOT ALL INST EXECUTED AND COMMITED",
                            3,
                        )
                    break

    def from_bits_to_name(self, addr):
        real_addr = 0
        for i in range(4, -1, -1):
            real_addr = 2 * real_addr + addr[i]
        return f"x{real_addr}"

    def from_bits_to_name_for_input(self, addr):
        real_addr = 0
        for i in range(4, -1, -1):
            real_addr = 2 * real_addr + addr[i]
        return f"i{real_addr}"

    def from_bits_to_name_for_output(self, addr):
        real_addr = 0
        for i in range(4, -1, -1):
            real_addr = 2 * real_addr + addr[i]
        return f"o{real_addr}"

    def to_int(self, data):
        res = 0
        for i in range(len(data)):
            res += data[i] << i
        return res

    def to_bits(self, data):
        res = []
        for _ in range(32):
            res += [data % 2]
            data //= 2
        return res

    def dump_state(self):
        self.log("===========DUMP===========", 3)
        self.log("ROB:", 3)
        for i, e in enumerate(self._rob._entries):
            if e.valid[0]:
                self.log(
                    f"  [{i}] valid={e.valid[0]} ready={e.ready[0]} dest={self.from_bits_to_name(e.dest_reg)} value={self.to_int(e.value)} is_halt={e.is_halt[0]} is_store={e.is_store[0]} pc = {self.to_int(e.pc)}",
                    3,
                )
        self.log("RS:", 3)
        for i, e in enumerate(self._rs._entries):
            if e.valid[0]:
                self.log(
                    f"  [{i}] valid={e.valid[0]} op1_ready={e.op1_ready[0]} op1_tag={e.op1_tag} op2_ready={e.op2_ready[0]}  op2_tag={e.op2_tag}  is_mem={e.is_memory[0]} mem_rd{e.mem_ready} mem_tag={e.mem_tag} pc = {self.to_int(e.pc)}",
                    3,
                )
        for reg in self._registers:
            if reg in ["x1", "x2", "x3", "x4", "x5", "x30", "x31"]:
                self.log(
                    f" reg : {self._registers[reg]._name} state : {self.to_int(self._registers[reg].get())} = {(self._registers[reg].get())}",
                    3,
                )
        self.log(
            f"mem[x30]={self.to_int(self._mem.get_dump(self.to_int(self._registers['x30'].get())))}",
            3,
        )
        self.log(
            f"mem[x30 + 4]={self.to_int(self._mem.get_dump(self.to_int(self._registers['x30'].get()) + 4))}",
            3,
        )
        self.log(
            f"mem[x31]={self.to_int(self._mem.get_dump(self.to_int(self._registers['x31'].get())))}",
            3,
        )
        self.log(
            f"mem[x31 + 4]={self.to_int(self._mem.get_dump(self.to_int(self._registers['x31'].get()) + 4))}",
            3,
        )

    def flush(self):
        self.log("===========FLUSH===========", 3)
        self._rs.flush()
        self._rob.flush()
        self.rename = {
            key: {"ready": True, "from_tag": False, "tag": [0, 0, 0]} for key in self._registers
        }
        self.mem_rename = {
            key: {"ready": True, "from_tag": False, "tag": [0, 0, 0]} for key in self._registers
        }

    def commit(self):
        self.log("===========COMMIT===========", 3)
        if self._rob.get_head().ready[0] and self._rob.get_head().valid[0]:
            head = self._rob.get_head()

            if head.is_halt[0]:
                self.log(f"COMMIT: HALT FLAG SET pc={self.to_int(head.pc)}", 0)
                self.log(f"TICKS {self._clock}", 0)
                raise ValueError("HALT")

            if head.is_store[0] and not head.is_halt[0]:
                self.log(
                    f"COMMIT: store addr={self.to_int(head.store_addr)} data={self.to_int(head.store_data)}={(head.store_data)} pc={self.to_int(head.pc)} ",
                    3,
                )
            elif head.is_mem[0] and not head.is_halt[0]:
                self.log(
                    f"COMMIT: load reg {self.from_bits_to_name(head.dest_reg)} value={self.to_int(head.value)}={head.value} pc={self.to_int(head.pc)} ",
                    3,
                )
            elif head.manage == [0, 0, 0] and not head.is_halt[0]:
                self.log(
                    f"COMMIT: reg {self.from_bits_to_name(head.dest_reg)} value={self.to_int(head.value)}={head.value} pc={self.to_int(head.pc)}",
                    3,
                )

            if self._rob.get_head().is_store[0]:
                self._ar.set_rob()

                if self._rob.get_head().is_out == [1]:
                    port_num = self.to_int(self._rob.get_head().store_addr)
                    port_name = f"o{port_num}"
                    if self._rob.get_head().is_byte == [0]:  # word
                        self._outputs[port_name].set_from_rob()
                    else:
                        self._outputs[port_name].set_byte_from_rob()
                else:
                    self._dr.set_from_rob()

                    if self._rob.get_head().is_byte == [0]:  # sw
                        self._mem.set()
                    else:
                        self._mem.set_byte()

                    reg_num = self.from_bits_to_name(head.mem_op)

                    if self.mem_rename[reg_num]["tag"] == self._rob.get_head_tag():
                        self.mem_rename[reg_num]["ready"] = True

                self._rs.broadcast(
                    self._rob.get_head_tag(),
                    self._rob.get_head().value,
                    self.log_file,
                    self._rob.get_head_tag(),
                )
                self._rob.commit_head(self.log_file)

            else:
                reg_num = self.from_bits_to_name(self._rob.get_head().dest_reg)

                if not head.is_byte[0]:
                    self._registers[reg_num].set("ROB")
                else:
                    self._registers[reg_num].set_byte("ROB")

                if self.rename[reg_num]["tag"] == self._rob.get_head_tag():
                    self.rename[reg_num]["ready"] = True

                if self._rob.get_head().is_mem[0] and not self._rob.get_head().is_out[0]:
                    reg_num = self.from_bits_to_name(head.mem_op)
                    if self.mem_rename[reg_num]["tag"] == self._rob.get_head_tag():
                        self.mem_rename[reg_num]["ready"] = True

                self._rs.broadcast(
                    self._rob.get_head_tag(),
                    self._rob.get_head().value,
                    self.log_file,
                    self._rob.get_head_tag(),
                )
                self._rob.commit_head(self.log_file)

                if head.manage == [1, 0, 0]:  # branch
                    if head.value[0] == 1:
                        self._pc._value = head.pc
                        self._pc.increment(head.store_data)
                    self.log(
                        f"COMMIT: branch pc={self.to_int(self._pc.get())} data={self.to_int(head.value)} pc={self.to_int(head.pc)} ",
                        3,
                    )
                    if head.value[0] == 1:
                        self.flush()
                elif head.manage == [0, 1, 0]:  # jal
                    self._pc._value = head.pc
                    self._pc.increment(head.store_data)
                    self.log(f"COMMIT: jal pc={self.to_int(self._pc.get())}", 3)
                    self.flush()
                elif head.manage == [1, 1, 0]:  # jalr
                    self.log(f"COMMIT: jalr pc={self.to_int(head.store_data)}", 3)
                    self._pc._value = head.store_data
                    self.flush()
                elif head.manage == [0, 0, 1]:  # jalri
                    self.log(f"COMMIT: jalri pc={self.to_int(head.store_data)} ", 3)
                    self._pc._value = head.store_data
                    self._in_trap = False
                    self.flush()

        if not self._rob.get_head().ready[0] or not self._rob.get_head().valid[0]:
            self._state += 1

    def issue(self):
        self.log("===========ISSUE===========", 3)
        if not self._pre_trap:
            data = [
                [self._ir1, self._imm1],
                [self._ir2, self._imm2],
                [self._ir3, self._imm3],
                [self._ir4, self._imm4],
            ]
            if self._rob.free_slots() > 0 and self._rs.free_slots() > 0 and self._i_for_issue < 4:
                ir, imm = data[self._i_for_issue]
                self._i_for_issue += 1
                inst = ir.get()
                opcode = inst[0:7]
                rs1 = None
                rs2 = None
                rd = 5 * [0]
                imm_val = [0] * 32
                is_memory = [0]
                is_store = [0]
                is_out = [0]
                is_byte = [0]
                is_halt = [0]
                op1_val = 32 * [0]
                op2_val = 32 * [0]
                mem_tag = [0] * 3
                mem_ready = [1]
                mem_op = [0] * 5
                manage = 3 * [0]
                if opcode == [0, 1, 1, 0, 0, 1, 1]:  # R-type
                    rs1 = inst[15:20]
                    rs2 = inst[20:25]
                    rd = inst[7:12]
                elif opcode == [0, 0, 0, 0, 0, 0, 0]:
                    rd = inst[7:12]
                    imm.set_for_lui(ir._name)
                    imm_val = imm.get()
                elif opcode == [0, 0, 1, 0, 0, 1, 1] or opcode == [
                    0,
                    0,
                    0,
                    0,
                    0,
                    1,
                    1,
                ]:  # I-type arith
                    rs1 = inst[15:20]
                    rd = inst[7:12]
                    imm.set(ir._name)
                    imm_val = imm.get()
                elif opcode == [1, 1, 0, 0, 1, 1, 1]:  # LOAD
                    rs1 = inst[15:20]
                    rd = inst[7:12]
                    imm.set(ir._name)
                    imm_val = imm.get()
                    is_memory = [1]
                    mem_op = rs1
                    if self.mem_rename[self.from_bits_to_name(rs1)]["ready"]:
                        self.mem_rename[self.from_bits_to_name(rs1)]["ready"] = False
                    else:
                        mem_ready = [0]
                        mem_tag = self.mem_rename[self.from_bits_to_name(rs1)]["tag"]
                    if inst[12:15] == [0, 0, 0]:
                        is_byte = [1]
                    self.mem_rename[self.from_bits_to_name(rs1)]["tag"] = self._rob.get_tag()
                elif opcode == [0, 1, 0, 0, 0, 1, 1]:  # STORE (sw, sb)
                    rs1 = inst[15:20]
                    rs2 = inst[20:25]
                    imm.set_for_branch(ir._name)
                    imm_val = imm.get()
                    is_memory = [1]
                    is_store = [1]
                    mem_op = rs1
                    if self.mem_rename[self.from_bits_to_name(rs1)]["ready"]:
                        self.mem_rename[self.from_bits_to_name(rs1)]["ready"] = False
                    else:
                        mem_ready = [0]
                        mem_tag = self.mem_rename[self.from_bits_to_name(rs1)]["tag"]
                    self.mem_rename[self.from_bits_to_name(rs1)]["tag"] = self._rob.get_tag()
                    if inst[12:15] == [0, 0, 0]:
                        is_byte = [1]
                elif opcode == [1, 1, 0, 0, 0, 1, 1]:  # BRANCH
                    rs1 = inst[15:20]
                    rs2 = inst[20:25]
                    imm.set_for_branch(ir._name)
                    imm_val = imm.get()
                    manage = [1, 0, 0]
                elif opcode == [1, 1, 0, 1, 1, 1, 1]:  # JAL
                    rd = inst[7:12]
                    imm.set_for_jal(ir._name)
                    imm_val = imm.get()
                    manage = [0, 1, 0]
                elif opcode == [0, 0, 0, 1, 1, 1, 1]:  # JALR
                    rs1 = inst[15:20]
                    rd = inst[7:12]
                    imm.set_for_jalr(ir._name)
                    imm_val = imm.get()
                    manage = [1, 1, 0]
                elif opcode == [0, 0, 1, 1, 1, 1, 1]:  # JALRI
                    rs1 = inst[15:20]
                    rd = inst[7:12]
                    imm.set_for_jalr(ir._name)
                    imm_val = imm.get()
                    manage = [0, 0, 1]
                elif opcode == [0, 0, 0, 0, 0, 0, 1]:  # in
                    rs1 = inst[15:20]
                    rd = inst[7:12]
                    is_memory = [1]
                    if inst[12:15] == [0, 0, 1]:
                        is_byte = [1]
                elif opcode == [1, 0, 0, 0, 0, 0, 1]:  # out
                    rs1 = inst[15:20]
                    rd = inst[7:12]
                    is_memory = [1]
                    is_store = [1]
                    is_out = [1]
                    if inst[12:15] == [0, 0, 1]:
                        is_byte = [1]
                else:
                    if inst == 7 * [1] + 25 * [0]:
                        is_halt = [1]

                if rs1 is not None and rs1 != 5 * [0]:
                    src1 = self.from_bits_to_name(rs1)
                    ren1 = self.rename[src1]
                    if ren1["ready"]:
                        op1_val = self._registers[src1].get()
                        op1_ready = [1]
                        op1_tag = [0, 0, 0]
                    else:
                        op1_ready = [0]
                        op1_val = [0] * 32
                        op1_tag = ren1["tag"].copy()
                else:
                    op1_ready = [1]
                    op1_val = [0] * 32
                    op1_tag = [0, 0, 0]

                if rs2 is not None and rs2 != 5 * [0]:
                    src2 = self.from_bits_to_name(rs2)
                    ren2 = self.rename[src2]
                    if ren2["ready"]:
                        op2_val = self._registers[src2].get()
                        op2_ready = [1]
                        op2_tag = [0, 0, 0]
                    else:
                        op2_ready = [0]
                        op2_val = [0] * 32
                        op2_tag = ren2["tag"].copy()
                else:
                    op2_ready = [1]
                    op2_tag = [0, 0, 0]
                    if rs2 != 5 * [0]:
                        op2_val = imm_val

                rob_tag = self._rob.get_tag()
                pc = self.to_bits(self.to_int(self._pc.get()))
                self._pc.increment(
                    [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                )
                self._rob.allocate(
                    rd, pc, is_store, is_out, is_byte, mem_op, is_memory, manage, is_halt
                )

                if rd != 5 * [0]:
                    dest = self.from_bits_to_name(rd)
                    self.rename[dest]["ready"] = False
                    self.rename[dest]["tag"] = rob_tag.copy()

                self._rs.add_entry(
                    rob_tag=rob_tag,
                    is_memory=is_memory,
                    op1_ready=op1_ready,
                    op1_val=op1_val,
                    op1_tag=op1_tag,
                    op2_ready=op2_ready,
                    op2_val=op2_val,
                    op2_tag=op2_tag,
                    imm=imm_val,
                    dest_reg=rd if rd is not None else [0] * 5,
                    store_addr=None,
                    store_data=None,
                    opcode=inst[0:7],
                    funct3=inst[12:15],
                    funct7=inst[25:32],
                    pc=pc,
                    mem_tag=mem_tag,
                    mem_ready=mem_ready,
                    is_store=is_store,
                )

                self.log(
                    f"ISSUE: pc={self.to_int(pc)} opcode={opcode} rd={self.to_int(rd)} rs1={self.to_int(rs1) if rs1 else None} op1_ready={op1_ready} op1_tag={op1_tag} rs2={self.to_int(rs2) if rs2 else None} op2_ready={op2_ready} op2_tag={op2_tag} rob_tag={self.to_int(rob_tag)} is_halt={is_halt[0]}",
                    3,
                )

            if self._rob.free_slots() == 0 or self._rs.free_slots() == 0 or self._i_for_issue >= 4:
                self._state += 1
                self._i_for_issue = 0
        else:
            self._state += 1
            self._i_for_issue = 0

    def execute(self):
        self.log("===========EXECUTE===========", 2)

        self._state += 1

        ready_indices = self._rs.get_ready_indices(max_count=4, mem_once=True)

        self.log(f"READY: {ready_indices}", 2)
        alus = [self._alu1, self._alu2, self._alu3, self._alu4]
        it = iter(alus)
        for idx in ready_indices:
            e = self._rs._entries[idx]
            e.valid = [0]
            opcode = e.opcode
            funct3 = e.funct3
            funct7 = e.funct7
            alu = next(it)
            self.log(
                f"EXEC: rob_tag={self.to_int(e.rob_tag)} opcode={opcode} funct3={funct3} funct7={funct7} pc = {self.to_int(e.pc)}",
                2,
            )
            if opcode == [0, 1, 1, 0, 0, 1, 1]:  # R-type
                alu._left.set_op1_val(idx)
                alu._right.set_op2_val(idx)
                if funct3 == [0, 0, 0]:
                    if funct7 == [0, 0, 0, 0, 0, 0, 0]:  # add +
                        (alu.add())
                    if funct7 == [0, 1, 0, 0, 0, 0, 0]:  # sub +
                        (alu.sub())
                    if funct7 == [1, 0, 0, 0, 0, 0, 0]:  # mul +
                        (alu.mul())
                if funct3 == [1, 1, 1] and funct7 == [0, 0, 0, 0, 0, 0, 0]:  # and +
                    (alu.logic_and())
                if funct3 == [1, 1, 0]:
                    if funct7 == [0, 0, 0, 0, 0, 0, 0]:  # or +
                        (alu.logic_or())
                    if funct7 == [1, 0, 0, 0, 0, 0, 0]:  # not +
                        (alu.logic_not())
                    if funct7 == [1, 1, 0, 0, 0, 0, 0]:  # rem +
                        (alu.rem())
                if funct3 == [1, 0, 1]:
                    if funct7 == [0, 0, 0, 0, 0, 0, 0]:  # srl +
                        (alu.shift_right())
                    if funct7 == [0, 1, 0, 0, 0, 0, 1]:  # sra +
                        (alu.shift_right_arithmetic())
                if funct3 == [0, 1, 1] and funct7 == [0, 0, 0, 0, 0, 0, 0]:  # sltu +
                    (alu.set_less_than_unsigned())
                if funct3 == [1, 0, 0]:
                    if funct7 == [0, 0, 0, 0, 0, 0, 0]:  # xor
                        (alu.logic_xor())
                    if funct7 == [1, 0, 0, 0, 0, 0, 0]:  # div
                        (alu.div())
                if funct3 == [0, 0, 1]:
                    if funct7 == [0, 0, 0, 0, 0, 0, 0]:  # mulh
                        (alu.mulh())
                    if funct7 == [0, 0, 0, 0, 0, 0, 1]:  # sll
                        (alu.shift_left())
                if funct3 == [0, 1, 0]:
                    if funct7 == [0, 0, 0, 0, 0, 0, 0]:  # slt
                        (alu.set_less_than())
                    if funct7 == [1, 0, 0, 0, 0, 0, 0]:  # seq
                        (alu.set_equals())
                    if funct7 == [1, 1, 0, 0, 0, 0, 0]:  # sne
                        (alu.set_not_equals())
                    if funct7 == [1, 1, 1, 0, 0, 0, 0]:  # seqom
                        (alu.set_equals_or_more())
                result = alu.get()

                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].value = result.copy()
                self._rob._entries[rob_idx].ready[0] = 1
                self._rs.broadcast(e.rob_tag, result, self.log_file)

                self._rs.clear_entry(idx, self.log_file)
            elif opcode == [0, 0, 0, 0, 0, 0, 0]:
                alu._left.set_imm_val(idx)

                alu.pass_value()
                result = alu.get()
                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].value = result.copy()
                self._rob._entries[rob_idx].ready[0] = 1
                self._rs.broadcast(e.rob_tag, result, self.log_file)

                self._rs.clear_entry(idx, self.log_file)
            elif opcode == [0, 0, 1, 0, 0, 1, 1]:  # I-type arith
                alu._left.set_op1_val(idx)
                alu._right.set_op2_val(idx)
                if funct3 == [0, 0, 0]:  # addi
                    (alu.add())
                if funct3 == [0, 1, 0]:  # slti
                    (alu.set_less_than())
                if funct3 == [1, 1, 1]:  # andi
                    (alu.logic_and())
                if funct3 == [1, 1, 0]:  # ori
                    (alu.logic_or())
                if funct3 == [1, 0, 0]:  # xori
                    (alu.logic_xor())

                result = alu.get()

                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].value = result.copy()
                self._rob._entries[rob_idx].ready[0] = 1
                self._rs.broadcast(e.rob_tag, result, self.log_file)

                self._rs.clear_entry(idx, self.log_file)

            elif opcode == [0, 0, 0, 0, 0, 1, 1]:  # I-type shift
                alu._left.set_op1_val(idx)
                alu._right.set_op2_val(idx)
                if funct3 == [0, 0, 0]:
                    (alu.shift_left())
                if funct3 == [1, 0, 0]:
                    (alu.shift_right())
                if funct3 == [0, 1, 0]:
                    (alu.shift_right_arithmetic())

                result = alu.get()

                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].value = result.copy()
                self._rob._entries[rob_idx].ready[0] = 1
                self._rs.broadcast(e.rob_tag, result, self.log_file)

                self._rs.clear_entry(idx, self.log_file)

            elif opcode == [1, 1, 0, 0, 1, 1, 1]:  # LOAD
                alu._left.set_op1_val(idx)
                alu._right.set_op2_val(idx)
                alu.add()
                self._ar.set(alu._name)
                if funct3 == [0, 1, 0]:  # lw (word)
                    self._dr.set("mem")
                    result = self._dr.get()
                else:
                    self._dr.set_byte("mem")
                    result = self._dr.get_byte()
                    result += 24 * [0]
                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].value = result.copy()
                self._rob._entries[rob_idx].ready[0] = 1
                self._rs.broadcast(e.rob_tag, result, self.log_file, e.mem_tag)

                self._rs.clear_entry(idx, self.log_file)

            elif opcode == [0, 1, 0, 0, 0, 1, 1]:  # STORE
                alu._left.set_op1_val(idx)
                alu._right.set_imm_val(idx)
                alu.add()
                store_addr = alu.get()
                store_data = e.op2_val
                if funct3 == [0, 1, 0]:  # sw (word)
                    # сохраняем как есть
                    pass
                elif funct3 == [0, 0, 0]:  # sb (byte)
                    store_data = store_data[:8] + [0] * 24

                rob_idx = self.to_int(e.rob_tag)

                self._rob._entries[rob_idx].store_addr = store_addr.copy()
                self._rob._entries[rob_idx].store_data = store_data.copy()
                self._rob._entries[rob_idx].ready[0] = 1
                self._rs.clear_entry(idx, self.log_file)
            elif opcode == [1, 1, 0, 0, 0, 1, 1]:  # BRANCH
                alu._left.set_op1_val(idx)
                alu._right.set_op2_val(idx)

                if funct3 == [0, 0, 0]:  # beq
                    alu.set_equals()
                elif funct3 == [0, 0, 1]:  # bne
                    alu.set_not_equals()
                elif funct3 == [1, 0, 0]:  # bgt (signed >)
                    alu.set_greater_than()
                elif funct3 == [0, 1, 1]:  # bgte (signed >)
                    alu.set_greater_than_or_equals()
                elif funct3 == [0, 1, 0]:
                    alu.set_less_than()
                elif funct3 == [1, 0, 1]:  # ble (signed <=)
                    alu.set_less_than_or_equals()
                elif funct3 == [1, 1, 0]:
                    alu.set_less_than_unsigned()
                elif funct3 == [1, 1, 1]:
                    alu.set_less_than_unsigned_or_equals()

                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].ready[0] = 1
                self._rob._entries[rob_idx].value = alu.get()
                self._rob._entries[rob_idx].store_data = e.imm
                self._rs.clear_entry(idx, self.log_file)

            elif opcode == [1, 1, 0, 1, 1, 1, 1]:  # JAL
                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].value = self.to_bits(self.to_int(e.pc) + 4)
                self._rob._entries[rob_idx].ready[0] = 1
                self._rob._entries[rob_idx].store_data = e.imm
                self._rs.clear_entry(idx, self.log_file)
            elif opcode == [0, 0, 0, 1, 1, 1, 1] or opcode == [0, 0, 1, 1, 1, 1, 1]:  # JALR
                rob_idx = self.to_int(e.rob_tag)
                alu._left.set_op1_val(idx)
                alu._right.set_imm_val(idx)
                alu.add()
                self._rob._entries[rob_idx].store_data = alu.get()
                self._rob._entries[rob_idx].value = self.to_bits(self.to_int(e.pc) + 4)
                self._rob._entries[rob_idx].ready[0] = 1
                break
            elif opcode == [0, 0, 0, 0, 0, 0, 1]:  # IN
                if e.funct3 == [0, 0, 0]:
                    port_name = self.from_bits_to_name_for_input(e.op1_val)
                    result = self._inputs[port_name].get()
                elif e.funct3 == [0, 0, 1]:
                    port_name = self.from_bits_to_name_for_input(e.op1_val)
                    result_byte = self._inputs[port_name].get_byte(self._clock)
                    result = result_byte.copy() + 24 * [0]
                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].value = result.copy()
                self._rob._entries[rob_idx].ready[0] = 1
                self._rs.broadcast(e.rob_tag, result, self.log_file)
                self._rs.clear_entry(idx, self.log_file)

            elif opcode == [1, 0, 0, 0, 0, 0, 1]:  # OUT
                port_num = self.to_int(e.dest_reg)
                if e.funct3 == [0, 0, 0]:
                    data = e.op1_val
                elif e.funct3 == [0, 0, 1]:
                    data = e.op1_val[:8] + [0] * 24
                else:
                    self._rs.clear_entry(idx, self.log_file)
                    continue

                rob_idx = self.to_int(e.rob_tag)
                self._rob._entries[rob_idx].store_data = data.copy()
                self._rob._entries[rob_idx].store_addr = self.to_bits(port_num)
                self._rob._entries[rob_idx].ready[0] = 1
                self._rob._entries[rob_idx].is_store = [1]
                self._rob._entries[rob_idx].is_out = [1]
                self._rs.clear_entry(idx, self.log_file)

            else:
                if opcode == 7 * [1]:
                    rob_idx = self.to_int(e.rob_tag)
                    self._rob._entries[rob_idx].ready[0] = 1
                    self._rob._entries[rob_idx].is_halt[0] = 1
                    self.log("HALT DETECTED", 3)
                    self._rs.clear_entry(idx, self.log_file)

    def fetch_next(self):
        self.log("===========FETCH===========", 3)
        if not self._pre_trap:
            self.log(
                f"ROB SLOTS={self._rob.free_slots()}, RS SLOTS={self._rs.free_slots()}",
                3,
            )
            self._ar.set("pc")
            self._ir1.set("mem", 0)
            self._ir2.set("mem", 1)
            self._ir3.set("mem", 2)
            self._ir4.set("mem", 3)
            self.log(f"IR 1: {self._ir1.get()}", 3)
            self.log(f"IR 2: {self._ir2.get()}", 3)
            self.log(f"IR 3: {self._ir3.get()}", 3)
            self.log(f"IR 4: {self._ir4.get()}", 3)

        self._state += 1

    def tick(self):
        if self._state != 0:
            self.log(f"\n=== TICK {self._clock} ===", 3)

        if self._state == 0:
            self.log(f"\n=== TICK {self._clock} ===", 2)
            self.dump_state()
            self.execute()
        elif self._state == 1:
            self.commit()
        elif self._state == 2:
            self.fetch_next()
        elif self._state == 3:
            self.issue()
        elif self._state == 4:
            self.handle_interrupts()
        self._clock += 1
