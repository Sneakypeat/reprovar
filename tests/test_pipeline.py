import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reprovar.cli import FIELDNAMES, audit, normalised_rows  # noqa: E402


class ReproVarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = normalised_rows()
        cls.audits = audit(cls.rows)

    def test_manifest_has_balanced_domains(self):
        with (ROOT / "data" / "variants.tsv").open(encoding="utf-8") as handle:
            records = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(records), 10)
        self.assertEqual(sum(r["domain"] == "germline" for r in records), 5)
        self.assertEqual(sum(r["domain"] == "somatic" for r in records), 5)

    def test_all_variants_recovered(self):
        self.assertEqual(len({row["key"] for row in self.rows}), 10)
        self.assertTrue(all(row["source_id"] for row in self.rows))

    def test_required_provenance_fields_are_present(self):
        required = {"source_id", "source_url", "retrieved_at", "review_status", "disease_context"}
        self.assertTrue(required.issubset(FIELDNAMES))
        for row in self.rows:
            self.assertTrue(all(row[field] for field in ("source_id", "source_url", "retrieved_at")))

    def test_somatic_rows_retain_context(self):
        somatic = [row for row in self.rows if row["domain"] == "somatic"]
        self.assertTrue(somatic)
        self.assertTrue(all(row["disease_context"] for row in somatic))
        self.assertTrue(all(row["evidence_tier"] for row in somatic))
        self.assertTrue(all(row["citation_id"] for row in somatic))

    def test_civic_snapshots_are_complete(self):
        for path in (ROOT / "data" / "raw" / "civic").glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            connection = payload["response"]["data"]["evidenceItems"]
            self.assertEqual(connection["totalCount"], len(connection["nodes"]))

    def test_snapshots_match_checksums(self):
        checksum_file = ROOT / "data" / "raw" / "SHA256SUMS"
        expected = {}
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            expected[relative] = digest
        snapshots = sorted((ROOT / "data" / "raw").rglob("*.json"))
        self.assertEqual(len(expected), 10)
        for path in snapshots:
            relative = str(path.relative_to(ROOT))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected[relative])

    def test_raw_files_contain_no_obvious_patient_fields(self):
        prohibited = {"patient_name", "medical_record_number", "date_of_birth"}
        for path in (ROOT / "data" / "raw").rglob("*.json"):
            content = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(prohibited.intersection(str(content).lower()))

    def test_audit_is_deterministic(self):
        self.assertEqual(self.audits, audit(self.rows))
        self.assertEqual(len(self.audits), 10)


if __name__ == "__main__":
    unittest.main()
