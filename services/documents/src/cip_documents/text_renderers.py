from cip_contracts import Claim, Draft, Reference

from cip_documents.disclosure import ai_disclosure

BIBTEX_ESCAPES = str.maketrans({"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": "", "}": ""})


def _yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _markdown_claim(claim: Claim, keys: dict[str, str]) -> str:
    cited = dict.fromkeys(keys[link.paper_id] for link in claim.citations if link.paper_id in keys)
    body = claim.text.strip().rstrip(".")
    citation = f" [{'; '.join(f'@{key}' for key in cited)}]" if cited else ""
    sentence = f"{body}{citation}."
    return f'[{sentence}]{{.revisar veredicto="{claim.verdict.value}"}}' if claim.needs_review else sentence


def render_markdown(draft: Draft) -> str:
    keys = {reference.paper_id: reference.key for reference in draft.references}
    lines = [
        "---",
        f"title: {_yaml_string(draft.title)}",
        f"lang: {draft.language}",
        "bibliography: references.bib",
        "link-citations: true",
        "---",
        "",
        f"> **Declaración de uso de IA.** {ai_disclosure(draft)}",
    ]
    for section in draft.sections:
        lines += ["", f"## {section.heading}"]
        for paragraph in section.paragraphs:
            sentences = [_markdown_claim(claim, keys) for claim in paragraph.claims if claim.is_visible]
            if sentences:
                lines += ["", " ".join(sentences)]
    lines += ["", "## Referencias", "", "::: {#refs}", ":::", ""]
    return "\n".join(lines)


def _bibtex_entry(reference: Reference) -> str:
    authors = " and ".join(
        f"{author.family}, {author.given}".rstrip(", ").translate(BIBTEX_ESCAPES) for author in reference.authors
    )
    fields = {
        "author": authors,
        "title": f"{{{(reference.title or reference.file_name).translate(BIBTEX_ESCAPES)}}}",
        "journal": (reference.journal or "").translate(BIBTEX_ESCAPES),
        "year": str(reference.year or ""),
        "doi": reference.doi or "",
    }
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields.items() if value)
    kind = "article" if reference.journal else "misc"
    return f"@{kind}{{{reference.key},\n{body}\n}}\n"


def render_bibtex(references: list[Reference]) -> str:
    return "\n".join(_bibtex_entry(reference) for reference in references)
