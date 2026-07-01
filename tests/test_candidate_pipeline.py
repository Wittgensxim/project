import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CandidatePipelineTests(unittest.TestCase):
    def test_builds_anchor_and_single_swap_only_for_not_certified_pairs(self):
        from ecpor.candidate_pipeline import build_candidate_pipelines

        generation = build_candidate_pipelines(
            programs=["tiny"],
            anchor_passes=["sroa", "early-cse", "instcombine", "dce"],
            attempts=[
                _attempt(
                    "tiny",
                    "",
                    "h0",
                    "sroa",
                    "early-cse",
                    "cert-0",
                    "validated",
                    "not_certified_independent",
                ),
                _attempt(
                    "tiny",
                    "sroa",
                    "h1",
                    "early-cse",
                    "instcombine",
                    "cert-1",
                    "validated",
                    "certified_independent",
                ),
                _attempt(
                    "tiny",
                    "sroa,early-cse",
                    "h2",
                    "instcombine",
                    "dce",
                    "",
                    "skipped_low_priority",
                    "skipped_by_static_filter",
                ),
            ],
        )

        self.assertEqual(generation.summary["anchor"], 1)
        self.assertEqual(generation.summary["single_swap"], 1)
        self.assertEqual(generation.summary["collapsed_certified_independent"], 1)
        self.assertEqual(generation.summary["frozen_by_static_filter"], 1)
        self.assertEqual(generation.summary["invalid_run_failed"], 0)

        candidates = generation.candidates
        self.assertEqual(len(candidates), 2)
        anchor = candidates[0]
        swap = candidates[1]
        self.assertEqual(anchor.source, "anchor")
        self.assertEqual(anchor.base_pipeline, "sroa,early-cse,instcombine,dce")
        self.assertEqual(anchor.candidate_pipeline, anchor.base_pipeline)
        self.assertEqual(anchor.validation_label, "anchor")
        self.assertEqual(swap.source, "single_swap")
        self.assertEqual(swap.swap_index, 0)
        self.assertEqual(swap.candidate_pipeline, "early-cse,sroa,instcombine,dce")
        self.assertEqual(swap.prefix_state_hash, "h0")
        self.assertEqual(swap.validation_label, "not_certified_independent")
        self.assertEqual(swap.cert_id, "cert-0")

    def test_writes_requested_candidate_csv_fields(self):
        from ecpor.candidate_pipeline import CANDIDATE_FIELDS, write_candidates_csv
        from ecpor.candidate_pipeline import build_candidate_pipelines

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "candidates.csv"
            generation = build_candidate_pipelines(
                programs=["tiny"],
                anchor_passes=["sroa", "early-cse"],
                attempts=[
                    _attempt(
                        "tiny",
                        "",
                        "h0",
                        "sroa",
                        "early-cse",
                        "cert-0",
                        "validated",
                        "not_certified_independent",
                    )
                ],
            )

            write_candidates_csv(out, generation.candidates)

            with out.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, CANDIDATE_FIELDS)
                rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["source"], "single_swap")
        self.assertEqual(rows[1]["swap_index"], "0")


def _attempt(
    program,
    prefix_passes,
    state_hash,
    pass_a,
    pass_b,
    cert_id,
    action,
    label,
):
    return {
        "program": program,
        "prefix_passes": prefix_passes,
        "state_hash": state_hash,
        "pass_a": pass_a,
        "pass_b": pass_b,
        "cert_id": cert_id,
        "action": action,
        "label": label,
    }


if __name__ == "__main__":
    unittest.main()
