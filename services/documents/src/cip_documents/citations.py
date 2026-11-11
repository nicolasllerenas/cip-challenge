from collections import defaultdict
from dataclasses import dataclass
from string import ascii_lowercase

from cip_contracts import Author, CitationLink, Reference

CONJUNCTION = {"es": "y", "en": "&"}
NO_DATE = {"es": "s.f.", "en": "n.d."}


@dataclass(frozen=True)
class Vocabulary:
    conjunction: str
    no_date: str

    @classmethod
    def for_language(cls, language: str) -> "Vocabulary":
        code = language if language in CONJUNCTION else "en"
        return cls(CONJUNCTION[code], NO_DATE[code])


class ApaStyle:
    def __init__(self, references: list[Reference], language: str = "es") -> None:
        self._words = Vocabulary.for_language(language)
        self._by_paper = {reference.paper_id: reference for reference in references}
        self._years = self._disambiguated_years(references)

    def _disambiguated_years(self, references: list[Reference]) -> dict[str, str]:
        groups: dict[tuple[str, int | None], list[Reference]] = defaultdict(list)
        for reference in sorted(references, key=lambda item: (item.title or "").lower()):
            groups[(self._short_authors(reference), reference.year)].append(reference)
        years: dict[str, str] = {}
        for (_, year), group in groups.items():
            base = str(year) if year else self._words.no_date
            for index, reference in enumerate(group):
                suffix = ascii_lowercase[index] if len(group) > 1 else ""
                years[reference.paper_id] = f"{base}{suffix}"
        return years

    def _short_authors(self, reference: Reference) -> str:
        families = [author.family for author in reference.authors]
        if not families:
            return reference.title or reference.file_name
        if len(families) == 1:
            return families[0]
        if len(families) == 2:
            return f"{families[0]} {self._words.conjunction} {families[1]}"
        return f"{families[0]} et al."

    def sorted_references(self) -> list[Reference]:
        return sorted(
            self._by_paper.values(),
            key=lambda reference: (self._short_authors(reference).lower(), self._years[reference.paper_id]),
        )

    def label(self, paper_id: str) -> str:
        reference = self._by_paper[paper_id]
        return f"{self._short_authors(reference)}, {self._years[paper_id]}"

    def parenthetical(self, citations: list[CitationLink]) -> str:
        papers = dict.fromkeys(link.paper_id for link in citations if link.paper_id in self._by_paper)
        labels = sorted((self.label(paper_id) for paper_id in papers), key=str.lower)
        return f"({'; '.join(labels)})" if labels else ""

    def _author_list(self, authors: list[Author]) -> str:
        names = [f"{author.family}, {author.initials}".rstrip(", ") for author in authors]
        if len(names) == 1:
            return names[0]
        separator = f" {self._words.conjunction} " if self._words.conjunction == "y" else ", & "
        return ", ".join(names[:-1]) + separator + names[-1]

    def entry_parts(self, reference: Reference) -> tuple[str, str | None, str]:
        year = f"({self._years[reference.paper_id]})."
        title = (reference.title or reference.file_name).rstrip(".")
        lead = f"{self._author_list(reference.authors)} {year} {title}." if reference.authors else f"{title}. {year}"
        doi = f"https://doi.org/{reference.doi}" if reference.doi else ""
        if reference.journal:
            return f"{lead} ", reference.journal, f". {doi}".rstrip()
        return f"{lead} {doi}".rstrip(), None, ""
