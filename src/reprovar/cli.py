"""Command-line entry point for ReproVar."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "variants.tsv"
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
USER_AGENT = "ReproVar/0.1 (public research audit)"


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def fetch_clinvar(record: dict[str, str]) -> dict[str, Any]:
    term = f'{record["gene"]}[gene] AND {record["query"]}[variant name]'
    if record.get("source_record"):
        ids = [record["source_record"]]
    else:
        params = urllib.parse.urlencode({"db": "clinvar", "term": term, "retmode": "json"})
        search = request_json(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + params
        )
        ids = search["esearchresult"]["idlist"]
        if len(ids) != 1:
            raise ValueError(f'{record["key"]}: expected one ClinVar hit, found {len(ids)}')
        time.sleep(0.36)  # stay below NCBI's unauthenticated request rate
    params = urllib.parse.urlencode({"db": "clinvar", "id": ids[0], "retmode": "json"})
    summary = request_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + params
    )
    return {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "query": term,
        "source_url": f'https://www.ncbi.nlm.nih.gov/clinvar/variation/{ids[0]}/',
        "response": summary,
    }


CIVIC_QUERY = """
query ReproVarEvidence($molecularProfileName: String!, $after: String) {
  evidenceItems(first: 100, after: $after, molecularProfileName: $molecularProfileName, status: ACCEPTED) {
    totalCount
    pageInfo { hasNextPage endCursor }
    nodes {
      id name evidenceLevel evidenceRating evidenceType evidenceDirection significance status variantOrigin
      molecularProfile { id name }
      disease { id name doid }
      therapies { id name }
      lastAcceptedRevisionEvent { createdAt }
      source { id citationId sourceType }
    }
  }
}
""".strip()


def fetch_civic(record: dict[str, str]) -> dict[str, Any]:
    molecular_profile = f'{record["gene"]} {record["query"]}'
    nodes: list[dict[str, Any]] = []
    cursor = None
    reported_total = 0
    while True:
        response = request_json(
            "https://civicdb.org/api/graphql",
            {"query": CIVIC_QUERY, "variables": {"molecularProfileName": molecular_profile, "after": cursor}},
        )
        if response.get("errors"):
            raise ValueError(f'{record["key"]}: CIViC API error: {response["errors"]}')
        connection = response.get("data", {}).get("evidenceItems", {})
        reported_total = connection.get("totalCount", 0)
        nodes.extend(connection.get("nodes", []))
        page_info = connection.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            raise ValueError(f'{record["key"]}: CIViC pagination cursor missing')
    exact = [
        node
        for node in nodes
        if record["gene"].upper() in node["molecularProfile"]["name"].upper()
        and record["query"].upper() in node["molecularProfile"]["name"].upper()
    ]
    if len(nodes) != reported_total:
        raise ValueError(
            f'{record["key"]}: CIViC returned {len(nodes)} of {reported_total} evidence items'
        )
    return {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "query": record["query"],
        "source_url": "https://civicdb.org/",
        "response": {"data": {"evidenceItems": {"totalCount": len(exact), "nodes": exact}}},
    }


def fetch_all() -> None:
    errors: list[str] = []
    for record in read_manifest():
        source = record["source"]
        destination = RAW / source.lower() / f'{record["key"]}.json'
        try:
            payload = fetch_clinvar(record) if source == "ClinVar" else fetch_civic(record)
            atomic_json(destination, payload)
            print(f"fetched {record['key']} from {source}")
        except (ValueError, KeyError, urllib.error.URLError) as error:
            errors.append(str(error))
    if errors:
        raise RuntimeError("fetch failed:\n- " + "\n- ".join(errors))


def _clean_date(value: str | None) -> str:
    if not value or value.startswith("1/01/01"):
        return ""
    for fmt in ("%Y/%m/%d %H:%M", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value[:10]


def normalise_clinvar(record: dict[str, str], payload: dict[str, Any]) -> list[dict[str, str]]:
    result = payload["response"]["result"]
    item = result[result["uids"][0]]
    classification = item.get("germline_classification", {})
    variation = item["variation_set"][0]
    locations = {loc["assembly_name"]: loc for loc in variation.get("variation_loc", [])}
    grch38 = locations.get("GRCh38", {})
    return [{
        **record,
        "source_id": item.get("accession_version", item.get("accession", "")),
        "normalised_name": item.get("title", ""),
        "classification": classification.get("description", "not provided"),
        "review_status": classification.get("review_status", "not provided"),
        "disease_context": "; ".join(
            trait.get("trait_name", "") for trait in classification.get("trait_set", [])
        ),
        "evidence_tier": "",
        "assertion_type": "germline classification",
        "therapies": "",
        "citation_id": "",
        "last_evaluated": _clean_date(classification.get("last_evaluated")),
        "grch38": ":".join(
            filter(None, [grch38.get("chr", ""), grch38.get("start", ""), grch38.get("stop", "")])
        ),
        "source_url": payload["source_url"],
        "retrieved_at": payload["retrieved_at"][:10],
    }]


def normalise_civic(record: dict[str, str], payload: dict[str, Any]) -> list[dict[str, str]]:
    nodes = payload["response"]["data"]["evidenceItems"]["nodes"]
    if not nodes:
        return [{
            **record,
            "source_id": "",
            "normalised_name": f'{record["gene"]} {record["query"]}',
            "classification": "no accepted assertion recovered",
            "review_status": "missing",
            "disease_context": "",
            "evidence_tier": "",
            "assertion_type": "",
            "therapies": "",
            "citation_id": "",
            "last_evaluated": "",
            "grch38": "",
            "source_url": payload["source_url"],
            "retrieved_at": payload["retrieved_at"][:10],
        }]
    rows = []
    for node in nodes:
        event = node.get("lastAcceptedRevisionEvent") or {}
        rows.append({
            **record,
            "source_id": f'CIViC EID{node["id"]}',
            "normalised_name": node["molecularProfile"]["name"],
            "classification": node.get("significance") or "not provided",
            "review_status": node.get("status") or "not provided",
            "disease_context": node.get("disease", {}).get("name", ""),
            "evidence_tier": node.get("evidenceLevel") or "",
            "assertion_type": node.get("evidenceType") or "",
            "therapies": "; ".join(t["name"] for t in node.get("therapies", [])),
            "citation_id": (node.get("source") or {}).get("citationId") or "",
            "last_evaluated": _clean_date(event.get("createdAt")),
            "grch38": "",
            "source_url": f'https://civicdb.org/evidence/{node["id"]}/summary',
            "retrieved_at": payload["retrieved_at"][:10],
        })
    return rows


def normalised_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for record in read_manifest():
        path = RAW / record["source"].lower() / f'{record["key"]}.json'
        if not path.exists():
            raise FileNotFoundError(f"missing snapshot: {path}; run `reprovar fetch`")
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.extend(
            normalise_clinvar(record, payload)
            if record["source"] == "ClinVar"
            else normalise_civic(record, payload)
        )
    return rows


FIELDNAMES = [
    "key", "domain", "gene", "input_variant", "source", "source_id",
    "normalised_name", "classification", "review_status", "disease_context",
    "evidence_tier", "assertion_type", "therapies", "citation_id", "last_evaluated",
    "grch38", "source_url", "retrieved_at",
]


def write_matrix(rows: list[dict[str, str]]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    with (REPORTS / "evidence_matrix.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def audit(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    audits: list[dict[str, str]] = []
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["key"], []).append(row)
    for record in read_manifest():
        matches = grouped[record["key"]]
        missing = any(r["review_status"] == "missing" for r in matches)
        classes = {r["classification"] for r in matches if r["classification"]}
        stale = any(
            not r["last_evaluated"] or int(r["last_evaluated"][:4]) < 2021
            for r in matches
        )
        flags = []
        if missing:
            flags.append("missing accepted assertion")
        if len(classes) > 1:
            flags.append("context-dependent evidence")
        if stale:
            flags.append("date missing or before 2021")
        audits.append({
            "key": record["key"],
            "source": record["source"],
            "records_recovered": str(len(matches)),
            "distinct_significances": str(len(classes)),
            "manual_review_required": "yes" if flags else "no",
            "flags": "; ".join(flags),
        })
    return audits


def write_audit(audits: list[dict[str, str]]) -> None:
    fields = ["key", "source", "records_recovered", "distinct_significances", "manual_review_required", "flags"]
    with (REPORTS / "audit_summary.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(audits)


def write_svg(rows: list[dict[str, str]], audits: list[dict[str, str]]) -> None:
    grouped = Counter(row["key"] for row in rows)
    labels = [record["key"] for record in read_manifest()]
    flagged = {row["key"] for row in audits if row["manual_review_required"] == "yes"}
    width, height = 1200, 620
    left, top, baseline = 95, 85, 425
    plot_width = width - left - 45
    bar_width = plot_width / len(labels) * 0.58
    max_count = max(grouped.values())
    max_scaled = math.log2(max_count + 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17212b}.title{font-size:22px;font-weight:700}.small{font-size:12px}.label{font-size:12px;font-weight:600}</style>',
        '<text x="42" y="42" class="title">Public evidence records recovered per benchmark variant</text>',
        '<text x="42" y="66" class="small">Log₂(count + 1) scale; exact record counts are printed above bars.</text>',
        f'<line x1="{left}" y1="{baseline}" x2="{width-35}" y2="{baseline}" stroke="#65727e"/>',
    ]
    for tick in (0, 1, 4, 16, 64, 128):
        if tick > max_count * 1.2:
            continue
        scaled = math.log2(tick + 1)
        y = baseline - scaled * 300 / max_scaled
        parts.append(f'<line x1="{left-5}" y1="{y:.1f}" x2="{width-35}" y2="{y:.1f}" stroke="#d8dee3"/>')
        parts.append(f'<text x="{left-14}" y="{y+4:.1f}" text-anchor="end" class="small">{tick}</text>')
    for index, label in enumerate(labels):
        x = left + (index + 0.5) * plot_width / len(labels)
        count = grouped[label]
        bar_height = math.log2(count + 1) * 300 / max_scaled
        colour = "#c75b39" if label in flagged else "#287d8e"
        parts.append(f'<rect x="{x-bar_width/2:.1f}" y="{baseline-bar_height:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="3" fill="{colour}"/>')
        parts.append(f'<text x="{x:.1f}" y="{baseline-bar_height-8:.1f}" text-anchor="middle" class="label">{count}</text>')
        parts.append(f'<text x="{x:.1f}" y="{baseline+22}" text-anchor="end" transform="rotate(-38 {x:.1f} {baseline+22})" class="small">{html.escape(label)}</text>')
    parts.extend([
        '<rect x="925" y="28" width="12" height="12" fill="#287d8e"/><text x="943" y="39" class="small">no audit flag</text>',
        '<rect x="1030" y="28" width="12" height="12" fill="#c75b39"/><text x="1048" y="39" class="small">manual review flag</text>',
        '<text x="42" y="598" class="small">Counts describe source records, not evidence strength or clinical validity.</text>',
        '</svg>',
    ])
    (REPORTS / "figures").mkdir(parents=True, exist_ok=True)
    (REPORTS / "figures" / "assertion_counts.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_report(rows: list[dict[str, str]], audits: list[dict[str, str]]) -> None:
    germline = [r for r in rows if r["domain"] == "germline"]
    somatic = [r for r in rows if r["domain"] == "somatic"]
    flagged = [a for a in audits if a["manual_review_required"] == "yes"]
    retrieved = sorted({r["retrieved_at"] for r in rows})
    source_date = ", ".join(retrieved)
    lines = [
        "# ReproVar evidence audit",
        "",
        f"**Snapshot date:** {source_date}  ",
        "**Intended use:** research, training and portfolio demonstration only",
        "",
        "## Question",
        "",
        "Can a compact, reproducible workflow recover and expose the provenance, review status and context of public evidence for representative germline and somatic cancer variants?",
        "",
        "## Results",
        "",
        f"The workflow recovered {len(germline)} ClinVar aggregate classifications for five germline variants and {len(somatic)} accepted CIViC evidence items for five somatic variants. The somatic records expanded into disease- and therapy-specific evidence statements; they must therefore be reviewed in context rather than collapsed into one label.",
        "",
        f"The audit flagged {len(flagged)} of 10 variants for manual review because their evidence was context dependent or included a missing or pre-2021 evaluation date. These flags are workflow controls. They are not classifications of clinical validity.",
        "",
        "![Public evidence records recovered](figures/assertion_counts.svg)",
        "",
        "## Variant-level audit",
        "",
        "| Variant | Source | Records | Distinct significance statements | Review? | Reason |",
        "|---|---|---:|---:|---|---|",
    ]
    for item in audits:
        lines.append(
            f'| {item["key"]} | {item["source"]} | {item["records_recovered"]} | '
            f'{item["distinct_significances"]} | {item["manual_review_required"]} | {item["flags"] or "—"} |'
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "A source label alone is insufficient for clinical reporting. Germline assertions require the condition, review status and evaluation date. Somatic evidence additionally requires tumour type, therapy, direction, evidence level and supporting publication. ReproVar retains these fields and identifies records that need human review.",
        "",
        "## Limitations",
        "",
        "This benchmark is deliberately small and is not representative of the full variant spectrum. It does not evaluate copy-number variants, fusions, splice prediction, population frequencies, phenotype matching or patient-level evidence. Public assertions may change after the frozen snapshot. The workflow does not apply ACMG/AMP criteria, assign AMP/ASCO/CAP tiers, diagnose disease, recommend therapy or replace accredited laboratory review.",
        "",
        "## Reproduction",
        "",
        "```bash",
        "python -m unittest discover -s tests -v",
        "PYTHONPATH=src python -m reprovar.cli analyse",
        "# Refresh public records (network required):",
        "PYTHONPATH=src python -m reprovar.cli all",
        "```",
        "",
        "Exact rows are available in [`evidence_matrix.tsv`](evidence_matrix.tsv); variant-level flags are in [`audit_summary.tsv`](audit_summary.tsv).",
    ])
    (REPORTS / "evidence_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_checksums() -> None:
    paths = sorted(path for path in RAW.rglob("*.json"))
    lines = []
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(ROOT)}")
    (RAW / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyse() -> None:
    rows = normalised_rows()
    audits = audit(rows)
    write_matrix(rows)
    write_audit(audits)
    write_svg(rows, audits)
    write_report(rows, audits)
    write_checksums()
    print(f"wrote {len(rows)} evidence rows and {len(audits)} variant audits")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("fetch", "analyse", "all"), nargs="?", default="analyse")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command in {"fetch", "all"}:
            fetch_all()
        if args.command in {"analyse", "all"}:
            analyse()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
