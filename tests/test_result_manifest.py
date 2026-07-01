import csv
import hashlib
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class ResultManifestTests(unittest.TestCase):
    def test_builds_p7a_manifest_from_outputs_and_hashes_files(self):
        from ecpor.result_manifest import build_p7a_manifest, write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p5_candidates = root / "p5_candidates.csv"
            p5_pipeline_runs = root / "p5_pipeline_runs.csv"
            p6_object_size = root / "p6_object_size.csv"
            passspec = root / "passspec.yaml"
            opt = root / "opt.exe"
            llc = root / "llc.exe"
            llvm_size = root / "llvm-size.exe"
            out_dir = root / "p7a"
            cert_dir = root / "certs"
            out_dir.mkdir()
            cert_dir.mkdir()
            _write_text(p5_candidates, "program,candidate_id,source,candidate_pipeline\n")
            _write_text(p5_pipeline_runs, "program,candidate_id,pipeline\n")
            _write_text(passspec, "passes: {}\n")
            _write_text(opt, "opt")
            _write_text(llc, "llc")
            _write_text(llvm_size, "size")
            _write_p6_object_size(p6_object_size)
            _write_p7a_outputs(out_dir)
            expected_p6_object_size_sha256 = _sha256_text(p6_object_size)
            expected_opt_sha256 = _sha256_text(opt)

            manifest = build_p7a_manifest(
                p5_candidates_csv=p5_candidates,
                p5_pipeline_runs_csv=p5_pipeline_runs,
                p6_object_size_csv=p6_object_size,
                passspec_path=passspec,
                output_dir=out_dir,
                cert_dir=cert_dir,
                opt_path=opt,
                llc_path=llc,
                llvm_size_path=llvm_size,
                repo_root=root,
                result_generated_from_commit="abc123",
            )
            manifest_path = root / "manifest.json"
            write_manifest(manifest_path, manifest)
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["stage"], "P7a")
        self.assertEqual(loaded["result_generated_from_commit"], "abc123")
        self.assertEqual(
            loaded["sha256"]["p6_object_size_csv"], expected_p6_object_size_sha256
        )
        self.assertEqual(loaded["sha256"]["opt"], expected_opt_sha256)
        self.assertEqual(loaded["summary"]["static_candidate_second_swaps"], 7)
        self.assertEqual(loaded["summary"]["unique_depth2_candidates"], 3)
        self.assertNotIn("ecpor_git_commit", loaded["summary"])
        self.assertNotIn("p5_candidates_csv", loaded["summary"])
        self.assertEqual(loaded["seed"]["candidate_id"], "seed")
        self.assertEqual(
            loaded["depth2_candidates"][0]["text_delta_pct_vs_anchor"], -10.0
        )
        self.assertEqual(loaded["depth2_candidates"][0]["delta_pct_vs_parent"], 0.0)


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_p6_object_size(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["program", "candidate_id", "source", "text_delta_pct"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "program": "tiny",
                    "candidate_id": "tiny__anchor",
                    "source": "anchor",
                    "text_delta_pct": "0.000000",
                },
                {
                    "program": "tiny",
                    "candidate_id": "seed",
                    "source": "single_swap",
                    "text_delta_pct": "-10.000000",
                },
            ]
        )


def _write_p7a_outputs(out_dir: Path) -> None:
    _write_text(
        out_dir / "two_swap_report.md",
        textwrap.dedent(
            """
            # P7a Bounded Two-Swap Smoke Report

            ecpor_git_commit: abc123
            p5_candidates_csv: data/outputs/p5/candidates.csv
            seed_candidates: 1
            attempted_second_swaps: 7
            static_candidate_second_swaps: 7
            validated_second_swaps: 7
            raw_depth2_candidates: 4
            duplicate_sequences: 1
            unique_depth2_candidates: 3
            anchor_runs: 8
            depth1_seed_runs: 0
            depth2_candidate_runs: 3
            total_pipeline_runs: 11
            best_depth1_text_delta_pct_vs_anchor: -10.0000
            best_depth2_text_delta_pct_vs_anchor: -10.0000
            best_depth2_delta_pct_vs_parent: 0.0000
            """
        ).strip()
        + "\n",
    )
    _write_text(out_dir / "two_swap_attempts.csv", "program,cache_hit,dynamic_test\n")
    _write_text(out_dir / "two_swap_pipeline_runs.csv", "program,candidate_id\n")
    with (out_dir / "two_swap_candidates.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "depth",
                "parent_candidate_id",
                "source",
                "candidate_pipeline",
                "swap_index",
                "pass_a",
                "pass_b",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "program": "tiny",
                "candidate_id": "tiny__depth2",
                "depth": "2",
                "parent_candidate_id": "seed",
                "source": "two_swap",
                "candidate_pipeline": "b,a,c",
                "swap_index": "1",
                "pass_a": "a",
                "pass_b": "c",
            }
        )
    with (out_dir / "two_swap_object_size.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "program",
                "candidate_id",
                "source",
                "text_delta_pct",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "program": "tiny",
                "candidate_id": "tiny__depth2",
                "source": "two_swap",
                "text_delta_pct": "-10.000000",
            }
        )


def _sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
