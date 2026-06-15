import argparse
import struct
import sys


def tokenize(source: str) -> list[str]:
    tokens = []
    i = 0
    n = len(source)

    while i < n:
        c = source[i]

        if c.isspace():
            i += 1
            continue

        if c == "\\":
            i += 1
            while i < n and source[i] != "\n":
                i += 1
            continue

        if c == "(":
            i += 1
            depth = 1
            while i < n and depth > 0:
                if source[i] == "(":
                    depth += 1
                elif source[i] == ")":
                    depth -= 1
                i += 1
            continue

        if c == '"':
            i += 1
            start = i
            while i < n and source[i] != '"':
                i += 1
            if i < n:
                content = source[start:i]
                tokens.append('"' + content + '"')
                i += 1
            else:
                tokens.append('"' + source[start:])
            continue

        start = i
        while i < n and not source[i].isspace() and source[i] not in ("(", ")", '"', "\\"):
            i += 1
        token = source[start:i]
        tokens.append(token)

    return tokens


def bits(val, n):
    result = [(val >> (i)) & 1 for i in range(n)]
    return result


def signed_bits(val, n):

    if val < 0:
        val = (1 << n) + val
    return bits(val, n)


def make_r_type(funct3, funct7, rs1, rs2, rd):

    opcode = [0, 1, 1, 0, 0, 1, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = bits(funct3, 3)
    rs1_bits = bits(rs1, 5)
    rs2_bits = bits(rs2, 5)
    funct7_bits = bits(funct7, 7)
    return opcode + rd_bits + funct3_bits + rs1_bits + rs2_bits + funct7_bits


def make_i_type_arith(funct3, rs1, rd, imm):

    opcode = [0, 0, 1, 0, 0, 1, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = bits(funct3, 3)
    rs1_bits = bits(rs1, 5)
    imm_bits = signed_bits(imm, 12)
    return opcode + rd_bits + funct3_bits + rs1_bits + imm_bits


def make_i_type_shift(funct3, rs1, rd, shamt):
    opcode = [0, 0, 0, 0, 0, 1, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = bits(funct3, 3)
    rs1_bits = bits(rs1, 5)
    imm_bits = bits(shamt, 5) + [0] * 7
    return opcode + rd_bits + funct3_bits + rs1_bits + imm_bits


def make_load(funct3, rs1, rd, imm):

    opcode = [1, 1, 0, 0, 1, 1, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = bits(funct3, 3)
    rs1_bits = bits(rs1, 5)
    imm_bits = signed_bits(imm, 12)
    return opcode + rd_bits + funct3_bits + rs1_bits + imm_bits


def make_store(funct3, rs2, rs1, offset):
    opcode = [0, 1, 0, 0, 0, 1, 1]
    off = signed_bits(offset & 0xFFF, 12)
    bit12 = off[11]
    bit11 = off[10]
    bits_10_5 = off[5:10]
    bits_4_1 = off[0:5]
    return (
        opcode
        + bits_4_1
        + bits(funct3, 3)
        + bits(rs2, 5)
        + bits(rs1, 5)
        + bits_10_5
        + [bit11]
        + [bit12]
    )


def make_branch(funct3, rs1, rs2, offset):

    opcode = [1, 1, 0, 0, 0, 1, 1]
    off = signed_bits(offset & 0xFFF, 12)
    bit12 = off[11]
    bit11 = off[10]
    bits_10_5 = off[5:10]
    bits_4_1 = off[0:5]
    return (
        opcode
        + bits_4_1
        + bits(funct3, 3)
        + bits(rs1, 5)
        + bits(rs2, 5)
        + bits_10_5
        + [bit11]
        + [bit12]
    )


def make_jal(rd, offset):
    opcode = [1, 1, 0, 1, 1, 1, 1]
    rd_bits = bits(rd, 5)
    return opcode + rd_bits + signed_bits(offset, 20)


def make_lui(rd, offset):
    opcode = [0, 0, 0, 0, 0, 0, 0]
    rd_bits = bits(rd, 5)
    return opcode + rd_bits + signed_bits(offset, 20)


def make_jalr(rs1, rd, imm):
    opcode = [0, 0, 0, 1, 1, 1, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = [0, 0, 0]
    rs1_bits = bits(rs1, 5)
    imm_bits = signed_bits(imm, 12)
    return opcode + rd_bits + funct3_bits + rs1_bits + imm_bits


def make_jalri(rs1, rd, imm):
    opcode = [0, 0, 1, 1, 1, 1, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = [0, 0, 0]
    rs1_bits = bits(rs1, 5)
    imm_bits = signed_bits(imm, 12)
    return opcode + rd_bits + funct3_bits + rs1_bits + imm_bits


def make_print(rs1, rd):
    opcode = [1, 0, 0, 0, 0, 0, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = [0, 0, 1]
    rs1_bits = bits(rs1, 5)
    fill = 12 * [0]
    return opcode + rd_bits + funct3_bits + rs1_bits + fill


def make_print_word(rs1, rd):
    opcode = [1, 0, 0, 0, 0, 0, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = [0, 0, 0]
    rs1_bits = bits(rs1, 5)
    fill = 12 * [0]
    return opcode + rd_bits + funct3_bits + rs1_bits + fill


def make_input(rs1, rd):
    opcode = [0, 0, 0, 0, 0, 0, 1]
    rd_bits = bits(rd, 5)
    funct3_bits = [0, 0, 1]
    rs1_bits = bits(rs1, 5)
    fill = 12 * [0]
    return opcode + rd_bits + funct3_bits + rs1_bits + fill


def make_halt():
    return [1, 1, 1, 1, 1, 1, 1] + [0] * 25


class ForthCompiler:
    def __init__(self):
        self.var_labels = {}  # имя переменной -> адрес в области данных
        self.const_labels = {}  # имя переменной -> адрес в области данных
        self.proc_labels = {}  # имя процедуры -> адрес в области кода
        self.string_labels = {}  # строковый литерал -> адрес в области данных
        self.array_labels = {}
        self.over_all_name = {}  # имя -> тип ('var', 'proc', 'isr')
        self.label_addrs = {}  # внутренние метки -> адрес в коде

        self.reading_buff = []
        for _ in range(32):
            self.reading_buff.append(32 * [0])
        self.label_counter = 0
        self.data_code = [[0, 0, 1, 0] + 28 * [0]] + self.init_interrupt() + self.reading_buff
        self.data_addr = len(self.data_code) * 4
        self.prc_addr = 0
        self.proc_code = []
        self.all_code = []

    def init_interrupt(self):
        return (
            [make_input(0, 4)] + self.push_input(4) + self.pop_reg_addr(5) + [make_jalri(5, 4, 0)]
        )

    def push_reg(self, reg):
        return [make_i_type_arith(0, 30, 30, -4), make_store(2, 30, reg, 0)]

    def push_input(self, reg):
        return [
            make_store(0, 29, reg, 0),
            make_i_type_arith(0, 29, 29, 1),
            make_branch(4, 29, 27, 8),
            make_i_type_arith(0, 26, 29, 1),
        ]

    def pop_input(self, reg):
        return [
            make_load(0, 28, reg, 0),
            make_i_type_arith(0, 28, 28, 1),
            make_branch(4, 28, 26, 8),
            make_i_type_arith(0, 27, 28, -1),
        ]

    def pop_reg(self, reg):
        return [make_load(2, 30, reg, 0), make_i_type_arith(0, 30, 30, 4)]

    def push_reg_addr(self, reg):
        return [make_i_type_arith(0, 31, 31, -4), make_store(2, 31, reg, 0)]

    def pop_reg_addr(self, reg):
        return [make_load(2, 31, reg, 0), make_i_type_arith(0, 31, 31, 4)]

    def compile_push_reg_from_data(self):
        return self.pop_reg(1) + self.push_reg_addr(1)

    def compile_push_data_from_reg(self):
        return self.pop_reg_addr(1) + self.push_reg(1)

    def compile_literal(self, n):
        n = int(n)
        return (
            [make_lui(1, (n & 0xFFFFF000) >> 12)]
            + [make_i_type_shift(0, 1, 1, 12)]
            + [make_lui(2, (n & 0x00000FFF))]
            + [make_r_type(0, 0, 1, 2, 1)]
            + self.push_reg(1)
        )

    def compile_add(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(0, 0, 1, 2, 1)] + self.push_reg(1)

    def compile_sub(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(0, 2, 2, 1, 1)] + self.push_reg(1)

    def compile_mul(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(0, 1, 1, 2, 1)] + self.push_reg(1)

    def compile_div(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [(make_r_type(1, 1, 2, 1, 1))] + self.push_reg(1)

    def compile_mod(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [(make_r_type(3, 3, 2, 1, 1))] + self.push_reg(1)

    def compile_and(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [(make_r_type(7, 0, 1, 2, 1))] + self.push_reg(1)

    def compile_or(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [(make_r_type(3, 0, 1, 2, 1))] + self.push_reg(1)

    def compile_xor(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [(make_r_type(1, 0, 1, 2, 1))] + self.push_reg(1)

    def compile_not(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [(make_r_type(3, 1, 1, 2, 1))] + self.push_reg(1)

    def compile_dup(self):  # checked
        return [(make_load(2, 30, 1, 0))] + self.push_reg(1)

    def compile_dup_addr(self):
        return [(make_load(2, 31, 1, 0))] + self.push_reg_addr(1)

    def compile_drop(self):  # checked
        return [make_i_type_arith(0, 30, 30, 4)]

    def compile_swap(self):  # checked
        return [
            (make_load(2, 30, 1, 0)),
            (make_load(2, 30, 2, 4)),
            (make_store(2, 30, 2, 0)),
            (make_store(2, 30, 1, 4)),
        ]

    def compile_over(self):  # checked
        return [(make_load(2, 30, 1, 4))] + self.push_reg(1)

    def compile_rot(self):
        return (
            self.pop_reg(1)
            + self.pop_reg(2)
            + self.pop_reg(3)
            + self.push_reg(2)
            + self.push_reg(1)
            + self.push_reg(3)
        )

    def compile_fetch(self):  # checked
        return self.pop_reg(1) + [(make_load(2, 1, 1, 0))] + self.push_reg(1)

    def compile_store(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [(make_store(2, 1, 2, 0))]

    def compile_equals(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(2, 1, 1, 2, 1)] + self.push_reg(1)

    def compile_not_equals(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(2, 3, 1, 2, 1)] + self.push_reg(1)

    def compile_less(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(2, 0, 1, 2, 1)] + self.push_reg(1)

    def compile_more(self):  # checked
        return self.pop_reg(2) + self.pop_reg(1) + [make_r_type(2, 0, 1, 2, 1)] + self.push_reg(1)

    def compile_equals_or_more(self):  # checked
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(2, 7, 1, 2, 1)] + self.push_reg(1)

    def compile_equals_or_less(self):  # checked
        return self.pop_reg(2) + self.pop_reg(1) + [make_r_type(2, 7, 1, 2, 1)] + self.push_reg(1)

    def compile_begin_loop(self, result):
        size = len(result) * 4 + 8
        end = self.pop_reg(1) + [make_branch(0, 1, 0, -size)]
        return result + end

    def compile_if(self, if_part, else_part):  # checked
        if len(else_part) == 0:
            size = len(if_part) * 4 + 4
            start = self.pop_reg(1) + [make_branch(0, 1, 0, size)]
            return start + if_part
        else:
            else_part_size = len(else_part) * 4 + 4
            if_part += [make_jal(5, else_part_size)]
            if_part_size = len(if_part) * 4 + 4
            start = self.pop_reg(1) + [make_branch(0, 1, 0, if_part_size)]
            return start + if_part + else_part

    def compile_return(self):
        return [make_load(2, 31, 1, 0), make_i_type_arith(0, 31, 31, 4), make_jalr(1, 2, 0)]

    def compile_read(self):
        return [make_branch(0, 28, 29, 0)] + self.pop_input(1) + self.push_reg(1)

    def compile_call(self, offset):
        return [make_jal(1, offset)]

    def compile_unsigned_less(self):
        return self.pop_reg(1) + self.pop_reg(2) + [make_r_type(6, 0, 1, 2, 1)] + self.push_reg(1)

    def compile_unsigned_more(self):
        return self.pop_reg(2) + self.pop_reg(1) + [make_r_type(6, 0, 1, 2, 1)] + self.push_reg(1)

    def compile_proc_start(self):
        return self.push_reg_addr(1)

    def compile_do_loop(self, result):
        start = (
            self.compile_swap()
            + self.pop_reg(1)
            + self.push_reg_addr(1)
            + self.pop_reg(1)
            + self.push_reg_addr(1)
        )
        end = (
            self.pop_reg(1)
            + self.pop_reg_addr(2)
            + [make_r_type(0, 0, 1, 2, 1)]
            + self.pop_reg_addr(2)
        )
        end += (
            [make_branch(6, 1, 2, 24)]
            + self.push_reg_addr(2)
            + self.push_reg_addr(1)
            + [make_jal(0, -24 - len(result + end) * 4)]
        )
        return start + result + end

    def compile_print(self):
        return self.pop_reg(1) + [make_print(1, 0)]

    def compile_print_word(self):
        return self.pop_reg(1) + [make_print_word(1, 0)]

    def compile_input(self):
        return self.pop_reg(1) + [make_print(0, 1)]

    def compile_i(self):
        return self.compile_dup_addr() + self.pop_reg_addr(1) + self.push_reg(1)

    def string_to_32bit_blocks(self, text: str) -> list[list]:
        data = text.encode("utf-8") + b"\x00"
        result = []
        for char in data:
            code = char
            input_code = [code >> i & 1 for i in range(0, 8)]
            result += [input_code]
        while len(result) % 4 != 0:
            result += [8 * [0]]
        blocks = []
        for i in range(0, len(result), 4):
            blocks += [result[i] + result[i + 1] + result[i + 2] + result[i + 3]]
        return blocks

    def handle_variable(self, it):
        name = next(it)
        if name in self.over_all_name:
            raise SyntaxError(f"Переменная {name} уже определена")
        self.var_labels[name] = self.data_addr
        self.over_all_name[name] = "var"
        self.data_addr += 4
        self.data_code.append(32 * [0])

    def handle_constant(self, it):
        name = next(it)
        if name in self.over_all_name:
            raise SyntaxError(f"Константа {name} уже определена")
        self.const_labels[name] = self.data_addr
        self.over_all_name[name] = "const"
        self.data_addr += 4
        self.data_code.append(32 * [0])

    def handle_string(self, it):
        content = it[1:-1]
        if content not in self.string_labels:
            self.string_labels[content] = self.data_addr
            code = self.string_to_32bit_blocks(content)
            self.data_code += code
            self.data_addr += len(code) * 4
        return

    def handle_array(self, it):
        name = next(it)
        if name in self.over_all_name:
            raise SyntaxError(f"Имя {name} уже определено")
        size = next(it)
        if not self.is_number(size):
            raise SyntaxError("Длинна массива должна быть числом")
        size = int(size)
        self.array_labels[name] = self.data_addr
        self.over_all_name[name] = "array"
        self.data_addr += 4 * size
        for _ in range(size):
            self.data_code.append(32 * [0])

    def is_number(self, token):
        try:
            int(token)
            return True
        except ValueError:
            return False

    def first_pass(self, tokens):
        it = iter(tokens)
        while True:
            try:
                token = next(it)
            except StopIteration:
                break
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if token == "VARIABLE":
                self.handle_variable(it)
            elif token == "CONSTANT":
                self.handle_constant(it)
            elif token == "CREATE":
                self.handle_array(it)
            elif token.startswith('"') and token.endswith('"'):
                self.handle_string(token)
            else:
                pass
        self.proc_addr = self.data_addr

    def second_pass(self, tokens):
        it = iter(tokens)
        while True:
            try:
                token = next(it)
            except StopIteration:
                break
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if token == ":":
                self.handle_proc_definition(it)
            else:
                pass

    def handle_proc_definition(self, it):
        name = next(it)
        if name in self.over_all_name:
            raise SyntaxError(f"Имя {name} уже определено")
        self.proc_labels[name] = self.proc_addr
        self.over_all_name[name] = "proc"
        code = self.compile_proc_start() + self.handle_proc_body(it) + self.compile_return()
        self.proc_code += code
        self.proc_addr += len(code) * 4

    def handle_proc_body(self, it):
        result = []
        while True:
            try:
                token = next(it)
            except StopIteration:
                break
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if token == "VARIABLE":
                next(it)
                continue
            elif token == "CONSTANT":
                result += self.compile_const_definition(next(it))
            elif token == "CREATE":
                token = next(it)
                result += self.compile_literal(self.array_labels[token])
                token = next(it)
                result += self.compile_literal(token)
                continue
            elif token == ":":
                raise SyntaxError
            elif token == ";":
                return result
            elif token == "DUP":
                result += self.compile_dup()
            elif token == "SWAP":
                result += self.compile_swap()
            elif token == "DROP":
                result += self.compile_drop()
            elif token == "ROT":
                result += self.compile_rot()
            elif token == "OVER":
                result += self.compile_over()
            elif token == ">R":
                result += self.compile_push_reg_from_data()
            elif token == "R>":
                result += self.compile_push_data_from_reg()
            elif token == "@":
                result += self.compile_fetch()
            elif token == "!":
                result += self.compile_store()
            elif token == "+":
                result += self.compile_add()
            elif token == "-":
                result += self.compile_sub()
            elif token == "*":
                result += self.compile_mul()
            elif token == "/":
                result += self.compile_div()
            elif token == "%":
                result += self.compile_mod()
            elif token == "&":
                result += self.compile_and()
            elif token == "|":
                result += self.compile_or()
            elif token == "^":
                result += self.compile_xor()
            elif token == "%":
                result += self.compile_mod()
            elif token == "=":
                result += self.compile_equals()
            elif token == "!=":
                result += self.compile_not_equals()
            elif token == ">=":
                result += self.compile_equals_or_more()
            elif token == "<=":
                result += self.compile_equals_or_less()
            elif token == "<":
                result += self.compile_less()
            elif token == ">":
                result += self.compile_more()
            elif token == "U<":
                result += self.compile_unsigned_less()
            elif token == "U>":
                result += self.compile_unsigned_more()
            elif token == "not":
                result += self.compile_not()
            elif token == "emit":
                result += self.compile_print()
            elif token == ".":
                result += self.compile_print_word()
            elif token == "key":
                result += self.compile_read()
            elif self.is_number(token):
                result += self.compile_literal(token)
            elif token == "begin":
                result += self.compile_begin_loop(self.handle_begin_body(it))
            elif token == "do":
                result += self.compile_do_loop(self.handle_loop_do(it))
            elif token.startswith('"') and token.endswith('"'):
                result += self.compile_literal(self.string_labels[token[1:-1]])
            elif token == "if":
                if_part, else_part = self.handle_if_body(it)
                result += self.compile_if(if_part, else_part)
            elif token == "'":
                result += self.compile_tick(next(it))
            elif token == "execute":
                result += self.compile_execute()
            else:
                if token in self.over_all_name:
                    if self.over_all_name[token] == "proc":
                        result += [token]
                    elif self.over_all_name[token] == "array":
                        result += self.compile_literal(self.array_labels[token])
                    elif self.over_all_name[token] == "var":
                        result += self.compile_literal(self.var_labels[token])
                    elif self.over_all_name[token] == "const":
                        result += self.compile_literal(self.const_labels[token])
                    else:
                        raise SyntaxError
                else:
                    raise SyntaxError

    def handle_if_body(self, it, is_loop=False):
        result = []
        while True:
            try:
                token = next(it)
            except StopIteration:
                raise SyntaxError("NO END FOR IF") from None
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if (
                token == "VARIABLE"
                or token == "CONSTANT"
                or token == "CREATE"
                or token.startswith('"')
                and token.endswith('"')
                or token == ":"
                or token == ";"
            ):
                raise SyntaxError("DO DEF IN IF")
            elif token == "DUP":
                result += self.compile_dup()
            elif token == "SWAP":
                result += self.compile_swap()
            elif token == "DROP":
                result += self.compile_drop()
            elif token == "ROT":
                result += self.compile_rot()
            elif token == "OVER":
                result += self.compile_over()
            elif token == ">R":
                result += self.compile_push_reg_from_data()
            elif token == "R>":
                result += self.compile_push_data_from_reg()
            elif token == "@":
                result += self.compile_fetch()
            elif token == "!":
                result += self.compile_store()
            elif token == "+":
                result += self.compile_add()
            elif token == "-":
                result += self.compile_sub()
            elif token == "*":
                result += self.compile_mul()
            elif token == "/":
                result += self.compile_div()
            elif token == "%":
                result += self.compile_mod()
            elif token == "&":
                result += self.compile_and()
            elif token == "|":
                result += self.compile_or()
            elif token == "^":
                result += self.compile_xor()
            elif token == "%":
                result += self.compile_mod()
            elif token == "=":
                result += self.compile_equals()
            elif token == "!=":
                result += self.compile_not_equals()
            elif token == ">=":
                result += self.compile_equals_or_more()
            elif token == "<=":
                result += self.compile_equals_or_less()
            elif token == "<":
                result += self.compile_less()
            elif token == ">":
                result += self.compile_more()
            elif token == "U<":
                result += self.compile_unsigned_less()
            elif token == "U>":
                result += self.compile_unsigned_more()
            elif token == "not":
                result += self.compile_not()
            elif token == "emit":
                result += self.compile_print()
            elif token == ".":
                result += self.compile_print_word()
            elif token == "key":
                result += self.compile_read()
            elif token == "begin":
                result += self.compile_begin_loop(self.handle_begin_body(it, is_loop))
            elif token == "do":
                result += self.compile_do_loop(self.handle_loop_do(it, is_loop))
            elif token == "I" and is_loop:
                result += self.compile_i()
            elif self.is_number(token):
                result += self.compile_literal(token)
            elif token == "if":
                if_part, else_part = self.handle_if_body(it, is_loop)
                result += self.compile_if(if_part, else_part)
            elif token == "else":
                return [result, self.handle_else_body(it, is_loop)]
            elif token == "then":
                return [result, []]
            elif token == "'":
                result += self.compile_tick(next(it))
            elif token == "execute":
                result += self.compile_execute()
            else:
                if token in self.over_all_name:
                    if self.over_all_name[token] == "proc":
                        result += [token]
                    elif self.over_all_name[token] == "array":
                        result += self.compile_literal(self.array_labels[token])
                    elif self.over_all_name[token] == "var":
                        result += self.compile_literal(self.var_labels[token])
                    elif self.over_all_name[token] == "const":
                        result += self.compile_literal(self.const_labels[token])
                    else:
                        raise SyntaxError
                else:
                    raise SyntaxError

    def handle_else_body(self, it, is_loop=False):
        result = []
        while True:
            try:
                token = next(it)
            except StopIteration:
                raise SyntaxError("NO END FOR IF") from None
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if (
                token == "VARIABLE"
                or token == "CONSTANT"
                or token == "CREATE"
                or token.startswith('"')
                and token.endswith('"')
                or token == ":"
                or token == ";"
            ):
                raise SyntaxError("NO DEF IN IF")
            elif token == "DUP":
                result += self.compile_dup()
            elif token == "SWAP":
                result += self.compile_swap()
            elif token == "DROP":
                result += self.compile_drop()
            elif token == "ROT":
                result += self.compile_rot()
            elif token == "OVER":
                result += self.compile_over()
            elif token == ">R":
                result += self.compile_push_reg_from_data()
            elif token == "R>":
                result += self.compile_push_data_from_reg()
            elif token == "@":
                result += self.compile_fetch()
            elif token == "!":
                result += self.compile_store()
            elif token == "+":
                result += self.compile_add()
            elif token == "-":
                result += self.compile_sub()
            elif token == "*":
                result += self.compile_mul()
            elif token == "/":
                result += self.compile_div()
            elif token == "%":
                result += self.compile_mod()
            elif token == "&":
                result += self.compile_and()
            elif token == "|":
                result += self.compile_or()
            elif token == "^":
                result += self.compile_xor()
            elif token == "%":
                result += self.compile_mod()
            elif token == "=":
                result += self.compile_equals()
            elif token == "!=":
                result += self.compile_not_equals()
            elif token == ">=":
                result += self.compile_equals_or_more()
            elif token == "<=":
                result += self.compile_equals_or_less()
            elif token == "<":
                result += self.compile_less()
            elif token == ">":
                result += self.compile_more()
            elif token == "U<":
                result += self.compile_unsigned_less()
            elif token == "U>":
                result += self.compile_unsigned_more()
            elif token == "not":
                result += self.compile_not()
            elif token == "begin":
                result += self.compile_begin_loop(self.handle_begin_body(it, is_loop))
            elif token == "do":
                result += self.compile_do_loop(self.handle_loop_do(it, is_loop))
            elif token == "I" and is_loop:
                result += self.compile_i()
            elif token == "emit":
                result += self.compile_print()
            elif token == ".":
                result += self.compile_print_word()
            elif token == "key":
                result += self.compile_read()
            elif self.is_number(token):
                result += self.compile_literal(token)
            elif token == "if":
                if_part, else_part = self.handle_if_body(it, is_loop)
                result += self.compile_if(if_part, else_part)
            elif token == "else":
                raise SyntaxError
            elif token == "then":
                return result
            elif token == "'":
                result += self.compile_tick(next(it))
            elif token == "execute":
                result += self.compile_execute()
            else:
                if token in self.over_all_name:
                    if self.over_all_name[token] == "proc":
                        result += [token]
                    elif self.over_all_name[token] == "array":
                        result += self.compile_literal(self.array_labels[token])
                    elif self.over_all_name[token] == "var":
                        result += self.compile_literal(self.var_labels[token])
                    elif self.over_all_name[token] == "const":
                        result += self.compile_literal(self.const_labels[token])
                    else:
                        raise SyntaxError
                else:
                    raise SyntaxError

    def handle_begin_body(self, it, is_loop=False):
        result = []
        while True:
            try:
                token = next(it)
            except StopIteration:
                raise SyntaxError("NO END FOR LOOP") from None
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if token == "VARIABLE" or token == "CONSTANT" or token == "CREATE":
                raise SyntaxError
            elif token.startswith('"') and token.endswith('"'):
                result += self.compile_literal(self.string_labels[token[1:-1]])
            elif token == ":" or token == ";":
                raise SyntaxError
            elif token == "DUP":
                result += self.compile_dup()
            elif token == "SWAP":
                result += self.compile_swap()
            elif token == "DROP":
                result += self.compile_drop()
            elif token == "ROT":
                result += self.compile_rot()
            elif token == "OVER":
                result += self.compile_over()
            elif token == ">R":
                result += self.compile_push_reg_from_data()
            elif token == "R>":
                result += self.compile_push_data_from_reg()
            elif token == "@":
                result += self.compile_fetch()
            elif token == "!":
                result += self.compile_store()
            elif token == "+":
                result += self.compile_add()
            elif token == "-":
                result += self.compile_sub()
            elif token == "*":
                result += self.compile_mul()
            elif token == "/":
                result += self.compile_div()
            elif token == "%":
                result += self.compile_mod()
            elif token == "&":
                result += self.compile_and()
            elif token == "|":
                result += self.compile_or()
            elif token == "^":
                result += self.compile_xor()
            elif token == "%":
                result += self.compile_mod()
            elif token == "=":
                result += self.compile_equals()
            elif token == "!=":
                result += self.compile_not_equals()
            elif token == ">=":
                result += self.compile_equals_or_more()
            elif token == "<=":
                result += self.compile_equals_or_less()
            elif token == "<":
                result += self.compile_less()
            elif token == ">":
                result += self.compile_more()
            elif token == "U<":
                result += self.compile_unsigned_less()
            elif token == "U>":
                result += self.compile_unsigned_more()
            elif token == "not":
                result += self.compile_not()
            elif token == "emit":
                result += self.compile_print()
            elif token == ".":
                result += self.compile_print_word()
            elif token == "key":
                result += self.compile_read()
            elif token == "begin":
                result += self.compile_begin_loop(self.handle_begin_body(it, is_loop))
            elif token == "do":
                result += self.compile_do_loop(self.handle_loop_do(it, is_loop))
            elif token == "I" and is_loop:
                result += self.compile_i()
            elif self.is_number(token):
                result += self.compile_literal(token)
            elif token == "if":
                if_part, else_part = self.handle_if_body(it, is_loop)
                result += self.compile_if(if_part, else_part)
            elif token == "until":
                return result
            elif token == "'":
                result += self.compile_tick(next(it))
            elif token == "execute":
                result += self.compile_execute()
            else:
                if token in self.over_all_name:
                    if self.over_all_name[token] == "proc":
                        result += [token]
                    elif self.over_all_name[token] == "array":
                        result += self.compile_literal(self.array_labels[token])
                    elif self.over_all_name[token] == "var":
                        result += self.compile_literal(self.var_labels[token])
                    elif self.over_all_name[token] == "const":
                        result += self.compile_literal(self.const_labels[token])
                    else:
                        raise SyntaxError
                else:
                    raise SyntaxError

    def compile_const_definition(self, name):
        return self.compile_literal(self.const_labels[name]) + self.compile_store()

    def compile_execute(self):
        return [make_load(2, 30, 2, 0), make_i_type_arith(0, 30, 30, 4), make_jalr(2, 1, 0)]

    def compile_tick(self, name):
        return self.compile_literal(self.proc_labels[name])

    def compile_const(self, name):
        return self.compile_literal(self.const_labels[name]) + self.compile_fetch()

    def handle_loop_do(self, it, is_loop=True):
        result = []
        while True:
            try:
                token = next(it)
            except StopIteration:
                raise SyntaxError("NO END FOR LOOP") from None
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if token == "VARIABLE" or token == "CONSTANT" or token == "CREATE":
                raise SyntaxError("NO DEF IN LOOPS")
            elif token.startswith('"') and token.endswith('"'):
                result += self.compile_literal(self.string_labels[token[1:-1]])
            elif token == ":" or token == ";":
                raise SyntaxError("NO DEF IN LOOPS")
            elif token == "DUP":
                result += self.compile_dup()
            elif token == "SWAP":
                result += self.compile_swap()
            elif token == "DROP":
                result += self.compile_drop()
            elif token == "ROT":
                result += self.compile_rot()
            elif token == "OVER":
                result += self.compile_over()
            elif token == ">R":
                result += self.compile_push_reg_from_data()
            elif token == "R>":
                result += self.compile_push_data_from_reg()
            elif token == "@":
                result += self.compile_fetch()
            elif token == "!":
                result += self.compile_store()
            elif token == "+":
                result += self.compile_add()
            elif token == "*":
                result += self.compile_mul()
            elif token == "/":
                result += self.compile_div()
            elif token == "%":
                result += self.compile_mod()
            elif token == "&":
                result += self.compile_and()
            elif token == "|":
                result += self.compile_or()
            elif token == "^":
                result += self.compile_xor()
            elif token == "%":
                result += self.compile_mod()
            elif token == "=":
                result += self.compile_equals()
            elif token == "!=":
                result += self.compile_not_equals()
            elif token == ">=":
                result += self.compile_equals_or_more()
            elif token == "<=":
                result += self.compile_equals_or_less()
            elif token == "<":
                result += self.compile_less()
            elif token == ">":
                result += self.compile_more()
            elif token == "U<":
                result += self.compile_unsigned_less()
            elif token == "U>":
                result += self.compile_unsigned_more()
            elif token == "not":
                result += self.compile_not()
            elif token == "emit":
                result += self.compile_print()
            elif token == ".":
                result += self.compile_print_word()
            elif token == "key":
                result += self.compile_read()
            elif token == "begin":
                result += self.compile_begin_loop(self.handle_begin_body(it, is_loop))
            elif token == "do":
                result += self.compile_do_loop(self.handle_loop_do(it, is_loop))
            elif token == "loop":
                return result
            elif token == "'":
                result += self.compile_tick(next(it))
            elif token == "execute":
                result += self.compile_execute()
            elif token == "I" and is_loop:
                result += self.compile_i()
            elif self.is_number(token):
                result += self.compile_literal(token)
            elif token == "if":
                if_part, else_part = self.handle_if_body(it, is_loop)
                result += self.compile_if(if_part, else_part)
            elif token == "loop":
                return result
            else:
                if token in self.over_all_name:
                    if self.over_all_name[token] == "proc":
                        result += [token]
                    elif self.over_all_name[token] == "array":
                        result += self.compile_literal(self.array_labels[token])
                    elif self.over_all_name[token] == "var":
                        result += self.compile_literal(self.var_labels[token])
                    elif self.over_all_name[token] == "const":
                        result += self.compile_const(token)
                    else:
                        raise SyntaxError

    def third_pass(self, it):
        result = []
        while True:
            try:
                token = next(it)
            except StopIteration:
                break
            if not token or token.startswith("(") or token.startswith("\\"):
                continue
            if token == "VARIABLE":
                next(it)
                continue
            elif token == "CONSTANT":
                result += self.compile_const_definition(next(it))
            elif token == "CREATE":
                token = next(it)
                result += self.compile_literal(self.array_labels[token])
                token = next(it)
                result += self.compile_literal(token)
                continue
            elif token == ":":
                while token != ";":
                    token = next(it)
                continue
            elif token == "DUP":
                result += self.compile_dup()
            elif token == "SWAP":
                result += self.compile_swap()
            elif token == "DROP":
                result += self.compile_drop()
            elif token == "ROT":
                result += self.compile_rot()
            elif token == "OVER":
                result += self.compile_over()
            elif token == ">R":
                result += self.compile_push_reg_from_data()
            elif token == "R>":
                result += self.compile_push_data_from_reg()
            elif token == "@":
                result += self.compile_fetch()
            elif token == "!":
                result += self.compile_store()
            elif token == "+":
                result += self.compile_add()
            elif token == "-":
                result += self.compile_sub()
            elif token == "*":
                result += self.compile_mul()
            elif token == "/":
                result += self.compile_div()
            elif token == "%":
                result += self.compile_mod()
            elif token == "&":
                result += self.compile_and()
            elif token == "|":
                result += self.compile_or()
            elif token == "^":
                result += self.compile_xor()
            elif token == "%":
                result += self.compile_mod()
            elif token == "=":
                result += self.compile_equals()
            elif token == "!=":
                result += self.compile_not_equals()
            elif token == ">=":
                result += self.compile_equals_or_more()
            elif token == "<=":
                result += self.compile_equals_or_less()
            elif token == "<":
                result += self.compile_less()
            elif token == ">":
                result += self.compile_more()
            elif token == "U<":
                result += self.compile_unsigned_less()
            elif token == "U>":
                result += self.compile_unsigned_more()
            elif token == "not":
                result += self.compile_not()
            elif token == "emit":
                result += self.compile_print()
            elif token == ".":
                result += self.compile_print_word()
            elif token == "key":
                result += self.compile_read()
            elif self.is_number(token):
                result += self.compile_literal(token)
            elif token == "'":
                result += self.compile_tick(next(it))
            elif token == "execute":
                result += self.compile_execute()
            elif token == "begin":
                result += self.compile_begin_loop(self.handle_begin_body(it))
            elif token == "do":
                result += self.compile_do_loop(self.handle_loop_do(it, True))
            elif token.startswith('"') and token.endswith('"'):
                result += self.compile_literal(self.string_labels[token[1:-1]])
            elif token == "if":
                if_part, else_part = self.handle_if_body(it)
                result += self.compile_if(if_part, else_part)
            else:
                if token in self.over_all_name:
                    if self.over_all_name[token] == "proc":
                        result += [token]
                    elif self.over_all_name[token] == "array":
                        result += self.compile_literal(self.array_labels[token])
                    elif self.over_all_name[token] == "var":
                        result += self.compile_literal(self.var_labels[token])
                    elif self.over_all_name[token] == "const":
                        result += self.compile_const(token)
                    else:
                        raise SyntaxError
                else:
                    raise SyntaxError
        return result + [make_halt()]

    def fourth_pass(self, data):
        for i in range(len(data)):
            inst = data[i]
            if isinstance(inst, str):
                data[i] = self.compile_call(self.proc_labels[inst] - i * 4)[0]

    def disassemble(self, instr: int) -> str:

        opcode = instr & 0x7F
        rd = (instr >> 7) & 0x1F
        funct3 = (instr >> 12) & 0x7
        rs1 = (instr >> 15) & 0x1F
        rs2 = (instr >> 20) & 0x1F
        funct7 = (instr >> 25) & 0x7F

        if opcode == 0x41:
            if funct3 == 0x04:
                return f"print x{rd}"
            elif funct3 == 0x00:
                return f"print_word x{rd}"
        if opcode == 0x40 and funct3 == 0x04:
            return f"input x{rd}"
        if opcode == 0x7F and (instr >> 7) == 0:
            return "halt"

        if opcode == 0x7C:
            imm = (instr >> 20) & 0xFFF
            if imm & 0x800:
                imm -= 0x1000
            return f"jalri x{rd}, x{rs1}, {imm}"

        # R
        if opcode == 0x66:
            if funct3 == 0x00:
                if funct7 == 0x00:
                    return f"add x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x02:
                    return f"sub x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x01:
                    return f"mul x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x07 and funct3 == 0x00:
                return f"and x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x03:
                if funct7 == 0x00:
                    return f"or x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x01:
                    return f"not x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x02:
                    return f"rem x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x05:
                if funct7 == 0x00:
                    return f"srl x{rd}, x{rs1}, x{rs2}"
                if funct3 == 0x02:
                    return f"sra x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x06 and funct7 == 0x00:
                return f"sltu x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x01:
                if funct7 == 0x00:
                    return f"xor x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x01:
                    return f"div x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x04:
                if funct7 == 0x00:
                    return f"mulh x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x40:
                    return f"sll x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x02:
                if funct7 == 0x00:
                    return f"slt x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x01:
                    return f"seq x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x03:
                    return f"sne x{rd}, x{rs1}, x{rs2}"
                if funct7 == 0x07:
                    return f"seqm x{rd}, x{rs1}, x{rs2}"
            if funct3 == 0x07 and funct7 == 0x00:
                return f"and x{rd}, x{rs1}, x{rs2}"
            return f"r-type f7={funct7:x} f3={funct3}"

        if opcode == 0x00:
            imm = (instr >> 12) & 0xFFFFF
            return f"lui x{rd}, 0x{imm:x}"

        if opcode == 0x64:
            imm = (instr >> 20) & 0xFFF
            if imm & 0x800:
                imm -= 0x1000
            if funct3 == 0x00:
                return f"addi x{rd}, x{rs1}, {imm}"
            if funct3 == 0x02:
                return f"slti x{rd}, x{rs1}, {imm}"
            if funct3 == 0x01:
                return f"xori x{rd}, x{rs1}, {imm}"
            if funct3 == 0x07:
                return f"andi x{rd}, x{rs1}, {imm}"
            if funct3 == 0x03:
                return f"ori  x{rd}, x{rs1}, {imm}"

        if opcode == 0x60:
            shamt = (instr >> 20) & 0x1F
            if funct3 == 0x00:
                return f"slli x{rd}, x{rs1}, {shamt}"
            if funct3 == 0x01:
                return f"srli x{rd}, x{rs1}, {shamt}"
            if funct3 == 0x02:
                return f"srai x{rd}, x{rs1}, {shamt}"
            return f"shift-imm f3={funct3}"

        if opcode == 0x73:
            imm = (instr >> 20) & 0xFFF
            if imm & 0x800:
                imm -= 0x1000
            if funct3 == 0x00:
                return f"lb  x{rd}, {imm}(x{rs1})"
            if funct3 == 0x02:
                return f"lw  x{rd}, {imm}(x{rs1})"

        if opcode == 0x62:
            imm_lo = (instr >> 7) & 0x1F
            imm_hi = (instr >> 25) & 0x1F
            bit11 = (instr >> 30) & 1
            bit12 = (instr >> 31) & 1
            imm = imm_lo | (imm_hi << 5) | (bit11 << 10) | (bit12 << 11)
            if imm & 0x800:
                imm -= 0x1000
            if funct3 == 0x00:
                return f"sb x{rs2}, {imm}(x{rs1})"
            if funct3 == 0x02:
                return f"sw x{rs2}, {imm}(x{rs1})"

        if opcode == 0x63:
            imm_lo = (instr >> 7) & 0x1F
            imm_hi = (instr >> 25) & 0x1F
            bit11 = (instr >> 30) & 1
            bit12 = (instr >> 31) & 1
            imm = imm_lo | (imm_hi << 5) | (bit11 << 10) | (bit12 << 11)
            if imm & 0x800:
                imm -= 0x1000
            if funct3 == 0x00:
                return f"beq  x{rs1}, x{rs2}, {imm}"
            if funct3 == 0x01:
                return f"bne  x{rs1}, x{rs2}, {imm}"
            if funct3 == 0x04:
                return f"bgt  x{rs1}, x{rs2}, {imm}"
            if funct3 == 0x03:
                return f"bge  x{rs1}, x{rs2}, {imm}"
            if funct3 == 0x02:
                return f"blt  x{rs1}, x{rs2}, {imm}"
            if funct3 == 0x05:
                return f"ble  x{rs1}, x{rs2}, {imm}"
            if funct3 == 0x06:
                return f"bltu x{rs1}, x{rs2}, {imm}"
            if funct3 == 0x07:
                return f"bltue x{rs1}, x{rs2}, {imm}"

        if opcode == 0x7B:
            imm = (instr >> 12) & 0xFFFFF
            if imm & 0x100000:
                imm -= 0x200000
            return f"jal x{rd}, {imm}"

        if opcode == 0x78:
            imm = (instr >> 20) & 0xFFF
            if imm & 0x800:
                imm -= 0x1000
            return f"jalr x{rd}, x{rs1}, {imm}"

        if opcode == 0x7C:
            imm = (instr >> 20) & 0xFFF
            if imm & 0x800:
                imm -= 0x1000
            return f"jalri x{rd}, x{rs1}, {imm}"

        return "data"

    def generate_listing(self, start_addr: int, filename: str):

        with open(filename, "w", encoding="utf-8") as f:
            for i, inst in enumerate(self.all_code):
                addr = start_addr + i * 4
                if isinstance(inst, list):
                    word = bits_to_int(inst)
                elif isinstance(inst, str):
                    f.write(f"{addr} - ???? - <{inst}>\n")
                    continue
                else:
                    word = inst
                hex_str = f"{word:08X}"
                mnemonic = self.disassemble(word)
                f.write(f"{addr} - {hex_str} - {mnemonic}\n")

    def compile_all(self, file):
        with open(file) as f:
            it = tokenize(f.read())
        self.first_pass(it.copy())
        self.second_pass(it.copy())
        self.all_code = self.data_code + self.proc_code + self.third_pass(iter(it))
        self.fourth_pass(self.all_code)
        return self.proc_addr, self.all_code.copy()


def bits_to_int(bits: list[int]) -> int:
    value = 0
    for i, bit in enumerate(bits):
        if bit:
            value |= 1 << i
    return value


def write_binary(code, filename: str):
    with open(filename, "wb") as f:
        for instr in code:
            if isinstance(instr, list):
                word = bits_to_int(instr)
            elif isinstance(instr, int):
                word = instr
            else:
                raise TypeError(f"Неизвестный тип инструкции: {type(instr)}")
            f.write(struct.pack("<I", word))


def write_text(code, filename: str):
    with open(filename, "w") as f:
        for instr in code:
            if isinstance(instr, list):
                word = bits_to_int(instr)
            elif isinstance(instr, int):
                word = instr
            else:
                word = 0
            f.write(f"{word:08x}\n")


def main():
    parser = argparse.ArgumentParser(description="Компилятор Forth -> RISC-V машинный код")
    parser.add_argument("input", help="Входной файл с исходным кодом")
    parser.add_argument(
        "-o", "--output-bin", default=None, help="Выходной бинарный файл (по умолчанию input.bin)"
    )
    parser.add_argument(
        "-l", "--listing", default=None, help="Файл листинга (по умолчанию input.lst)"
    )
    parser.add_argument(
        "--format",
        choices=["binary", "text"],
        default="binary",
        help="Формат выходного файла (только для совместимости, лучше использовать -o)",
    )

    args = parser.parse_args()

    base = args.input.rsplit(".", 1)[0]
    bin_filename = args.output_bin if args.output_bin else f"{base}.bin"
    lst_filename = args.listing if args.listing else f"{base}.lst"

    try:
        compiler = ForthCompiler()
        start_addr, code = compiler.compile_all(args.input)
        print(
            f"Компиляция завершена. Начало кода: {start_addr} (0x{start_addr:X}), размер: {len(code)} инструкций"
        )

        # Сохраняем бинарный файл
        with open(bin_filename, "wb") as f:
            for instr in code:
                word = bits_to_int(instr) if isinstance(instr, list) else instr
                f.write(struct.pack("<I", word))
        print(f"Бинарный файл сохранён: {bin_filename}")

        # Генерируем листинг
        compiler.generate_listing(0, lst_filename)
        print(f"Листинг сохранён: {lst_filename}")

    except SyntaxError as e:
        print(f"Ошибка синтаксиса: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Файл {args.input} не найден", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Неизвестная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
