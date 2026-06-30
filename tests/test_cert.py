import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class CertificateTests(unittest.TestCase):
    def test_pair_certificate_round_trips_to_json(self):
        from ecpor.cert import PairCertificate

        cert = PairCertificate(
            cert_id="cert-1",
            label="certified_independent",
            reason="hard hash equal",
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="input-hash",
            env_id="env-1",
            execution_model="materialized_ir_fresh_opt",
            llvm_version="23.0.0git",
            command_ab=["opt", "input.ll", "-passes=function(instcombine,dce)"],
            command_ba=["opt", "input.ll", "-passes=function(dce,instcombine)"],
            input_ir_path="input.ll",
            output_ab="ab.ll",
            output_ba="ba.ll",
            hash_ab="same",
            hash_ba="same",
            hard_equal=True,
            normalizer_version="hard-normalizer-v1",
            verifier_ab=True,
            verifier_ba=True,
            exit_code_ab=0,
            exit_code_ba=0,
            failure_kind_ab=None,
            failure_kind_ba=None,
            elapsed_ab_ms=1.25,
            elapsed_ba_ms=1.5,
            nesting="function",
            pipeline_ab="function(instcombine,dce)",
            pipeline_ba="function(dce,instcombine)",
            extra_flags=[],
            pass_a_instance="instcombine@unknown",
            pass_b_instance="dce@unknown",
            region_id="function_scalar_mvp",
            ecpor_git_commit="abc123",
            ecpor_git_dirty=False,
        )

        data = json.loads(cert.to_json())

        self.assertEqual(data["label"], "certified_independent")
        self.assertEqual(data["claim"], "certified_independent")
        self.assertEqual(data["pass_a"], "instcombine")
        self.assertEqual(data["pass_b"], "dce")
        self.assertTrue(data["hard_equal"])
        self.assertEqual(data["scope"], "state-specific")
        self.assertEqual(data["pipeline_ab"], "function(instcombine,dce)")
        self.assertIsNone(data["failure_kind_ab"])
        self.assertEqual(data["elapsed_ab_ms"], 1.25)
        self.assertEqual(data["ecpor_git_commit"], "abc123")

    def test_make_cert_id_is_stable_and_state_sensitive(self):
        from ecpor.cert import make_cert_id

        base = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state-1",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
            nesting="function",
            pipeline_ab="function(instcombine,dce)",
            pipeline_ba="function(dce,instcombine)",
            extra_flags=[],
        )
        again = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state-1",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
            nesting="function",
            pipeline_ab="function(instcombine,dce)",
            pipeline_ba="function(dce,instcombine)",
            extra_flags=[],
        )
        changed = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state-2",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
            nesting="function",
            pipeline_ab="function(instcombine,dce)",
            pipeline_ba="function(dce,instcombine)",
            extra_flags=[],
        )

        self.assertEqual(base, again)
        self.assertNotEqual(base, changed)

    def test_make_cert_id_is_sensitive_to_nesting_and_flags(self):
        from ecpor.cert import make_cert_id

        base = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
            nesting="function",
            pipeline_ab="function(instcombine,dce)",
            pipeline_ba="function(dce,instcombine)",
            extra_flags=[],
        )
        different_nesting = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
            nesting="module",
            pipeline_ab="module(instcombine,dce)",
            pipeline_ba="module(dce,instcombine)",
            extra_flags=[],
        )
        different_flags = make_cert_id(
            pass_a="instcombine",
            pass_b="dce",
            input_state_hash="state",
            env_id="env",
            execution_model="materialized_ir_fresh_opt",
            normalizer_version="hard-normalizer-v1",
            nesting="function",
            pipeline_ab="function(instcombine,dce)",
            pipeline_ba="function(dce,instcombine)",
            extra_flags=["-some-flag"],
        )

        self.assertNotEqual(base, different_nesting)
        self.assertNotEqual(base, different_flags)


if __name__ == "__main__":
    unittest.main()
