class Mux:
    def set_connections(self, connections):
        self._connections = connections

    def __init__(self, name, connections):
        self._connections = connections
        self._name = name
        self._value = 32 * [0]

    def set(self, ind):
        self._value = self._connections[ind].get()
        return f"Setting value to {self._name} from {ind}"

    def set_byte(self, ind):
        self._value[:8] = self._connections[ind].get()[:8]
        last = self._value[7]
        for i in range(8, 32):
            self._value[i] = last
        return f"Setting value to {self._name} from {ind}"

    def get(self):
        return self._value.copy()

    def get_byte(self):
        return self._value[:8].copy()

    def set_op1_val(self, ind):
        self._value = self._connections["RS"].get(ind).op1_val

    def set_op2_val(self, ind):
        self._value = self._connections["RS"].get(ind).op2_val

    def set_imm_val(self, ind):
        self._value = self._connections["RS"].get(ind).imm
