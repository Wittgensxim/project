# PassSpec Trust Report

PassSpec is an auditable metadata layer for static candidate generation.
It records conservative hints about possible pass opportunities and interactions.
These hints can prioritize dynamic AB/BA validation, but they never certify independence.

## Audit Summary

TotalPasses: 8
TotalHints: 64
RequiresAnyHints: 10
MayConsumeHints: 30
MayProduceHints: 24
ManualHints: 0
EmpiricalRepairHints: 5
LegacyHintsWithoutExplicitProvenance: 59
UnknownConfidenceHints: 59
HintsWithSupportCases: 5

## Provenance Inputs

P10AuditManifestStage: P10
P10AuditManifestCommit: 9291115ab1f764c6a0b7bbced0d64b69ce594ec8

## Empirical Repair Hints

| hint | source | stage | support cases | meaning |
| --- | --- | --- | ---: | --- |
| sroa.may_produce.scalar_cfg_opportunity | empirical_false_negative_repair | P3 | 2 | P3 static-filter repair for scalar producer to CFG simplification. |
| sroa.may_produce.dce_opportunity | empirical_false_negative_repair | P8b-2 | 5 | P8b-2 repair; sroa can expose cleanup opportunities consumed by dce/adce. |
| early-cse.may_produce.scalar_cfg_opportunity | empirical_false_negative_repair | P3.5 | 1 | P3.5 hold-out repair for CSE/load simplification feeding CFG cleanup. |
| simplifycfg.may_consume.scalar_cfg_opportunity | empirical_false_negative_repair | P3 | 3 | P3/P3.5 repairs for scalar producers exposing CFG simplification opportunities. |
| gvn.may_produce.scalar_cfg_opportunity | empirical_false_negative_repair | P3 | 1 | P3 repair for value numbering feeding simplifycfg through scalar CFG opportunity. |

The support cases explain why a hint was added; they are not sufficient proof.

### Support Cases

- `sroa.may_produce.scalar_cfg_opportunity`
  - program=testsuite_stanford_bubblesort; pair=sroa,simplifycfg; observed_label=not_certified_independent
  - program=testsuite_stanford_intmm; pair=sroa,simplifycfg; observed_label=not_certified_independent
- `sroa.may_produce.dce_opportunity`
  - program=testsuite_misc_ffbench; pair=sroa,adce; observed_label=not_certified_independent
  - program=testsuite_misc_flops_1; pair=sroa,dce; observed_label=not_certified_independent
  - program=testsuite_misc_flops_1; pair=sroa,adce; observed_label=not_certified_independent
  - program=testsuite_misc_flops_2; pair=sroa,dce; observed_label=not_certified_independent
  - program=testsuite_misc_flops_2; pair=sroa,adce; observed_label=not_certified_independent
- `early-cse.may_produce.scalar_cfg_opportunity`
  - program=testsuite_stanford_queens; pair=early-cse,simplifycfg; observed_label=not_certified_independent
- `simplifycfg.may_consume.scalar_cfg_opportunity`
  - program=testsuite_stanford_bubblesort; pair=sroa,simplifycfg; observed_label=not_certified_independent
  - program=testsuite_stanford_intmm; pair=sroa,simplifycfg; observed_label=not_certified_independent
  - program=testsuite_stanford_bubblesort; pair=simplifycfg,gvn; observed_label=not_certified_independent
- `gvn.may_produce.scalar_cfg_opportunity`
  - program=testsuite_stanford_bubblesort; pair=simplifycfg,gvn; observed_label=not_certified_independent

## Legacy hint limitations

Legacy hints are intentionally exposed rather than hidden.
They come from MVP-stage manual initialization and currently have no explicit provenance.
Their presence does not affect hard-pruning soundness because static filter decisions never certify independence.
However, they affect candidate recall and dynamic-test cost, so future PassSpecDB work should replace or annotate them using official registry data, source analysis, remarks, or empirical calibration.

## Behavioral compatibility

static_filter_behavior_change = false
passspec_behavior_change = false
classify_pair behavior unchanged
provenance metadata is ignored for decisions except for normalized hint names

## Evolution Roadmap

PassSpec v2: provenance for empirical repair hints
PassSpec v2.5: provenance for all legacy hints
PassSpec v3: registry snapshot from opt --print-passes
PassSpec v4: source-static extraction of analysis reads / preserved analyses
PassSpec v5: dynamic footprint / remarks / instrumentation
