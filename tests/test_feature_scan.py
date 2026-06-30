import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class FeatureScanTests(unittest.TestCase):
    def test_scan_ir_text_counts_basic_features(self):
        from ecpor.feature_scan import scan_ir_text

        features = scan_ir_text(
            """
            define i32 @f(i32 %x) {
            entry:
              %slot = alloca i32
              store i32 %x, ptr %slot
              %loaded = load i32, ptr %slot
              %called = call i32 @g(i32 %loaded)
              br label %next
            next:
              %phi = phi i32 [ %called, %entry ]
              ret i32 %phi
            }

            declare i32 @g(i32)
            """
        )

        self.assertEqual(features["num_functions"], 1)
        self.assertEqual(features["num_basic_blocks"], 2)
        self.assertEqual(features["num_alloca"], 1)
        self.assertEqual(features["num_load"], 1)
        self.assertEqual(features["num_store"], 1)
        self.assertEqual(features["num_call"], 1)
        self.assertEqual(features["num_branch"], 1)
        self.assertEqual(features["num_phi"], 1)
        self.assertEqual(features["num_ret"], 1)
        self.assertTrue(features["has_alloca"])
        self.assertTrue(features["has_load_store"])
        self.assertTrue(features["has_call"])
        self.assertTrue(features["has_branch"])
        self.assertTrue(features["has_phi"])
        self.assertGreater(features["num_instructions"], 0)

    def test_diff_features_subtracts_ab_from_ba(self):
        from ecpor.feature_scan import diff_features

        diff = diff_features(
            {"num_instructions": 2, "has_call": False},
            {"num_instructions": 5, "has_call": True},
        )

        self.assertEqual(diff["num_instructions"], 3)
        self.assertEqual(diff["has_call"], "False -> True")


if __name__ == "__main__":
    unittest.main()
