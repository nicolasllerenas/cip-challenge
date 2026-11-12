from cip_contracts import CitationLink
from cip_documents.citations import ApaStyle
from cip_testkit import sample_draft


def links(*paper_ids: str) -> list[CitationLink]:
    return [CitationLink(passage_id=f"{paper_id}:1", paper_id=paper_id, page=1) for paper_id in paper_ids]


def test_in_text_labels_follow_apa_author_rules_in_spanish():
    style = ApaStyle(sample_draft().references, "es")

    assert style.label("p-quispe") == "Quispe et al., 2019"
    assert style.label("p-condori") == "Condori y Flores, 2021"


def test_same_author_and_year_are_disambiguated_with_letters():
    style = ApaStyle(sample_draft().references, "es")

    assert {style.label("p-nina-a"), style.label("p-nina-b")} == {"Nina, 2023a", "Nina, 2023b"}


def test_parenthetical_groups_are_sorted_and_deduplicated():
    style = ApaStyle(sample_draft().references, "es")

    assert style.parenthetical(links("p-quispe", "p-condori", "p-quispe")) == (
        "(Condori y Flores, 2021; Quispe et al., 2019)"
    )
    assert style.parenthetical(links("unknown")) == ""


def test_reference_entry_uses_initials_conjunction_and_doi():
    style = ApaStyle(sample_draft().references, "es")
    reference = next(item for item in style.sorted_references() if item.paper_id == "p-quispe")

    lead, journal, tail = style.entry_parts(reference)

    assert lead == "Quispe, R. E., Huaman, C. y Vargas, L. (2019). Stomatal regulation in Andean potato. "
    assert journal == "Synthetic Journal"
    assert tail == ". https://doi.org/10.5555/quispe2019"


def test_english_uses_ampersand():
    style = ApaStyle(sample_draft().references, "en")

    assert style.label("p-condori") == "Condori & Flores, 2021"
