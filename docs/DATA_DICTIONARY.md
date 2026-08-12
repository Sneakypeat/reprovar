# Data dictionary

| Field | Meaning |
|---|---|
| `key` | Stable project identifier for the benchmark variant |
| `domain` | Germline or somatic analysis track |
| `gene` | HGNC gene symbol |
| `input_variant` | Curated transcript or protein expression |
| `source` | Public evidence source |
| `source_id` | VCV accession/version or CIViC evidence-item ID |
| `normalised_name` | Source-reported variant or molecular-profile name |
| `classification` | Source-reported germline classification or somatic significance |
| `review_status` | Source-reported review or acceptance status |
| `disease_context` | Condition or tumour type attached to the assertion |
| `evidence_tier` | Source-reported CIViC evidence level (retained under a generic field name) |
| `assertion_type` | Germline classification, predictive, prognostic or diagnostic context |
| `therapies` | Therapies linked to a CIViC assertion |
| `citation_id` | PubMed identifier linked to a CIViC evidence item |
| `last_evaluated` | Source evaluation or last accepted-revision date |
| `grch38` | ClinVar GRCh38 chromosome:start:stop when available |
| `source_url` | Direct public record link |
| `retrieved_at` | UTC date on which the frozen response was obtained |
