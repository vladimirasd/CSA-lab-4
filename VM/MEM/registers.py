class DataRegister:
    def __init__(self, name, connections):
        self._name = name
        self._connections = connections
        self._value = 32 * [0]

    def set(self, ind, byte=None):
        if byte is None:
            self._value = self._connections[ind].get()
        else:
            self._value = self._connections[ind].get_big()[byte * 32 : byte * 32 + 32]
        return f"Setting value to {self._name} from {ind}"

    def set_from_rob(self):
        self._value = self._connections["ROB"].get_head_store_data()
        return f"Setting store value to {self._name} from ROB"

    def set_byte(self, ind):
        self._value[:8] = self._connections[ind].get()[:8]
        return f"Setting value to {self._name} from {ind}"

    def get(self):
        return self._value.copy()

    def set_connections(self, connections):
        self._connections = connections

    def get_byte(self):
        return self._value[:8].copy()

    def get_as_int(self):
        result = 0
        for i in range(31, -1, -1):
            result = result * 2 + self._value[i]
        return result

    def set_interrupt_vector(self, ind):
        self._value = self._connections[ind].get_interrupt_vector()
        return f"Setting interrupt vector to {self._name} from {ind}"


class AdressRegister:
    def __init__(self, name, connections):
        self._name = name
        self._connections = connections
        self._value = 32 * [0]

    def set(self, ind):
        self._value = self._connections[ind].get()
        return f"Setting value to {self._name} from {ind}"

    def set_rob(self):
        self._value = self._connections["ROB"].get_head_store_addr()
        return f"Setting value to {self._name} from ROB"

    def set_connections(self, connections):
        self._connections = connections

    def set_byte(self, ind):
        self._value[:8] = self._connections[ind].get()[8:]
        return f"Setting value to {self._name} from {ind}"

    def get(self):
        return self._value.copy()

    def get_byte(self):
        return self._value[:8].copy()

    def get_as_int(self):
        result = 0
        for i in range(23, -1, -1):
            result = result * 2 + self._value[i]
        return result


class Buffer:
    def __init__(self, name, connections):
        self._name = name
        self._connections = connections
        self._value = 128 * [0]

    def set_first(self, ind):
        self._value[:32] = self._connections[ind].get()

    def set_second(self, ind):
        self._value[32:64] = self._connections[ind].get()

    def set_third(self, ind):
        self._value[64:96] = self._connections[ind].get()

    def set_fourth(self, ind):
        self._value[96:128] = self._connections[ind].get()

    def set_connections(self, connections):
        self._connections = connections

    def get_first(self):
        return self._value[:32]

    def get_second(self):
        return self._value[32:64]

    def get_third(self):
        return self._value[64:96]

    def get_fourth(self):
        return self._value[96:128]


class ProgramCounter:
    _value = [0] * 4 + 28 * [1]

    def __init__(self, name, connections):
        self._name = name
        self._connections = connections

    def set(self, ind):
        self._value = self._connections[ind].get()
        return f"Setting value to {self._name} from {ind}"

    def set_connections(self, connections):
        self._connections = connections

    def set_byte(self, ind):
        self._value[:8] = self._connections[ind].get()[8:]
        return f"Setting value to {self._name} from {ind}"

    def get(self):
        return self._value.copy()

    def get_byte(self):
        return self._value[:8].copy()

    def get_as_int(self):
        result = 0
        for i in range(31, -1, -1):
            result = result * 2 + self._value[i]
        return result

    def increment(self, inc):
        inc = inc + 8 * [inc[-1]]
        value = self._value
        off_top = 32 * [0]
        result = 32 * [0]

        result[0] = (value[0] + inc[0]) % 2
        off_top[0] = (value[0] + inc[0]) // 2

        for i in range(1, 32):
            sum = off_top[i - 1] + value[i] + inc[i]
            result[i] = sum % 2
            off_top[i] = sum // 2

        self._value = result
        return "Incrementing pc"

    def add(self, bits):
        inc = bits
        value = self._value
        off_top = 32 * [0]
        result = 32 * [0]

        result[0] = (value[0] + inc[0]) % 2
        off_top[0] = (value[0] + inc[0]) // 2

        for i in range(1, 32):
            sum = off_top[i - 1] + value[i] + inc[i]
            result[i] = sum % 2
            off_top[i] = sum // 2

        self._value = result
        return "Adding imm to pc by special summ"


