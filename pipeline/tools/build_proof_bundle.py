"""Assemble the client-facing proof bundle for a release.

The bundle is deliberately made of things the client can check without trusting
this machine: the live verification log (produced by `deploy/proof.py` against
the public site), the dataset card and manifest exactly as published, the
codebook, a flat table of all 37 codes with their boundaries, and SHA-256 sums.

No screenshots are copied in. A stale picture is worse than no picture: the log
and the sums can be re-verified, a PNG cannot.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from afs.taxonomy import Taxonomy  # noqa: E402
from afs import identity  # noqa: E402

OUT = ROOT / "outputs" / "proof"
LABELS = {"A_failure_type": "A. What failed", "B_cause_class": "B. Why",
          "C_lifecycle_stage": "C. Where", "D_severity": "D. Severity",
          "E_detection_point": "E. Detection"}


def codebook_csv(path: Path) -> int:
    import csv

    t = Taxonomy()
    rows = []
    for dim in t.spec["dimensions"]:
        for code in t.codes(dim):
            b = t.categories(dim)[code]
            rows.append({
                "dimension": LABELS.get(dim, dim),
                "code": code,
                "label": b["label"],
                "definition": " ".join(b["definition"].split()),
                "inclusion_rule": " | ".join(b["include"]),
                "exclusion_clause": " | ".join(b["exclude"]),
                "ordinal": b.get("ordinal", ""),
            })
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


MESSAGE = f"""\
Subject: Dataset release and completed codebook — Failures in Agentic AI

Hello,

A short note on what changed, and how to check it without taking my word for it.

1. The taxonomy is now complete on paper as well as in code. Every one of the 37
   categories across the five dimensions carries a definition, an inclusion rule
   and an explicit "not this category" clause. Previously only the failure-type
   axis was fully specified; the lifecycle, severity and detection axes had a
   one-line gloss each. No category was renamed and no label in the corpus moved,
   so every figure in the report is unchanged. `04_all_37_codes.csv` in this
   bundle lists all of them in one table.

2. The corpus is packaged as a dataset release and is now public:
   {identity.HF_URL}
   3,089 annotated failures, 32 columns, parquet, with cited examples, the schema
   and the codebook. `load_dataset("{identity.HF_REPO_ID}")`
   returns 3,089 rows and 32 features. Full issue text is not redistributed —
   each row keeps the permalink, the title and the short quotation that decided
   the label — and credential-shaped strings are masked before export.

3. Everything is live and independently checkable:
   {identity.SITE_URL}           the application (Data tab)
   {identity.DATASET_PAGE_URL}   the dataset card and files
   {identity.SITE_URL}api/dataset  counts as JSON
   {identity.REPORT_URL}    the written report
   {identity.HF_URL}

`01_live_verification.txt` is the output of a read-only probe run against the
public site and the Hub from outside the host: endpoint responses, the headline
figures, the robustness verdicts and the conformance line-by-line.
`05_SHA256SUMS.txt` matches the documents in this zip, so you can confirm nothing
was edited after the fact.

One thing is deliberately not done: the second-coder reliability pass. The
packet is prepared and blind, but a second coder has not sat the 40 records yet,
so agreement is reported as moderate (kappa 0.44) rather than as validated. I
would rather say that than round it up.

Best regards,
{identity.PROJECT_NAME} — {identity.INSTITUTION}
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    stamp = date.today().isoformat()
    name = f"Client_Proof_{stamp}_dataset"
    stage = OUT / "_bundle" / name
    if stage.exists():
        import shutil

        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    n_codes = codebook_csv(stage / "04_all_37_codes.csv")
    (stage / "00_message.txt").write_text(MESSAGE, encoding="utf-8")

    copies = [
        (OUT / "live_verification.txt", "01_live_verification.txt"),
        (ROOT / "outputs/hf_dataset/README.md", "02_dataset_card.md"),
        (ROOT / "outputs/hf_dataset/manifest.json", "03_dataset_manifest.json"),
        (ROOT / "configs/taxonomy.v1.yaml", "06_codebook_v1.yaml"),
        (ROOT / "outputs/reports/Requirement_Conformance.pdf",
         "07_Requirement_Conformance.pdf"),
        (ROOT / "outputs/reports/Agentic_Failure_Study_Report.pdf",
         "08_Study_Report.pdf"),
        (ROOT / "outputs/handover/One_Page_Summary.pdf", "09_One_Page_Summary.pdf"),
    ]
    missing = []
    for src, dst in copies:
        if src.exists():
            (stage / dst).write_bytes(src.read_bytes())
        else:
            missing.append(dst)

    sums = []
    for p in sorted(stage.iterdir()):
        sums.append(f"{sha256(p)}  {p.name}")
    (stage / "05_SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")

    zip_path = OUT / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(stage.iterdir()):
            zf.write(p, f"{name}/{p.name}")

    print(f"codes in table: {n_codes}")
    print(f"bundle: {zip_path} ({zip_path.stat().st_size / 1024:.0f} kB)")
    if missing:
        print("MISSING:", ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
