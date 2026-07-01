import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PipelineDedupTests(unittest.TestCase):
    def test_hash_is_stable_for_same_sequence(self):
        from ecpor.pipeline_dedup import pipeline_sequence_hash

        left = pipeline_sequence_hash(["sroa", "early-cse", "instcombine"])
        right = pipeline_sequence_hash(["sroa", "early-cse", "instcombine"])
        different = pipeline_sequence_hash(["early-cse", "sroa", "instcombine"])

        self.assertEqual(left, right)
        self.assertEqual(len(left), 64)
        self.assertNotEqual(left, different)

    def test_deduplicates_rows_by_candidate_pipeline(self):
        from ecpor.pipeline_dedup import deduplicate_pipeline_rows

        rows = [
            {
                "candidate_id": "first",
                "candidate_pipeline": "a,b,c",
                "parent_candidate_id": "p0",
                "swap_path": "0;1",
            },
            {
                "candidate_id": "duplicate",
                "candidate_pipeline": "a,b,c",
                "parent_candidate_id": "p1",
                "swap_path": "1;0",
            },
            {
                "candidate_id": "different",
                "candidate_pipeline": "b,a,c",
                "parent_candidate_id": "p2",
                "swap_path": "0",
            },
        ]

        result = deduplicate_pipeline_rows(rows)

        self.assertEqual([row["candidate_id"] for row in result.unique_rows], ["first", "different"])
        self.assertEqual([row["candidate_id"] for row in result.duplicate_rows], ["duplicate"])
        self.assertEqual(result.sequence_to_candidate_ids[result.unique_rows[0]["pipeline_sequence_hash"]], ["first", "duplicate"])


if __name__ == "__main__":
    unittest.main()
