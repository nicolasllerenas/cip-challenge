from pathlib import Path

import pytest
from cip_contracts import PaperMetadata
from cip_library.chunking import PageChunker, strip_references
from cip_library.metadata import find_doi, find_year, merge_metadata, parse_authors
from cip_library.pdf import UnreadablePdfError, extract_pdf


def test_doi_is_normalized_without_trailing_punctuation():
    text = "Available at https://doi.org/10.5555/SPP.2019.0142)."

    assert find_doi(text) == "10.5555/spp.2019.0142"


def test_publication_year_wins_over_cited_years():
    text = "Following Smith 2001 and Lee 2003, 2003.\nPublished: 15 March 2019"

    assert find_year(text) == 2019


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Quispe, Rosa Elena; Huaman, Carlos", [("Quispe", "Rosa Elena"), ("Huaman", "Carlos")]),
        ("Rosa Quispe and Carlos Huaman", [("Quispe", "Rosa"), ("Huaman", "Carlos")]),
        (None, []),
    ],
)
def test_authors_are_parsed_from_common_formats(raw, expected):
    assert [(author.family, author.given) for author in parse_authors(raw)] == expected


def test_remote_metadata_fills_gaps_but_keeps_local_doi():
    local = PaperMetadata(title="Local", year=2019, doi="10.5555/x")
    remote = PaperMetadata(title="Remote title", journal="Journal", doi="10.5555/other")

    merged = merge_metadata(local, remote)

    assert (merged.title, merged.year, merged.journal, merged.doi) == (
        "Remote title",
        2019,
        "Journal",
        "10.5555/x",
    )


def test_reference_section_is_not_indexed():
    pages = ["Intro text", "Results text\nReferences\nSmith, J. (2001). Old paper."]

    assert strip_references(pages) == ["Intro text", "Results text\n"]


def test_front_matter_noise_is_not_indexed():
    finding = "Drought limits potato yield in rainfed systems of the Andean highlands."
    page = f"Journal | https://doi.org/10.5555/x\nPublished: 15 March 2019\n{finding}"

    chunks = PageChunker(chunk_size=500, chunk_overlap=0).split([page])

    assert [chunk.text for chunk in chunks] == [
        "Drought limits potato yield in rainfed systems of the Andean highlands."
    ]


def test_chunks_keep_their_page_number():
    pages = ["A" * 10 + " first page sentence that is long enough to be kept.", "Second page " * 20]

    chunks = PageChunker(chunk_size=120, chunk_overlap=0).split(pages)

    assert {chunk.page for chunk in chunks} == {1, 2}
    assert [chunk.ordinal for chunk in chunks] == list(range(len(chunks)))


def test_scanned_pdf_has_no_text_layer(corpus: Path):
    extracted = extract_pdf(corpus / "scanned-field-notebook.pdf")

    assert not extracted.has_text_layer


def test_corrupt_pdf_raises_readable_error(corpus: Path):
    with pytest.raises(UnreadablePdfError, match="dañado"):
        extract_pdf(corpus / "corrupted-download.pdf")
