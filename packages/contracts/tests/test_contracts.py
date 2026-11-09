from cip_contracts import (
    Author,
    CitationLink,
    Claim,
    Draft,
    EventType,
    JobEvent,
    PaperMetadata,
    Paragraph,
    ReviewStatus,
    Section,
    Verdict,
)


def build_draft() -> Draft:
    link = CitationLink(passage_id="p1", paper_id="a", page=3)
    claims = [
        Claim(claim_id="c1", text="Uno", citations=[link], verdict=Verdict.SUPPORTED),
        Claim(claim_id="c2", text="Dos", citations=[link], verdict=Verdict.PARTIAL),
        Claim(claim_id="c3", text="Tres", verdict=Verdict.UNSUPPORTED, review=ReviewStatus.REMOVED),
    ]
    section = Section(section_id="s1", heading="Intro", paragraphs=[Paragraph(claims=claims)])
    return Draft(draft_id="d1", library_id="l1", prompt="estado del arte", title="T", sections=[section])


def test_stats_ignore_removed_claims_and_count_pending_review():
    stats = build_draft().stats

    assert stats.claims == 2
    assert stats.supported == 1
    assert stats.partial == 1
    assert stats.unsupported == 0
    assert stats.pending_review == 1


def test_find_claim_returns_none_for_unknown_id():
    draft = build_draft()

    assert draft.find_claim("c2").text == "Dos"
    assert draft.find_claim("missing") is None


def test_job_event_round_trips_as_ndjson():
    event = JobEvent(type=EventType.JOB_COMPLETED, message="listo", data={"draft_id": "d1"})

    restored = JobEvent.model_validate_json(event.to_ndjson())

    assert restored.is_terminal
    assert restored.data == {"draft_id": "d1"}


def test_author_initials_and_missing_metadata():
    author = Author(family="Monneveux", given="Philippe Jean-Marc")
    metadata = PaperMetadata(title="Drought", authors=[author])

    assert author.initials == "P. J. M."
    assert metadata.missing_fields == ["year"]
