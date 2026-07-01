import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ObjectSizeRunnerTests(unittest.TestCase):
    def test_parses_standard_llvm_size_output(self):
        from ecpor.object_size_runner import parse_llvm_size_output

        parsed = parse_llvm_size_output(
            "   text    data     bss     dec     hex filename\n"
            "    123       4       8     135      87 tiny.o\n"
        )

        self.assertEqual(parsed, (123, 4, 8, 135))

    def test_parser_handles_crlf_warning_lines_and_hex_numbers(self):
        from ecpor.object_size_runner import parse_llvm_size_output

        parsed = parse_llvm_size_output(
            "warning: ignored section\r\n"
            "   text    data     bss     dec     hex filename\r\n"
            "   0x10     0x4       0    0x14      14 tiny.o\r\n"
        )

        self.assertEqual(parsed, (16, 4, 0, 20))

    def test_parser_returns_none_for_empty_or_header_only_output(self):
        from ecpor.object_size_runner import parse_llvm_size_output

        self.assertIsNone(parse_llvm_size_output(""))
        self.assertIsNone(
            parse_llvm_size_output("text data bss dec hex filename\n")
        )

    def test_compile_and_measure_object_size(self):
        from ecpor.object_size_runner import measure_object_size

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_ir = tmp_path / "input.ll"
            output_obj = tmp_path / "input.o"
            input_ir.write_text("define void @f() { ret void }\n", encoding="utf-8")
            fake_llc = _write_fake_llc(tmp_path)
            fake_size = _write_fake_size(tmp_path)

            record = measure_object_size(
                program="tiny",
                candidate_id="tiny__anchor",
                ir_path=input_ir,
                object_path=output_obj,
                llc_path=[sys.executable, str(fake_llc)],
                llvm_size_path=[sys.executable, str(fake_size)],
            )

        self.assertEqual(record.program, "tiny")
        self.assertEqual(record.candidate_id, "tiny__anchor")
        self.assertEqual(record.compile_exit_code, 0)
        self.assertIsNone(record.compile_failure_kind)
        self.assertEqual(record.size_exit_code, 0)
        self.assertIsNone(record.size_failure_kind)
        self.assertEqual(record.text_size, 123)
        self.assertEqual(record.data_size, 4)
        self.assertEqual(record.bss_size, 8)
        self.assertEqual(record.total_size, 135)

    def test_size_parse_failure_is_explicit(self):
        from ecpor.object_size_runner import measure_object_size

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_ir = tmp_path / "input.ll"
            output_obj = tmp_path / "input.o"
            input_ir.write_text("define void @f() { ret void }\n", encoding="utf-8")
            fake_llc = _write_fake_llc(tmp_path)
            fake_size = tmp_path / "fake_size.py"
            fake_size.write_text("print('not size output')\n", encoding="utf-8")

            record = measure_object_size(
                program="tiny",
                candidate_id="tiny__anchor",
                ir_path=input_ir,
                object_path=output_obj,
                llc_path=[sys.executable, str(fake_llc)],
                llvm_size_path=[sys.executable, str(fake_size)],
            )

        self.assertEqual(record.size_failure_kind, "size_parse_failed")
        self.assertIsNone(record.text_size)
        self.assertIsNone(record.total_size)


def _write_fake_llc(tmp_path: Path) -> Path:
    fake_llc = tmp_path / "fake_llc.py"
    fake_llc.write_text(
        textwrap.dedent(
            """
            import pathlib
            import sys

            output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
            output.write_bytes(b"fake object")
            """
        ).strip(),
        encoding="utf-8",
    )
    return fake_llc


def _write_fake_size(tmp_path: Path) -> Path:
    fake_size = tmp_path / "fake_size.py"
    fake_size.write_text(
        "print('   text    data     bss     dec     hex filename')\n"
        "print('    123       4       8     135      87 tiny.o')\n",
        encoding="utf-8",
    )
    return fake_size


if __name__ == "__main__":
    unittest.main()
