from collections.abc import AsyncIterator
from typing import Any

import httpx
from cip_contracts import EventType, JobEvent
from fastapi import HTTPException

UNAVAILABLE = "Uno de los servicios del asistente no responde. Revisa que la app esté iniciada e intenta de nuevo."


def failure(message: str, code: str) -> JobEvent:
    return JobEvent(type=EventType.JOB_FAILED, message=message, data={"code": code})


def detail_of(response: httpx.Response) -> str:
    try:
        return response.json().get("detail") or UNAVAILABLE
    except ValueError:
        return UNAVAILABLE


class Upstream:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, url, **kwargs)
        except httpx.HTTPError as error:
            raise HTTPException(503, UNAVAILABLE) from error
        if response.status_code >= 400:
            raise HTTPException(response.status_code, detail_of(response))
        return response

    async def events(self, url: str, payload: dict[str, Any] | None = None) -> AsyncIterator[JobEvent]:
        try:
            async with self._client.stream("POST", url, json=payload, timeout=httpx.Timeout(10, read=None)) as response:
                if response.status_code >= 400:
                    await response.aread()
                    yield failure(detail_of(response), "upstream_rejected")
                    return
                async for line in response.aiter_lines():
                    if line.strip():
                        yield JobEvent.model_validate_json(line)
        except httpx.HTTPError:
            yield failure(UNAVAILABLE, "service_unavailable")

    async def health(self, name: str, url: str) -> dict[str, Any]:
        try:
            response = await self._client.get(url, timeout=3)
            return {"name": name, "ok": response.is_success, **response.json()}
        except (httpx.HTTPError, ValueError):
            return {"name": name, "ok": False}
