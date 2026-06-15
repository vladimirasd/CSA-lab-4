import heapq


class InputInterface:
    def __init__(self, vector_addr, name):
        self._input_queue = []
        self._vector_addr = vector_addr
        self._pending = False
        self._name = name

    def add(self, clock, data):
        heapq.heappush(self._input_queue, (clock, data))

    def is_active(self, current_clock):
        if self._input_queue and self._input_queue[0][0] <= current_clock:
            self._pending = True
            return True
        return False

    def get_byte(self, tick):
        if not self._pending or not self._input_queue:
            return None

        best_idx = -1
        best_clock = -1
        for i, (clock, _) in enumerate(self._input_queue):
            if clock <= tick and clock > best_clock:
                best_clock = clock
                best_idx = i

        if best_idx == -1:
            return None

        clock, byte = self._input_queue.pop(best_idx)
        self._pending = False
        return byte

    def get(self, tick):
        if not self._pending or not self._input_queue:
            return None

        best_idx = -1
        best_clock = -1
        for i, (clock, _) in enumerate(self._input_queue):
            if clock <= tick and clock > best_clock:
                best_clock = clock
                best_idx = i

        if best_idx == -1:
            return None

        clock, word = self._input_queue.pop(best_idx)
        self._pending = False
        return word

    def get_interrupt_vector(self):
        return self._vector_addr
