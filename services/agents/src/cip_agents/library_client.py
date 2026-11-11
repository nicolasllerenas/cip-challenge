from typing import Protocol

import httpx
from cip_contracts import Passage, SearchRequest
from pydantic import TypeAdapter

PASSAGES = TypeAdapter(list[Passage])


class LibraryUnavailableError(Exception):
    pass


class Library(Protocol):
    async def search(self, library_id: str, request: SearchRequest) -> list[Passage]: ...


class HttpLibrary:
    def __init__(self, base_url: str, timeout: float = 30.0, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport

    async def search(self, library_id: str, request: SearchRequest) -> list[Passage]:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post(f"/libraries/{library_id}/search", json=request.model_dump())
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise LibraryUnavailableError("No pude consultar tu biblioteca de PDFs.") from error
        return PASSAGES.validate_json(response.content)
