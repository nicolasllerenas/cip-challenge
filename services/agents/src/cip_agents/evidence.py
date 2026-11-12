import re
import unicodedata
from string import ascii_lowercase

from cip_contracts import CitationLink, Draft, PaperMetadata, Passage, Reference, Section, Verdict

NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
LABEL = re.compile(r"E\d+", re.IGNORECASE)


def short_citation(metadata: PaperMetadata, fallback: str) -> str:
    families = [author.family for author in metadata.authors]
    year = metadata.year or "s.f."
    if not families:
        return f"{metadata.title or fallback}, {year}"
    if len(families) == 1:
        return f"{families[0]}, {year}"
    if len(families) == 2:
        return f"{families[0]} y {families[1]}, {year}"
    return f"{families[0]} et al., {year}"


def label_evidence(passages: list[Passage]) -> dict[str, Passage]:
    return {f"E{index}": passage for index, passage in enumerate(passages, start=1)}


def resolve_citations(labels: list[str], by_label: dict[str, Passage]) -> tuple[list[CitationLink], int]:
    links: dict[str, CitationLink] = {}
    invalid = 0
    for raw in labels:
        match = LABEL.search(raw)
        passage = by_label.get(match.group(0).upper()) if match else None
        if passage is None:
            invalid += 1
            continue
        links.setdefault(
            passage.passage_id,
            CitationLink(passage_id=passage.passage_id, paper_id=passage.paper_id, page=passage.page),
        )
    return list(links.values()), invalid


def numbers_in(text: str) -> set[str]:
    return {number.replace(",", ".") for number in NUMBER.findall(text) if len(number) > 1}


def unsupported_numbers(claim: str, sources: list[str]) -> list[str]:
    return sorted(numbers_in(claim) - numbers_in(" ".join(sources)))


def number_guardrail(verdict: Verdict, rationale: str, claim: str, sources: list[str]) -> tuple[Verdict, str]:
    missing = unsupported_numbers(claim, sources)
    if verdict == Verdict.SUPPORTED and missing:
        return Verdict.PARTIAL, f"Los valores {', '.join(missing)} no aparecen en la fuente citada."
    return verdict, rationale


def _ascii_slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", ascii_value)


def build_references(passages: list[Passage]) -> list[Reference]:
    papers = {passage.paper_id: passage for passage in passages}
    references: list[Reference] = []
    taken: dict[str, int] = {}
    for paper_id, passage in papers.items():
        metadata = passage.metadata
        stem = metadata.authors[0].family if metadata.authors else (metadata.title or passage.file_name).split()[0]
        base = f"{_ascii_slug(stem) or 'ref'}{metadata.year or 'sf'}"
        count = taken.get(base, 0)
        taken[base] = count + 1
        references.append(
            Reference(
                key=base if count == 0 else f"{base}{ascii_lowercase[count]}",
                paper_id=paper_id,
                authors=metadata.authors,
                year=metadata.year,
                title=metadata.title,
                journal=metadata.journal,
                doi=metadata.doi,
                file_name=passage.file_name,
            )
        )
    return references


def cited_passages(sections: list[Section], evidence: dict[str, Passage]) -> dict[str, Passage]:
    cited = {link.passage_id for section in sections for claim in section.claims() for link in claim.citations}
    return {passage_id: passage for passage_id, passage in evidence.items() if passage_id in cited}


def assert_citations_are_grounded(draft: Draft) -> None:
    for claim in draft.claims():
        for link in claim.citations:
            if link.passage_id not in draft.evidence:
                raise ValueError(f"La cita {link.passage_id} no proviene de la biblioteca")
