from pathlib import Path

from fpdf import FPDF

from cip_testkit.papers import PAPERS, SyntheticPaper

DISCLAIMER = "Synthetic document generated for software testing. Not real research."


def _author_line(paper: SyntheticPaper) -> str:
    return ", ".join(f"{given} {family}" for family, given in paper.authors)


def write_paper(paper: SyntheticPaper, target: Path) -> Path:
    pdf = FPDF()
    pdf.set_title(paper.title)
    pdf.set_author("; ".join(f"{family}, {given}" for family, given in paper.authors))
    pdf.set_auto_page_break(auto=True, margin=20)
    width = pdf.epw
    for number, paragraphs in enumerate(paper.pages, start=1):
        pdf.add_page()
        if number == 1:
            pdf.set_font("Helvetica", size=8)
            pdf.multi_cell(width, 4, f"{paper.journal} | https://doi.org/{paper.doi}")
            pdf.ln(4)
            pdf.set_font("Helvetica", style="B", size=15)
            pdf.multi_cell(width, 7, paper.title)
            pdf.ln(2)
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(width, 5, _author_line(paper))
            pdf.multi_cell(width, 5, f"Published: 15 March {paper.year}")
            pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        for paragraph in paragraphs:
            pdf.multi_cell(width, 6, paragraph)
            pdf.ln(3)
        pdf.set_font("Helvetica", style="I", size=7)
        pdf.multi_cell(width, 4, DISCLAIMER)
    if paper.references:
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.multi_cell(width, 6, "References")
        pdf.set_font("Helvetica", size=9)
        for reference in paper.references:
            pdf.multi_cell(width, 5, reference)
    destination = target / f"{paper.slug}.pdf"
    pdf.output(str(destination))
    return destination


def write_scanned_pdf(target: Path) -> Path:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(200, 200, 200)
    pdf.rect(20, 20, 170, 240, style="F")
    destination = target / "scanned-field-notebook.pdf"
    pdf.output(str(destination))
    return destination


def write_corrupt_pdf(target: Path) -> Path:
    destination = target / "corrupted-download.pdf"
    destination.write_bytes(b"%PDF-1.4\n%broken\n1 0 obj << /Type /Catalog")
    return destination


def build_corpus(target: Path, *, include_problematic: bool = True) -> list[Path]:
    target.mkdir(parents=True, exist_ok=True)
    files = [write_paper(paper, target) for paper in PAPERS]
    if include_problematic:
        files += [write_scanned_pdf(target), write_corrupt_pdf(target)]
    return files
