import base64
import contextlib
import io
import os
import re
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator.forthcompiler import main as compile_main
from vm.vm import main as run_main


@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = os.path.join(tmpdir, "source.fs")
        input_file = os.path.join(tmpdir, "input.txt")
        bin_file = os.path.join(tmpdir, "program.bin")
        listing_file = os.path.join(tmpdir, "program.lst")

        with open(source_file, "w", encoding="utf-8") as f:
            f.write(golden["in_source"])
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(golden["in_stdin"])

        pc_from_yaml = golden.get("pc", None)
        log_level = str(golden.get("log_level", 3))

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            # 1. Компиляция
            compile_argv = ["forthcompiler.py", source_file, "-o", bin_file, "-l", listing_file]
            old_argv = sys.argv
            sys.argv = compile_argv
            try:
                compile_main()
            finally:
                sys.argv = old_argv

            output = stdout.getvalue()
            if pc_from_yaml is None or pc_from_yaml == "":
                match = re.search(r"Начало кода: (\d+) \(0x([0-9A-Fa-f]+)\)", output)
                pc = match.group(1) if match else "0x4040"
            else:
                pc = pc_from_yaml

            stdout.truncate(0)
            stdout.seek(0)

            run_argv = ["vm.py", bin_file, pc, "-i", input_file, "--log-level", log_level]
            sys.argv = run_argv
            try:
                run_main()
            finally:
                sys.argv = old_argv

        with open(bin_file, "rb") as f:
            binary_data = f.read()

        with open(listing_file, encoding="utf-8") as f:
            listing_data = f.read()

        log_file = bin_file[:-4] + "_log"
        with open(log_file, encoding="utf-8") as f:
            log_data = f.read()

        assert base64.b64encode(binary_data).decode() == golden.out["out_code_base64"]
        assert listing_data == golden.out["out_code"]
        assert stdout.getvalue() == golden.out["out_stdout"]
        assert log_data == golden.out["out_log"]
