import re
from collections import Counter
from datetime import UTC, datetime

import httpx
from cip_contracts import Author, PaperMetadata

from cip_library.pdf import ExtractedPdf

DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b((?:19|20)\d{2})\b")
PUBLICATION_YEAR = re.compile(
    r"(?:published|accepted|available online|©|copyright)[^\n]{0,40}?\b((?:19|20)\d{2})\b", re.IGNORECASE
)
NOISE_MARKERS = ("doi", "http", "journal", "vol.", "issn", "received", "©", "copyright", "www.")
UNHELPFUL_TITLES = ("untitled", "microsoft word", ".doc", ".pdf")
FIELD_LABELS = {"title": "título", "authors": "autores", "year": "año"}


def find_doi(text: str) -> str | None:
    match = DOI_PATTERN.search(text)
    return match.group(1).rstrip(".,;)]}").lower() if match else None


def find_year(text: str) -> int | None:
    current_year = datetime.now(UTC).year
    if match := PUBLICATION_YEAR.search(text):
        return int(match.group(1))
    years = [int(year) for year in YEAR_PATTERN.findall(text) if int(year) <= current_year]
    return Counter(years).most_common(1)[0][0] if years else None


def find_title(extracted: ExtractedPdf) -> str | None:
    info_title = extracted.info_title or ""
    if len(info_title) >= 15 and not any(marker in info_title.lower() for marker in UNHELPFUL_TITLES):
        return info_title
    first_page = extracted.pages[0] if extracted.pages else ""
    for line in first_page.splitlines()[:15]:
        candidate = line.strip()
        if 20 <= len(candidate) <= 250 and not any(marker in candidate.lower() for marker in NOISE_MARKERS):
            return candidate
    return None


def parse_person(name: str) -> Author:
    if "," in name:
        family, given = (part.strip() for part in name.split(",", 1))
        return Author(family=family, given=given)
    parts = name.split()
    return Author(family=parts[-1], given=" ".join(parts[:-1]))


def parse_authors(raw: str | None) -> list[Author]:
    if not raw:
        return []
    names = raw.split(";") if ";" in raw else re.split(r",|\band\b|&", raw)
    return [parse_person(name.strip()) for name in names if name.strip()]


def extract_metadata(extracted: ExtractedPdf) -> PaperMetadata:
    front_matter = extracted.front_matter
    return PaperMetadata(
        title=find_title(extracted),
        authors=parse_authors(extracted.info_author),
        year=find_year(front_matter),
        doi=find_doi(front_matter),
    )


def merge_metadata(local: PaperMetadata, remote: PaperMetadata | None) -> PaperMetadata:
    if remote is None:
        return local
    return PaperMetadata(
        title=remote.title or local.title,
        authors=remote.authors or local.authors,
        year=remote.year or local.year,
        doi=local.doi,
        journal=remote.journal or local.journal,
    )


def metadata_issues(metadata: PaperMetadata) -> list[str]:
    missing = [FIELD_LABELS[name] for name in metadata.missing_fields]
    return [f"Faltan datos para citarlo: {', '.join(missing)}. Puedes completarlos."] if missing else []


class CrossrefClient:
    def __init__(self, mailto: str | None = None, timeout: float = 6.0) -> None:
        agent = "CIP-Research-Assistant/0.1"
        self._headers = {"User-Agent": f"{agent} (mailto:{mailto})" if mailto else agent}
        self._timeout = timeout

    def lookup(self, doi: str) -> PaperMetadata | None:
        try:
            response = httpx.get(f"https://api.crossref.org/works/{doi}", headers=self._headers, timeout=self._timeout)
            response.raise_for_status()
        except httpx.HTTPError:
            return None
        work = response.json().get("message", {})
        authors = [
            Author(family=person.get("family") or person.get("name", ""), given=person.get("given", ""))
            for person in work.get("author", [])
        ]
        date_parts = work.get("issued", {}).get("date-parts") or [[None]]
        return PaperMetadata(
            title=next(iter(work.get("title", [])), None),
            authors=[author for author in authors if author.family],
            year=date_parts[0][0],
            doi=doi,
            journal=next(iter(work.get("container-title", [])), None),
        )
