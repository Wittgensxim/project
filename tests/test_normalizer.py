import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class NormalizerTests(unittest.TestCase):
    def test_hard_canonicalize_normalizes_newlines_and_trailing_newline(self):
        from ecpor.normalizer import hard_canonicalize

        self.assertEqual(hard_canonicalize("define void @f() {\r\n  ret void\r\n}"), "define void @f() {\n  ret void\n}\n")

    def test_hard_hash_text_is_stable_across_newline_styles(self):
        from ecpor.normalizer import hard_hash_text

        lhs = "define void @f() {\r\n  ret void\r\n}\r\n"
        rhs = "define void @f() {\n  ret void\n}\n"

        self.assertEqual(hard_hash_text(lhs), hard_hash_text(rhs))

    def test_hard_hash_text_preserves_optimization_metadata(self):
        from ecpor.normalizer import hard_hash_text

        with_metadata = "define void @f() !prof !0 {\n  ret void\n}\n!0 = !{!\"branch_weights\", i32 1, i32 2}\n"
        without_metadata = "define void @f() {\n  ret void\n}\n"

        self.assertNotEqual(hard_hash_text(with_metadata), hard_hash_text(without_metadata))

    def test_hard_hash_reads_file(self):
        from ecpor.normalizer import hard_hash, hard_hash_text

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.ll"
            path.write_bytes(b"define void @f() {\r\n  ret void\r\n}\r\n")

            self.assertEqual(hard_hash(path), hard_hash_text("define void @f() {\n  ret void\n}\n"))


if __name__ == "__main__":
    unittest.main()
