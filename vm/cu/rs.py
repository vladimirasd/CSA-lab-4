from vm.mem.registers import RsCounter


class RSEntry:
    def __init__(self):
        self.valid = [0]
        self.rob_tag = 3 * [0]
        self.is_memory = [0]
        self.op1_ready = [0]
        self.op1_val = [0] * 32
        self.op1_tag = [0] * 3
        self.op2_ready = [0]
        self.op2_val = [0] * 32
        self.op2_tag = [0] * 3
        self.mem_tag = [0] * 3
        self.mem_ready = [0]
        self.imm = [0] * 32
        self.store_addr = [0] * 32
        self.store_data = [0] * 32
        self.funct3 = [0] * 3
        self.funct7 = [0] * 7
        self.opcode = [0] * 7
        self.pc = 32 * [0]
        self.is_store = [0]


class RS:
    def __init__(self):
        self._entries = [RSEntry() for _ in range(8)]
        self._counter = RsCounter("rs_counter")

    def flush(self):
        for e in self._entries:
            e.valid = [0]
        self._counter._value = [0, 0, 0, 0]

    def is_full(self):
        return self._counter.get() == [0, 0, 0, 1]

    def get(self, ind):
        return self._entries[ind]

    def get_empty_addr(self):
        for i in range(8):
            if self._entries[i].valid == [0]:
                return i

    def add_entry(
        self,
        rob_tag,
        is_memory,
        op1_ready,
        op1_val,
        op1_tag,
        op2_ready,
        op2_val,
        op2_tag,
        imm,
        dest_reg,
        opcode,
        funct3,
        funct7,
        pc,
        is_store,
        mem_ready=None,
        mem_tag=None,
        store_addr=None,
        store_data=None,
    ):
        e = self._entries[self.get_empty_addr()]
        e.valid = [1]
        e.is_store = is_store.copy()
        e.rob_tag = rob_tag.copy()
        e.is_memory = is_memory.copy()
        e.op1_ready = op1_ready.copy()
        e.opcode = opcode.copy()
        e.funct3 = funct3.copy()
        e.funct7 = funct7.copy()
        e.op1_tag = op1_tag.copy()
        op2_tag = op2_tag.copy()
        e.pc = pc.copy()
        e.op1_val = op1_val.copy()
        e.op1_tag = op1_tag.copy()
        e.op2_ready = op2_ready.copy()
        e.op2_val = op2_val.copy()
        e.op2_tag = op2_tag.copy()
        e.imm = imm.copy()
        e.dest_reg = dest_reg.copy()
        e.mem_tag = mem_tag.copy()
        e.mem_ready = mem_ready.copy()
        if store_addr is not None:
            e.store_addr = store_addr.copy()
        else:
            e.store_addr = 32 * [0]
        if store_data is not None:
            e.store_data = store_data.copy()
        else:
            e.store_data = 32 * [0]
        self._counter.increment([1, 0, 0, 0])
        return

    def free_slots(self):
        free = 0
        for e in self._entries:
            if e.valid == [0]:
                free += 1
        return free

    def broadcast(self, rob_tag, value, log_file, mem_tag=None):
        if len(value) < 32:
            value += 24 * [0]
        for e in self._entries:
            if not e.valid[0]:
                continue
            if not e.op1_ready[0] and e.op1_tag == rob_tag:
                e.op1_val = value.copy()
                e.op1_ready[0] = 1
            if not e.op2_ready[0] and e.op2_tag == rob_tag:
                e.op2_val = value.copy()
                e.op2_ready[0] = 1
            if e.mem_tag == mem_tag and e.mem_ready == [0]:
                e.mem_ready = [1]

    def get_ready_indices(self, max_count=4, mem_once=True):
        ready = []
        mem_selected = False
        selected_tags = []
        for i, e in enumerate(self._entries):
            if not e.valid[0]:
                continue
            if e.op1_ready[0] and e.op2_ready[0] and (not e.is_memory[0] or e.mem_ready[0]):
                depends = False
                if not e.op1_ready[0] and e.op1_tag in selected_tags:
                    depends = True
                if not e.op2_ready[0] and e.op2_tag in selected_tags:
                    depends = True
                if depends:
                    continue
                if e.is_memory[0]:
                    if mem_once and mem_selected:
                        continue
                    mem_selected = True
                ready.append(i)
                selected_tags.append(e.rob_tag)
                if len(ready) == max_count:
                    break
        return ready

    def get_entry(self, index):
        return self._entries[index]

    def clear_entry(self, index, log_file):
        self._counter.increment([1, 1, 1, 1])
        self._entries[index].valid = [0]
