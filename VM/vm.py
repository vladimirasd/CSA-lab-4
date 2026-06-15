import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from VM.CPU import CPU


def big_to_bits(n):
    return (
        [n >> i & 1 for i in range(0, 8)],
        [n >> i & 1 for i in range(8, 16)],
        [n >> i & 1 for i in range(16, 24)],
        [n >> i & 1 for i in range(24, 32)],
    )


def to_bits(n):
    return [n >> i & 1 for i in range(0, 8)]


def run_vm(bin_file, pc, input_file=None):
    actual_pc = []
    for i in bin(pc)[2:]:
        actual_pc.append(int(i))
    actual_pc.reverse()
    for _ in range(len(actual_pc), 32):
        actual_pc += [0]
    with open(bin_file[:-4] + "_log", "w", encoding="utf-8") as log_file:
        cpu = CPU(
            bin_file,
            actual_pc,
            input_file,
            log_file,
        )

        try:
            cpu.run()
        except ValueError:
            print()

        output = cpu._o0._output_queue
        print("==========OUTPUT==========", file=log_file)
        for byte in output:
            if len(byte) == 8:
                char_code = 0
                for i in range(0, 8):
                    char_code += byte[i] << i
                print(chr(char_code), end="", file=log_file)
            else:
                result = 0
                for i in range(0, 32):
                    result += byte[i] << i
                print(result, file=log_file)


def main():
    parser = argparse.ArgumentParser(
        description="Запуск виртуальной машины RISC‑V с загрузкой бинарного файла."
    )
    parser.add_argument("bin_file", help="Путь к бинарному файлу (машинный код)")
    parser.add_argument(
        "pc", help="Начальное значение программного счётчика (десятичное или hex, например 0x4040)"
    )
    parser.add_argument(
        "-i", "--input", dest="input_file", help="Файл для ввода данных (по умолчанию None)"
    )
    parser.add_argument(
        "--log-level", type=int, choices=[1, 2, 3], default=0,
        help="Уровень детализации логирования: 1 — только ошибки, 2 — важные события, 3 — полная трассировка (по умолчанию 0 — логи отключены)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.bin_file):
        print(f"Ошибка: файл {args.bin_file} не найден.", file=sys.stderr)
        sys.exit(1)

    try:
        pc = int(args.pc, 0)
    except ValueError:
        print(
            f"Ошибка: неверный формат pc '{args.pc}'. Используйте десятичное или шестнадцатеричное число (например, 16448 или 0x4040).",
            file=sys.stderr,
        )
        sys.exit(1)

    run_vm(args.bin_file, pc, args.input_file, args.log_level)


if __name__ == "__main__":
    main()
