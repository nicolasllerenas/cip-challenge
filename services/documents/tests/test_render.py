import shutil
import subprocess
from io import BytesIO
from pathlib import Path

import pytest
from cip_documents.api import create_app, file_stem
from cip_documents.docx_renderer import render_docx
from cip_documents.text_renderers import render_bibtex, render_markdown
from cip_testkit import sample_draft
from docx import Document
from fastapi.testclient import TestClient


def open_docx(content: bytes):
    return Document(BytesIO(content))


def test_docx_contains_sections_citations_and_sorted_references():
    document = open_docx(render_docx(sample_draft()))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    headings = [p.text for p in document.paragraphs if p.style.name.startswith("Heading")]

    assert headings == ["Respuestas fisiológicas", "Fenotipado de alto rendimiento", "Referencias"]
    assert "déficit hídrico (Quispe et al., 2019)." in text
    assert "(Nina, 2023a; Nina, 2023b)" in text
    assert "Afirmación descartada" not in text
    references = text.split("Referencias")[-1].strip().splitlines()
    assert [line.split(",")[0] for line in references] == ["Condori", "Nina", "Nina", "Quispe"]


def test_claims_pending_review_become_word_comments():
    document = open_docx(render_docx(sample_draft()))
    comments = list(document.comments)

    assert len(comments) == 2
    assert all(comment.author == "Verificador de citas" for comment in comments)
    assert any("p. 1" in comment.text for comment in comments)


def test_review_comments_can_be_omitted():
    document = open_docx(render_docx(sample_draft(), include_review_comments=False))

    assert list(document.comments) == []


def test_docx_declares_ai_assistance():
    document = open_docx(render_docx(sample_draft()))

    assert document.core_properties.title == "Estado del arte: tolerancia a sequía en papa"
    assert "Declaración de uso de IA" in document.paragraphs[1].text
    assert "claude-haiku-5-5, claude-opus-5-5" in document.paragraphs[1].text


def test_markdown_uses_pandoc_citations_and_marks_review():
    markdown = render_markdown(sample_draft())

    assert "[@quispe2019]" in markdown
    assert "[@nina2023a; @nina2023b]" in markdown
    assert '{.revisar veredicto="unsupported"}' in markdown
    assert "bibliography: references.bib" in markdown


def test_bibtex_lists_every_reference():
    bibtex = render_bibtex(sample_draft().references)

    assert bibtex.count("@article{") == 4
    assert "author = {Quispe, Rosa Elena and Huaman, Carlos and Vargas, Lucia}" in bibtex


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc no está instalado")
def test_markdown_round_trips_to_latex_with_pandoc(tmp_path: Path):
    draft = sample_draft()
    (tmp_path / "draft.md").write_text(render_markdown(draft))
    (tmp_path / "references.bib").write_text(render_bibtex(draft.references))

    result = subprocess.run(
        ["pandoc", "draft.md", "--citeproc", "-s", "-o", "draft.tex"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Quispe" in (tmp_path / "draft.tex").read_text()


def test_render_endpoint_sets_download_headers():
    client = TestClient(create_app())

    response = client.post("/render", json={"draft": sample_draft().model_dump(mode="json"), "format": "docx"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert 'filename="estado-del-arte-tolerancia-a-sequia-en-papa.docx"' in response.headers["content-disposition"]


def test_file_stem_is_ascii_and_never_empty():
    assert file_stem("¿Sequía? ñandú") == "sequia-nandu"
    assert file_stem("¿?") == "borrador"
