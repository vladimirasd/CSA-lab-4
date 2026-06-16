class Memory:
    def set_ar(self, ar):
        self._ar = ar

    def set_dr(self, dr):
        self._dr = dr

    def __init__(self, ar, dr):
        self._ar = ar
        self._dr = dr
        self._mem = [[0] * 8 for _ in range(2**24)]

    def set(self):
        self._mem[self._ar.get_as_int()] = self._dr.get()[0:8]
        self._mem[self._ar.get_as_int() + 1] = self._dr.get()[8:16]
        self._mem[self._ar.get_as_int() + 2] = self._dr.get()[16:24]
        self._mem[self._ar.get_as_int() + 3] = self._dr.get()[24:32]
        return f"Writing word in mem on address {self._ar.get_as_int()}"

    def set_byte(self):
        self._mem[self._ar.get_as_int()] = self._dr.get_byte()
        return f"Writing byte in mem on address {self._ar.get_as_int()}"

    def get_dump(self, adr, is_byte=False):
        if is_byte:
            return self._mem[adr].copy()
        return (
            self._mem[adr].copy()
            + self._mem[adr + 1].copy()
            + self._mem[adr + 2].copy()
            + self._mem[adr + 3].copy()
        )

    def get(self):
        return (
            self._mem[self._ar.get_as_int()].copy()
            + self._mem[self._ar.get_as_int() + 1].copy()
            + self._mem[self._ar.get_as_int() + 2].copy()
            + self._mem[self._ar.get_as_int() + 3].copy()
        )

    def get_byte(self):
        return self._mem[self._ar.get_as_int()].copy()

    def get_big(self):
        result = (
            self._mem[self._ar.get_as_int()]
            + self._mem[self._ar.get_as_int() + 1]
            + self._mem[self._ar.get_as_int() + 2]
            + self._mem[self._ar.get_as_int() + 3]
        )
        if self._ar.get_as_int() + 7 >= len(self._mem):
            result += 32 * [0]
        else:
            result += (
                self._mem[self._ar.get_as_int() + 4]
                + self._mem[self._ar.get_as_int() + 5]
                + self._mem[self._ar.get_as_int() + 6]
                + self._mem[self._ar.get_as_int() + 7]
            )

        if self._ar.get_as_int() + 11 >= len(self._mem):
            result += 32 * [0]
        else:
            result += (
                self._mem[self._ar.get_as_int() + 8]
                + self._mem[self._ar.get_as_int() + 9]
                + self._mem[self._ar.get_as_int() + 10]
                + self._mem[self._ar.get_as_int() + 11]
            )

        if self._ar.get_as_int() + 15 >= len(self._mem):
            result += 32 * [0]
        else:
            result += (
                self._mem[self._ar.get_as_int() + 12]
                + self._mem[self._ar.get_as_int() + 13]
                + self._mem[self._ar.get_as_int() + 14]
                + self._mem[self._ar.get_as_int() + 15]
            )
        return result

    def write_code(self, start, data):
        for i in range(len(data)):
            self._mem[start + i * 4] = data[0:8]
            self._mem[start + i * 4 + 1] = data[8:16]
            self._mem[start + i * 4 + 2] = data[16:24]
            self._mem[start + i * 4 + 3] = data[24:32]
