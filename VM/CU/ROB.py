from VM.MEM.registers import RobCounter


class ROBEntry:
    def __init__(self):
        self.valid = [0]
        self.ready = [0]
        self.dest_reg = 5 * [0]
        self.value = 32 * [0]
        self.pc = 32 * [0]
        self.is_store = [0]
        self.store_addr = 32 * [0]
        self.store_data = 32 * [0]
        self.is_out = [0]
        self.is_byte = [0]
        self.is_mem = [0]
        self.is_halt = [0]
        self.mem_op = [0] * 3
        self.manage = [0, 0, 0]


class ROB:
    def __init__(self):
        self._entries = [ROBEntry() for _ in range(8)]
        self._head = RobCounter("head")
        self._tail = RobCounter("tail")

    def free_slots(self):
        free = 0
        for e in self._entries:
            if e.valid == [0]:
                free += 1
        return free

    def flush(self):
        for e in self._entries:
            e.valid = [0]
        self._head = RobCounter("head")
        self._tail = RobCounter("tail")

    def to_int(self, data):
        res = 0
        for i in range(len(data)):
            res += data[i] << i
        return res

    def is_full(self):
        return (self._tail.get_as_int() + 1) % 8 == self._head.get_as_int()

    def get_index_from_tag(self, tag):
        idx = (self.to_int(tag) - 1) % len(self._entries)
        return idx

    def is_empty(self):
        return self._tail.get_as_int() == self._head.get_as_int()

    def get_tail(self):
        return self._entries[self._tail.get_as_int()]

    def get_tag(self):
        return self._tail.get()

    def get_head_tag(self):
        return self._head.get()

    def get_head(self):
        return self._entries[self._head.get_as_int()]

    def allocate(self, dest_reg, pc, is_store, is_out, is_byte, mem_op, is_mem, manage, is_halt):
        idx = self._tail.get_as_int()
        self._entries[idx].valid = [1]
        self._entries[idx].ready = [0]
        self._entries[idx].dest_reg = dest_reg
        self._entries[idx].pc = pc
        self._entries[idx].is_store = is_store
        self._entries[idx].is_out = is_out
        self._entries[idx].is_byte = is_byte
        self._entries[idx].mem_op = mem_op
        self._entries[idx].is_mem = is_mem
        self._entries[idx].manage = manage
        self._entries[idx].is_halt = is_halt
        self._tail.increment([1, 0, 0])

    def commit_head(self, log_file):
        idx = self._head.get_as_int()
        self._entries[idx].valid = [0]
        self._head.increment([1, 0, 0])

    def get_head_store_addr(self):
        return self._entries[self._head.get_as_int()].store_addr.copy()

    def get(self):
        return self._entries[self._head.get_as_int()].value.copy()

    def get_head_store_data(self):
        return self._entries[self._head.get_as_int()].store_data.copy()
