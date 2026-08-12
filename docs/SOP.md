# Standard operating procedure: public variant-evidence audit

## Scope

This SOP covers retrieval and quality control of public, variant-level evidence for research and training. It does not cover patient-specific interpretation, report sign-out or clinical decision-making.

## Roles

- **Analyst:** runs the workflow, confirms identifiers and documents exceptions.
- **Reviewer:** checks source links, disease context, assertion status and dates.
- **Clinical signatory:** outside this project's scope; clinical conclusions require qualified personnel and an accredited laboratory process.

## Procedure

1. Define each variant with a gene, transcript-aware HGVS expression where applicable, domain and source.
2. Run `PYTHONPATH=src python -m reprovar.cli fetch`.
3. Confirm that each ClinVar query resolved to exactly one Variation ID.
4. Confirm that each CIViC evidence item matched both the intended gene and protein alteration and had accepted status.
5. Run `PYTHONPATH=src python -m reprovar.cli analyse`.
6. Run `python -m unittest discover -s tests -v`.
7. Review every row marked `manual_review_required=yes` in `reports/audit_summary.tsv` against the linked live source.
8. Record discrepancies without overwriting the frozen source response.
9. Version changes to the manifest, source snapshots, code and outputs together.

## Acceptance criteria

- Ten of ten manifest variants are represented.
- Every evidence row has a source identifier, URL and retrieval date.
- Somatic records retain disease context, evidence level and publication identifier.
- Snapshot hashes match `data/raw/SHA256SUMS`.
- All automated tests pass.
- No patient identifiers, automated diagnoses or treatment recommendations are present.

## Deviations and escalation

Stop and document the exception if a query returns zero or multiple ClinVar records, an API schema changes, source identifiers disagree, or a record cannot be reproduced. Escalate clinical questions to a qualified variant scientist or clinical geneticist.
