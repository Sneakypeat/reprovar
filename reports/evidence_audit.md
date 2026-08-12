# ReproVar evidence audit

**Snapshot date:** 2026-08-12  
**Intended use:** research, training and portfolio demonstration only

## Question

Can a compact, reproducible workflow recover and expose the provenance, review status and context of public evidence for representative germline and somatic cancer variants?

## Results

The workflow recovered 5 ClinVar aggregate classifications for five germline variants and 211 accepted CIViC evidence items for five somatic variants. The somatic records expanded into disease- and therapy-specific evidence statements; they must therefore be reviewed in context rather than collapsed into one label.

The audit flagged 6 of 10 variants for manual review because their evidence was context dependent or included a missing or pre-2021 evaluation date. These flags are workflow controls. They are not classifications of clinical validity.

![Public evidence records recovered](figures/assertion_counts.svg)

## Variant-level audit

| Variant | Source | Records | Distinct significance statements | Review? | Reason |
|---|---|---:|---:|---|---|
| BRCA1-c.68_69del | ClinVar | 1 | 1 | no | — |
| BRCA2-c.5946del | ClinVar | 1 | 1 | no | — |
| TP53-p.Arg273His | ClinVar | 1 | 1 | no | — |
| MLH1-p.Lys618del | ClinVar | 1 | 1 | yes | date missing or before 2021 |
| MUTYH-p.Gly396Asp | ClinVar | 1 | 1 | no | — |
| BRAF-V600E | CIViC | 111 | 5 | yes | context-dependent evidence; date missing or before 2021 |
| EGFR-L858R | CIViC | 48 | 3 | yes | context-dependent evidence; date missing or before 2021 |
| KRAS-G12C | CIViC | 18 | 4 | yes | context-dependent evidence; date missing or before 2021 |
| IDH1-R132H | CIViC | 4 | 1 | yes | date missing or before 2021 |
| PIK3CA-H1047R | CIViC | 30 | 4 | yes | context-dependent evidence; date missing or before 2021 |

## Interpretation

A source label alone is insufficient for clinical reporting. Germline assertions require the condition, review status and evaluation date. Somatic evidence additionally requires tumour type, therapy, direction, evidence level and supporting publication. ReproVar retains these fields and identifies records that need human review.

## Limitations

This benchmark is deliberately small and is not representative of the full variant spectrum. It does not evaluate copy-number variants, fusions, splice prediction, population frequencies, phenotype matching or patient-level evidence. Public assertions may change after the frozen snapshot. The workflow does not apply ACMG/AMP criteria, assign AMP/ASCO/CAP tiers, diagnose disease, recommend therapy or replace accredited laboratory review.

## Reproduction

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python -m reprovar.cli analyse
# Refresh public records (network required):
PYTHONPATH=src python -m reprovar.cli all
```

Exact rows are available in [`evidence_matrix.tsv`](evidence_matrix.tsv); variant-level flags are in [`audit_summary.tsv`](audit_summary.tsv).
