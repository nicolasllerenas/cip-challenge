import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

REFERENCES_HEADING = re.compile(
    r"^\s*(references|bibliography|literature cited|referencias|bibliografía)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
NOISE_LINE = re.compile(
    r"https?://|doi\.org|^\s*(received|accepted|published|available online|©|copyright)\b", re.IGNORECASE
)
MIN_CHUNK_CHARS = 60


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    page: int
    text: str


def strip_noise(page: str) -> str:
    return "\n".join(line for line in page.splitlines() if not NOISE_LINE.search(line))


def strip_references(pages: list[str]) -> list[str]:
    for index in range(len(pages) // 2, len(pages)):
        if match := REFERENCES_HEADING.search(pages[index]):
            return [*pages[:index], pages[index][: match.start()]]
    return pages


class PageChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split(self, pages: list[str]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for page_number, text in enumerate(strip_references(pages), start=1):
            for piece in self._splitter.split_text(strip_noise(text)):
                cleaned = " ".join(piece.split())
                if len(cleaned) >= MIN_CHUNK_CHARS:
                    chunks.append(Chunk(ordinal=len(chunks), page=page_number, text=cleaned))
        return chunks
