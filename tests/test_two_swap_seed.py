import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class TwoSwapSeedTests(unittest.TestCase):
    def test_top_k_per_program_selects_best_non_larger_and_equal_representatives(self):
        from ecpor.two_swap_seed import select_seed_rows

        p6_rows = [
            _size_row("p1", "p1_bad", "single_swap", "3.0"),
            _size_row("p1", "p1_best", "single_swap", "-5.0"),
            _size_row("p1", "p1_equal_a", "single_swap", "0.0"),
            _size_row("p1", "p1_equal_b", "single_swap", "0.0"),
            _size_row("p1", "p1_missing", "single_swap", "-9.0"),
            _size_row("p2", "p2_equal_a", "single_swap", "0.0"),
            _size_row("p2", "p2_equal_b", "single_swap", "0.0"),
            _size_row("p2", "p2_equal_c", "single_swap", "0.0"),
            _size_row("p2", "p2_equal_d", "single_swap", "0.0"),
            _size_row("p2", "p2_anchor", "anchor", "0.0"),
        ]
        p5_by_id = {
            row["candidate_id"]: {
                "program": row["program"],
                "candidate_id": row["candidate_id"],
                "candidate_pipeline": row["candidate_id"].replace("_", ","),
            }
            for row in p6_rows
            if row["candidate_id"] != "p1_missing"
        }

        seeds = select_seed_rows(
            p6_rows,
            p5_by_id,
            seed_mode="top-k-per-program",
            max_seeds_per_program=3,
        )

        self.assertEqual(
            [row["candidate_id"] for row in seeds],
            [
                "p1_best",
                "p1_equal_a",
                "p1_equal_b",
                "p2_equal_a",
                "p2_equal_b",
                "p2_equal_c",
            ],
        )
        self.assertEqual([row["seed_rank"] for row in seeds[:3]], ["1", "2", "3"])
        self.assertEqual(seeds[0]["seed_reason"], "best_text_delta")
        self.assertEqual(seeds[1]["seed_reason"], "equal_text_representative")
        self.assertEqual(seeds[3]["seed_reason"], "best_equal_text_delta")
        self.assertTrue(all(float(row["seed_text_delta_pct"]) <= 0.0 for row in seeds))
        self.assertTrue(all(row["seed_pipeline"] for row in seeds))

    def test_smaller_only_preserves_original_global_order(self):
        from ecpor.two_swap_seed import select_seed_rows

        p6_rows = [
            _size_row("p1", "p1_less", "single_swap", "-1.0"),
            _size_row("p2", "p2_best", "single_swap", "-3.0"),
            _size_row("p1", "p1_equal", "single_swap", "0.0"),
        ]
        p5_by_id = {
            row["candidate_id"]: {
                "program": row["program"],
                "candidate_id": row["candidate_id"],
                "candidate_pipeline": "a,b,c",
            }
            for row in p6_rows
        }

        seeds = select_seed_rows(
            p6_rows,
            p5_by_id,
            seed_mode="smaller-only",
            max_seeds_per_program=3,
        )

        self.assertEqual([row["candidate_id"] for row in seeds], ["p2_best", "p1_less"])
        self.assertEqual([row["seed_rank"] for row in seeds], ["1", "2"])
        self.assertTrue(all(row["seed_reason"] == "smaller_text" for row in seeds))


def _size_row(program: str, candidate_id: str, source: str, pct: str) -> dict[str, str]:
    return {
        "program": program,
        "candidate_id": candidate_id,
        "source": source,
        "text_delta_pct": pct,
    }


if __name__ == "__main__":
    unittest.main()