class RobCounter:
    _value = 3 * [0]

    def __init__(self, name):
        self._name = name

    def get_as_int(self):
        result = 0
        for i in range(2, -1, -1):
            result = result * 2 + self._value[i]
        return result

    def get(self):
        return self._value.copy()

    def increment(self, inc):
        value = self._value
        off_top = 3 * [0]
        result = 3 * [0]

        result[0] = (value[0] + inc[0]) % 2
        off_top[0] = (value[0] + inc[0]) // 2

        for i in range(1, 3):
            sum = off_top[i - 1] + value[i] + inc[i]
            result[i] = sum % 2
            off_top[i] = sum // 2

        self._value = result
        return "Incrementing ROB_counter"


class RsCounter:
    _value = 4 * [0]

    def __init__(self, name):
        self._name = name

    def get_as_int(self):
        result = 0
        for i in range(3, -1, -1):
            result = result * 2 + self._value[i]
        return result

    def get(self):
        return self._value.copy()

    def increment(self, inc):
        value = self._value
        off_top = 4 * [0]
        result = 4 * [0]

        result[0] = (value[0] + inc[0]) % 2
        off_top[0] = (value[0] + inc[0]) // 2

        for i in range(1, 4):
            sum = off_top[i - 1] + value[i] + inc[i]
            result[i] = sum % 2
            off_top[i] = sum // 2

        self._value = result
        return "Incrementing RS_counter"


class ZeroRegister:
    def __init__(self, name, connections):
        self._name = name
        self._connections = connections
        self._value = 32 * [0]

    def set(self, ind):
        return f"Setting value to {self._name} from {ind}"

    def set_byte(self, ind):
        return f"Setting value to {self._name} from {ind}"

    def get(self):
        return self._value.copy()

    def set_connections(self, connections):
        self._connections = connections

    def get_byte(self):
        return self._value[:8].copy()

    def get_as_int(self):
        return 0


class ImmRegister:
    def __init__(self, name, connections):
        self._name = name
        self._connections = connections
        self._value = 32 * [0]

    def set(self, ind):
        self._value = 32 * [0]
        self._value[:12] = self._connections[ind].get()[20:32]
        for i in range(12, 32):
            self._value[i] = self._value[i - 1]
        return f"Setting value to {self._name} from {ind}"

    def set_for_branch(self, ind):
        self._value = 32 * [0]
        inst = self._connections[ind].get()
        imm_bit12 = [inst[31]]
        imm_bit11 = [inst[30]]
        imm_10_5 = inst[25:30]
        imm_4_1 = inst[7:12]
        imm = imm_4_1 + imm_10_5 + imm_bit11 + imm_bit12 + [0]
        self._value[0:12] = imm
        for i in range(12, 32):
            self._value[i] = self._value[i - 1]
        return f"Setting value to {self._name} from {ind} "

    def set_for_jal(self, ind):
        self._value = 32 * [0]
        self._value[0:20] = self._connections[ind].get()[12:32]
        for i in range(20, 32):
            self._value[i] = self._value[i - 1]
        return f"Setting value to {self._name} from {ind}"

    def set_for_lui(self, ind):
        self._value = 32 * [0]
        self._value[0:20] = self._connections[ind].get()[12:32]
        for i in range(20, 32):
            self._value[i] = self._value[i - 1]
        return f"Setting value to {self._name} from {ind}"

    def set_for_jalr(self, ind):
        self._value = 32 * [0]
        self._value[0:12] = self._connections[ind].get()[20:32]
        for i in range(12, 32):
            self._value[i] = self._value[i - 1]
        return f"Setting value to {self._name} from {ind}"

    def get(self):
        return self._value.copy()

    def set_connections(self, connections):
        self._connections = connections

    def get_byte(self):
        return self._value[:8].copy()

    def get_as_int(self):
        result = 0
        for i in range(31, -1, -1):
            result = result * 2 + self._value[i]
        return result
