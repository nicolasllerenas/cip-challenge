from cip_contracts import (
    Author,
    CitationLink,
    Claim,
    Draft,
    PaperMetadata,
    Paragraph,
    Passage,
    Reference,
    ReviewStatus,
    Section,
    Verdict,
)

AUTHORS = {
    "p-quispe": [
        Author(family="Quispe", given="Rosa Elena"),
        Author(family="Huaman", given="Carlos"),
        Author(family="Vargas", given="Lucia"),
    ],
    "p-condori": [Author(family="Condori", given="Miguel Angel"), Author(family="Flores", given="Ana")],
    "p-nina-a": [Author(family="Nina", given="Roberto")],
    "p-nina-b": [Author(family="Nina", given="Roberto")],
}


def _reference(paper_id: str, key: str, year: int, title: str) -> Reference:
    return Reference(
        key=key,
        paper_id=paper_id,
        authors=AUTHORS[paper_id],
        year=year,
        title=title,
        journal="Synthetic Journal",
        doi=f"10.5555/{key}",
        file_name=f"{key}.pdf",
    )


def _passage(paper_id: str, page: int, text: str) -> Passage:
    return Passage(
        passage_id=f"{paper_id}:{page}",
        paper_id=paper_id,
        page=page,
        text=text,
        file_name=f"{paper_id}.pdf",
        metadata=PaperMetadata(authors=AUTHORS[paper_id]),
    )


def _link(paper_id: str, page: int) -> CitationLink:
    return CitationLink(passage_id=f"{paper_id}:{page}", paper_id=paper_id, page=page)


def sample_draft() -> Draft:
    references = [
        _reference("p-quispe", "quispe2019", 2019, "Stomatal regulation in Andean potato"),
        _reference("p-condori", "condori2021", 2021, "Root architecture and water uptake"),
        _reference("p-nina-a", "nina2023a", 2023, "Thermal imagery for drought phenotyping"),
        _reference("p-nina-b", "nina2023b", 2023, "Canopy temperature and yield"),
    ]
    evidence = {
        passage.passage_id: passage
        for passage in [
            _passage("p-quispe", 1, "Stomatal conductance decreased by 58 percent under drought."),
            _passage("p-condori", 2, "Deep root length density explained 63 percent of yield variation."),
            _passage("p-nina-a", 1, "Canopy temperature predicted tuber yield (R2 = 0.67)."),
            _passage("p-nina-b", 1, "Thermal imagery reduced phenotyping cost by 80 percent."),
        ]
    }
    physiology = Section(
        section_id="s1",
        heading="Respuestas fisiológicas",
        paragraphs=[
            Paragraph(
                claims=[
                    Claim(
                        claim_id="c1",
                        text="La papa cierra sus estomas de forma temprana ante el déficit hídrico.",
                        citations=[_link("p-quispe", 1)],
                        verdict=Verdict.SUPPORTED,
                    ),
                    Claim(
                        claim_id="c2",
                        text="La arquitectura radicular profunda explica gran parte del rendimiento bajo sequía",
                        citations=[_link("p-condori", 2), _link("p-quispe", 1)],
                        verdict=Verdict.PARTIAL,
                        rationale="La fuente cuantifica la relación solo en sequía terminal.",
                    ),
                ]
            )
        ],
    )
    phenotyping = Section(
        section_id="s2",
        heading="Fenotipado de alto rendimiento",
        paragraphs=[
            Paragraph(
                claims=[
                    Claim(
                        claim_id="c3",
                        text="La temperatura del dosel predice el rendimiento de tubérculos.",
                        citations=[_link("p-nina-a", 1), _link("p-nina-b", 1)],
                        verdict=Verdict.SUPPORTED,
                    ),
                    Claim(
                        claim_id="c4",
                        text="Los drones eliminan por completo la necesidad de mediciones manuales.",
                        citations=[_link("p-nina-b", 1)],
                        verdict=Verdict.UNSUPPORTED,
                        rationale="La fuente reporta una reducción de costos, no el reemplazo total.",
                    ),
                    Claim(
                        claim_id="c5",
                        text="Afirmación descartada por la investigadora.",
                        citations=[_link("p-nina-b", 1)],
                        verdict=Verdict.UNSUPPORTED,
                        review=ReviewStatus.REMOVED,
                    ),
                ]
            )
        ],
    )
    return Draft(
        draft_id="draft-1",
        library_id="lib-1",
        prompt="Redáctame un borrador del estado del arte sobre tolerancia a sequía en papa",
        title="Estado del arte: tolerancia a sequía en papa",
        sections=[physiology, phenotyping],
        references=references,
        evidence=evidence,
        models={"writer": "claude-opus-5-5", "verifier": "claude-haiku-5-5"},
    )
