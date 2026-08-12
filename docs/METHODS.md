# Methods

## Design

ReproVar is a descriptive, reproducible evidence-retrieval benchmark. Ten canonical cancer variants were selected a priori to span germline cancer predisposition and somatic precision oncology. The set is illustrative rather than statistically representative.

ClinVar was queried by gene and transcript-level cDNA expression through NCBI E-utilities. Each query was required to return exactly one Variation ID. The aggregate germline classification, review status, condition, evaluation date, VCV accession and GRCh38 location were retained.

CIViC was queried through its GraphQL v2 endpoint by molecular-profile name. Only accepted evidence items whose molecular-profile name contained both the intended gene and protein change were retained. Disease, therapies, evidence type, significance, evidence level, PubMed identifier and the last accepted revision date were preserved.

Raw API responses were frozen as JSON. SHA-256 digests provide integrity checks. A deterministic Python workflow generated the evidence matrix, variant-level audit, Markdown report and SVG figure. The release used Python 3.14.7 and has no third-party runtime dependencies.

## Audit rules

A variant was flagged for manual review if any of the following applied:

1. no accepted source assertion was recovered;
2. more than one distinct context-specific significance statement was recovered; or
3. the evaluation date was missing or preceded 2021.

These operational flags identify records requiring attention. They are not ACMG/AMP classifications, oncogenicity calls or treatment recommendations.

## Reproducibility and quality control

Automated tests verify the balanced benchmark design, source recovery, required provenance, somatic context, snapshot checksums, absence of obvious patient identifiers and deterministic audit output. All release outputs can be rebuilt offline from the frozen JSON snapshots.

## Pre-specified analysis contract

| Element | Specification |
|---|---|
| Primary question | Recover public provenance and context for all 10 variants |
| Primary endpoint | 10/10 variants represented in the normalised matrix |
| QC endpoint | All automated tests pass against frozen snapshots |
| Germline source | ClinVar aggregate germline classification |
| Somatic source | Accepted CIViC evidence items |
| Exclusions | Patient data; novel clinical classifications; treatment recommendations |
| Manual-review flag | Missing record, context-dependent evidence, or missing/pre-2021 date |
| Versioning | GitHub release plus Zenodo archive |
