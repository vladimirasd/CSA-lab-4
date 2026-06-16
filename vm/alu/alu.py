class Alu:
    _result = 0
    _off_top = 32 * [0]

    def __init__(self, name, left, right):
        self._left = left
        self._right = right
        self._name = name

    def add(self):
        left = self._left.get()
        right = self._right.get()
        off_top = 32 * [0]
        result = 32 * [0]

        result[0] = (left[0] + right[0]) % 2
        off_top[0] = (left[0] + right[0]) // 2

        for i in range(1, 32):
            sum = off_top[i - 1] + left[i] + right[i]
            result[i] = sum % 2
            off_top[i] = sum // 2

        self._result = result
        self._off_top = off_top
        return f"{self._name} executing add"

    def sub(self):

        left = self._left.get()
        right = self._right.get()

        for i in range(32):
            right[i] = 1 - right[i]

        carry = 1
        for i in range(32):
            total = right[i] + carry
            right[i] = total % 2
            carry = total // 2

        off_top = 32 * [0]
        result = 32 * [0]

        result[0] = (left[0] + right[0]) % 2
        off_top[0] = (left[0] + right[0]) // 2

        for i in range(1, 32):
            s = off_top[i - 1] + left[i] + right[i]
            result[i] = s % 2
            off_top[i] = s // 2
        self._result = result
        self._off_top = off_top
        return f"{self._name} executing sub"

    def logic_and(self):

        left = self._left.get()
        right = self._right.get()
        result = 32 * [0]

        for i in range(32):
            result[i] = 1 if (left[i] == 1 and right[i] == 1) else 0

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing logic and"

    def logic_or(self):
        left = self._left.get()
        right = self._right.get()
        result = 32 * [0]

        for i in range(32):
            result[i] = 1 if (left[i] == 1 or right[i] == 1) else 0

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing logic or"

    def logic_not(self):

        left = self._left.get()
        result = 32 * [0]

        for i in range(32):
            result[i] = 1 if left[i] == 0 else 0

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing logic not"

    def logic_xor(self):

        left = self._left.get()
        right = self._right.get()
        result = 32 * [0]
        for i in range(32):
            result[i] = 0 if (left[i] == right[i]) else 1
        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing logic xor"

    def neg(self):

        result = self._left.get()
        off_top = 32 * [0]
        for i in range(32):
            result[i] = (result[i] + 1) % 2
        off_top[0] = (result[0] + 1) // 2
        for i in range(1, 32):
            sum = off_top[i - 1] + result[i]
            result[i] = sum % 2
            off_top[i] = sum // 2
        self._result = result
        return f"{self._name} executing neg"

    def mul(self):

        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_int(left)
        right_val = self._bits_to_int(right)

        result_val = left_val * right_val

        result_val = result_val & 0xFFFFFFFF

        self._result = self._int_to_bits(result_val, 32)
        self._off_top = 32 * [0]
        return f"{self._name} executing mul"

    def mulh(self):

        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)

        result_val = left_val * right_val
        result_val = (result_val >> 32) & 0xFFFFFFFF

        self._result = self._int_to_bits(result_val, 32)
        self._off_top = 32 * [0]
        return f"{self._name} executing mulh"

    def div(self):

        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)

        result_val = 4294967295 if right_val == 0 else left_val

        self._result = self._int_to_bits(result_val & 0xFFFFFFFF, 32)
        self._off_top = 32 * [0]
        return f"{self._name} executing div"

    def rem(self):
        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)

        result_val = left_val if right_val == 0 else left_val % right_val

        self._result = self._int_to_bits(result_val & 0xFFFFFFFF, 32)
        self._off_top = 32 * [0]
        return f"{self._name} executing rem"

    def shift_left(self):
        left = self._left.get()
        shift = self._get_shift_amount()
        result = 32 * [0]
        for i in range(32):
            if i + shift < 32:
                result[i + shift] = left[i]
        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing shift left"

    def shift_right(self):
        left = self._left.get()
        shift = self._get_shift_amount()

        result = 32 * [0]
        for i in range(32):
            if i - shift >= 0:
                result[i - shift] = left[i]

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing shift right"

    def shift_right_arithmetic(self):

        left = self._left.get()
        shift = self._get_shift_amount()
        sign_bit = left[31]

        result = 32 * [0]
        for i in range(32):
            if i - shift >= 0:
                result[i - shift] = left[i]

        for i in range(shift):
            result[31 - i] = sign_bit

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing shift right arithmetic"

    def set_less_than(self):

        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)

        result = 32 * [0]
        if left_val < right_val:
            result[0] = 1

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set less than"

    def set_greater_than(self):

        left = self._right.get()
        right = self._left.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)

        result = 32 * [0]
        if left_val < right_val:
            result[0] = 1

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set less than"

    def set_greater_than_or_equals(self):

        left = self._right.get()
        right = self._left.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)

        result = 32 * [0]
        if left_val <= right_val:
            result[0] = 1

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set less than"

    def set_less_than_or_equals(self):

        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)

        result = 32 * [0]
        if left_val <= right_val:
            result[0] = 1

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set less than"

    def set_equals(self):
        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)
        result = 32 * [0]
        if left_val == right_val:
            result[0] = 1
        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set equals"

    def set_not_equals(self):
        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_signed_int(left)
        right_val = self._bits_to_signed_int(right)
        result = 32 * [0]
        if left_val != right_val:
            result[0] = 1
        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set not equals"

    def set_less_than_unsigned(self):
        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_unsigned_int(left)
        right_val = self._bits_to_unsigned_int(right)

        result = 32 * [0]
        if left_val < right_val:
            result[0] = 1

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set less than unsigned"

    def set_less_than_unsigned_or_equals(self):
        left = self._left.get()
        right = self._right.get()

        left_val = self._bits_to_unsigned_int(left)
        right_val = self._bits_to_unsigned_int(right)

        result = 32 * [0]
        if left_val <= right_val:
            result[0] = 1

        self._result = result
        self._off_top = 32 * [0]
        return f"{self._name} executing set less than unsigned"

    def sign_extend(self):
        imm = self._right.get()
        if len(imm) < 12:
            imm = [0] * (12 - len(imm)) + imm

        sign_bit = imm[11]

        result = imm.copy()
        for _ in range(12, 32):
            result.append(sign_bit)

        self._result = result[:32]
        self._off_top = 32 * [0]

    def sign_extend_byte(self):
        byte_val = self._left.get()
        if len(byte_val) < 8:
            byte_val = [0] * (8 - len(byte_val)) + byte_val

        sign_bit = byte_val[7]

        result = byte_val.copy()
        for _ in range(8, 32):
            result.append(sign_bit)

        self._result = result[:32]
        self._off_top = 32 * [0]

    def shift_left_12(self):

        imm = self._left.get()
        if len(imm) < 20:
            imm = [0] * (20 - len(imm)) + imm

        result = [0] * 12 + imm

        self._result = result[:32]
        self._off_top = 32 * [0]

    def get(self):
        return self._result.copy()

    def get_byte(self):
        return self._result[8:].copy()

    def _get_shift_amount(self):
        shift_val = self._right.get()
        shift = self._bits_to_unsigned_int(shift_val[:5]) if len(shift_val) >= 5 else self._bits_to_unsigned_int(
            shift_val)
        return shift % 32

    def _bits_to_int(self, bits):
        result = 0
        for i, bit in enumerate(bits):
            result |= bit << i
        return result

    def _bits_to_signed_int(self, bits):
        val = self._bits_to_unsigned_int(bits)
        if len(bits) == 32 and bits[31] == 1:
            val -= 1 << 32
        return val

    def _bits_to_unsigned_int(self, bits):
        result = 0
        for i, bit in enumerate(bits):
            if i < len(bits):
                result |= bit << i
        return result

    def _int_to_bits(self, num, size):
        bits = []
        for i in range(size):
            bits.append((num >> i) & 1)
        return bits

    def pass_value(self):
        self._result = self._left.get()
        return f"{self._name} is just passing value"

    def increment(self):
        left = self._left.get()
        right = [0, 0, 1, 0] + 28 * [0]
        off_top = 32 * [0]
        result = 32 * [0]

        result[0] = (left[0] + right[0]) % 2
        off_top[0] = (left[0] + right[0]) // 2

        for i in range(1, 32):
            sum = off_top[i - 1] + left[i] + right[i]
            result[i] = sum % 2
            off_top[i] = sum // 2

        self._result = result
        self._off_top = off_top
        return f"{self._name} executing increment by 4"

    def decrement(self):
        left = self._left.get()
        right = [0, 0, 1, 1] + 28 * [1]
        off_top = 32 * [0]
        result = 32 * [0]

        result[0] = (left[0] + right[0]) % 2
        off_top[0] = (left[0] + right[0]) // 2

        for i in range(1, 32):
            sum = off_top[i - 1] + left[i] + right[i]
            result[i] = sum % 2
            off_top[i] = sum // 2

        self._result = result
        self._off_top = off_top
        return f"{self._name} executing decrement by 4"
