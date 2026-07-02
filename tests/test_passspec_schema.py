import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class PassSpecSchemaTests(unittest.TestCase):
    def test_legacy_hint_lists_normalize_with_default_provenance(self):
        from ecpor.passspec_schema import normalize_passspec

        normalized = normalize_passspec(
            {
                "passes": {
                    "sroa": {
                        "level": "function",
                        "requires_any": ["has_alloca"],
                        "may_consume": ["alloca"],
                        "may_produce": ["scalar_value"],
                        "tags": ["scalar", "memory"],
                    }
                }
            }
        )

        self.assertEqual(normalized["sroa"]["requires_any"], ["has_alloca"])
        self.assertEqual(normalized["sroa"]["may_consume"], ["alloca"])
        self.assertEqual(normalized["sroa"]["may_produce"], ["scalar_value"])
        self.assertEqual(normalized["sroa"]["tags"], ["scalar", "memory"])
        provenance = normalized["sroa"]["_hint_provenance"]["may_produce"][
            "scalar_value"
        ]
        self.assertEqual(provenance.source, "unknown_legacy")
        self.assertEqual(provenance.confidence, "unknown")
        self.assertEqual(provenance.support, ())
        self.assertFalse(provenance.explicit_provenance)

    def test_mapping_hint_schema_preserves_source_confidence_and_support(self):
        from ecpor.passspec_schema import normalize_passspec

        normalized = normalize_passspec(
            {
                "passes": {
                    "sroa": {
                        "level": "function",
                        "requires_any": {"has_alloca": {"source": "source_static_hint"}},
                        "may_consume": [],
                        "may_produce": {
                            "dce_opportunity": {
                                "source": "empirical_false_negative_repair",
                                "confidence": "medium",
                                "created_in_stage": "P8b-2",
                                "support": [
                                    {
                                        "program": "testsuite_misc_ffbench",
                                        "pair": "sroa,adce",
                                        "observed_label": "not_certified_independent",
                                    }
                                ],
                                "note": "Observed as a static-filter false negative.",
                            }
                        },
                        "tags": ["scalar"],
                    }
                }
            }
        )

        self.assertEqual(normalized["sroa"]["may_produce"], ["dce_opportunity"])
        provenance = normalized["sroa"]["_hint_provenance"]["may_produce"][
            "dce_opportunity"
        ]
        self.assertEqual(provenance.source, "empirical_false_negative_repair")
        self.assertEqual(provenance.confidence, "medium")
        self.assertEqual(provenance.created_in_stage, "P8b-2")
        self.assertEqual(len(provenance.support), 1)
        self.assertTrue(provenance.explicit_provenance)

    def test_hybrid_list_items_allow_only_selected_hints_to_get_metadata(self):
        from ecpor.passspec_schema import normalize_passspec

        normalized = normalize_passspec(
            {
                "passes": {
                    "simplifycfg": {
                        "level": "function",
                        "requires_any": ["has_branch"],
                        "may_consume": [
                            "branch",
                            {
                                "scalar_cfg_opportunity": {
                                    "source": "empirical_false_negative_repair",
                                    "confidence": "medium",
                                    "created_in_stage": "P3",
                                }
                            },
                        ],
                        "may_produce": [],
                        "tags": ["cfg"],
                    }
                }
            }
        )

        self.assertEqual(
            normalized["simplifycfg"]["may_consume"],
            ["branch", "scalar_cfg_opportunity"],
        )
        legacy = normalized["simplifycfg"]["_hint_provenance"]["may_consume"][
            "branch"
        ]
        repaired = normalized["simplifycfg"]["_hint_provenance"]["may_consume"][
            "scalar_cfg_opportunity"
        ]
        self.assertFalse(legacy.explicit_provenance)
        self.assertTrue(repaired.explicit_provenance)


if __name__ == "__main__":
    unittest.main()
