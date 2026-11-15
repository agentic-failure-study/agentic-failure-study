"""Export every Word/PowerPoint deliverable to PDF beside its source.

The pipeline writes DOCX/PPTX; reviewers and the deployment preview want PDF.
This is a thin Windows COM wrapper (Word + PowerPoint) with no dependency on
LaTeX or LibreOffice, and it is safe to re-run: each PDF is overwritten.

Usage:  python tools/make_pdfs.py
"""
from __future__ import annotations

from pathlib import Path

import win32com.client as win32

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

DOCX = [
    OUT / "reports" / "Agentic_Failure_Study_Report.docx",
    OUT / "reports" / "Agentic_Failure_Study_Paper.docx",
    OUT / "reports" / "Requirement_Conformance.docx",
    OUT / "handover" / "One_Page_Summary.docx",
    OUT / "handover" / "Second_Coder_Packet.docx",
]
PPTX = [
    OUT / "handover" / "Agentic_Failure_Study_Deck.pptx",
]


def docx_pdf(src: Path) -> None:
    app = win32.Dispatch("Word.Application")
    app.Visible = False
    doc = app.Documents.Open(str(src), ReadOnly=True)
    try:
        doc.SaveAs(str(src.with_suffix(".pdf")), FileFormat=17)  # wdFormatPDF
        print(f"  {src.name} -> {src.with_suffix('.pdf').name} "
              f"({doc.ComputeStatistics(2)} pages)")
    finally:
        doc.Close(False)
        app.Quit()


def pptx_pdf(src: Path) -> None:
    app = win32.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(src), WithWindow=False)
    try:
        pres.SaveAs(str(src.with_suffix(".pdf")), 32)  # ppSaveAsPDF
        print(f"  {src.name} -> {src.with_suffix('.pdf').name} "
              f"({pres.Slides.Count} slides)")
    finally:
        pres.Close()
        app.Quit()


if __name__ == "__main__":
    for p in DOCX:
        if p.exists():
            docx_pdf(p)
    for p in PPTX:
        if p.exists():
            pptx_pdf(p)
