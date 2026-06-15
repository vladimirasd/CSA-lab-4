class OutputInterface:
    def __init__(self, name, connections):
        self._output_queue = []
        self._name = name
        self._connections = connections

    def set(self, ind):
        self._output_queue.append(self._connections[ind].get())
        return f"Setting value to {self._name} from {ind}"

    def set_byte(self, ind):
        self._output_queue.append(self._connections[ind].get_byte())
        return f"Setting value to {self._name} from {ind}"

    def set_from_rob(self):
        self._output_queue.append(self._connections["ROB"].get_head_store_data())

    def set_byte_from_rob(self):
        self._output_queue.append(self._connections["ROB"].get_head_store_data()[:8])
