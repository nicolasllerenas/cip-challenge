import httpx
import pytest
from cip_library import metadata
from cip_library.metadata import CrossrefClient

WORK = {
    "message": {
        "title": ["Root system architecture and drought"],
        "author": [{"family": "Condori", "given": "Miguel Angel"}, {"name": "CIP Consortium"}],
        "issued": {"date-parts": [[2021, 5]]},
        "container-title": ["Field Crops Research"],
    }
}


def fake_get(status: int, payload: dict | None = None):
    def get(url: str, headers: dict, timeout: float) -> httpx.Response:
        assert url.endswith("/10.5555/sfcr.2021.0077")
        assert "mailto" not in headers["User-Agent"]
        return httpx.Response(status, json=payload or {}, request=httpx.Request("GET", url))

    return get


def test_crossref_metadata_is_mapped_to_citation_fields(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(metadata.httpx, "get", fake_get(200, WORK))

    result = CrossrefClient().lookup("10.5555/sfcr.2021.0077")

    assert result.title == "Root system architecture and drought"
    assert [(author.family, author.given) for author in result.authors] == [
        ("Condori", "Miguel Angel"),
        ("CIP Consortium", ""),
    ]
    assert (result.year, result.journal) == (2021, "Field Crops Research")


def test_crossref_failures_fall_back_to_local_metadata(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(metadata.httpx, "get", fake_get(404))

    assert CrossrefClient().lookup("10.5555/sfcr.2021.0077") is None
