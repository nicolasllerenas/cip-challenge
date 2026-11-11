from io import BytesIO

from cip_contracts import Claim, Draft, Paragraph, Verdict
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.shared import Cm, Pt, RGBColor

from cip_documents.citations import ApaStyle
from cip_documents.disclosure import ai_disclosure

VERDICT_NOTES = {
    Verdict.PARTIAL: "Respaldo parcial: la fuente apoya solo una parte de esta afirmación.",
    Verdict.UNSUPPORTED: "Sin respaldo suficiente en las fuentes citadas. Verifícala o elimínala.",
}
MUTED = RGBColor(0x59, 0x5F, 0x69)


def claim_sentence(claim: Claim, style: ApaStyle) -> str:
    citation = style.parenthetical(claim.citations)
    body = claim.text.strip().rstrip(".")
    return f"{body} {citation}. " if citation else f"{body}. "


def review_note(claim: Claim, draft: Draft) -> str:
    sources = [
        f"{draft.evidence[link.passage_id].file_name}, p. {link.page}"
        for link in claim.citations
        if link.passage_id in draft.evidence
    ]
    lines = [VERDICT_NOTES.get(claim.verdict, ""), claim.rationale]
    if sources:
        lines.append("Fuentes: " + "; ".join(sources))
    return "\n".join(line for line in lines if line)


def _write_paragraph(document, paragraph: Paragraph, draft: Draft, style: ApaStyle, with_comments: bool) -> None:
    visible = [claim for claim in paragraph.claims if claim.is_visible]
    if not visible:
        return
    target = document.add_paragraph()
    for claim in visible:
        run = target.add_run(claim_sentence(claim, style))
        if with_comments and claim.needs_review:
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            document.add_comment(run, text=review_note(claim, draft), author="Verificador de citas", initials="VC")


def _write_references(document, style: ApaStyle) -> None:
    document.add_heading("Referencias", level=1)
    for reference in style.sorted_references():
        entry = document.add_paragraph()
        entry.paragraph_format.left_indent = Cm(1.27)
        entry.paragraph_format.first_line_indent = Cm(-1.27)
        lead, journal, tail = style.entry_parts(reference)
        entry.add_run(lead)
        if journal:
            entry.add_run(journal).italic = True
            entry.add_run(tail)


def render_docx(draft: Draft, include_review_comments: bool = True) -> bytes:
    style = ApaStyle(draft.references, draft.language)
    document = Document()
    document.styles["Normal"].font.name = "Calibri"
    document.styles["Normal"].font.size = Pt(11)
    properties = document.core_properties
    properties.title = draft.title
    properties.author = "Asistente de Investigación CIP"
    properties.comments = "Borrador generado con asistencia de IA; requiere revisión experta."
    document.add_heading(draft.title, level=0)
    disclosure = document.add_paragraph()
    disclosure.add_run("Declaración de uso de IA. ").bold = True
    note = disclosure.add_run(ai_disclosure(draft))
    note.italic = True
    note.font.color.rgb = MUTED
    for section in draft.sections:
        document.add_heading(section.heading, level=1)
        for paragraph in section.paragraphs:
            _write_paragraph(document, paragraph, draft, style, include_review_comments)
    if draft.references:
        _write_references(document, style)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
