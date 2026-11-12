from dataclasses import dataclass
from typing import Literal

from cip_testkit import PAPERS

Verdict = Literal["supported", "partial", "unsupported"]


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected: str
    language: Literal["en", "es"]


@dataclass(frozen=True)
class VerifierCase:
    claim: str
    paper: str
    page: int
    expected: Verdict
    note: str = ""


RETRIEVAL_CASES = [
    RetrievalCase("stomatal closure abscisic acid under soil drying", "stomatal-aba-andean-potato", "en"),
    RetrievalCase("photosynthesis reduction tuber biomass sensitive genotypes", "stomatal-aba-andean-potato", "en"),
    RetrievalCase("root length density deep roots terminal drought yield", "root-architecture-water-uptake", "en"),
    RetrievalCase("heritability of root traits for breeding", "root-architecture-water-uptake", "en"),
    RetrievalCase("proline accumulation osmotic potential native landraces", "osmotic-adjustment-proline", "en"),
    RetrievalCase("QTL on chromosome 5 and DREB transcription factor", "qtl-dreb-candidate-genes", "en"),
    RetrievalCase("marker assisted selection validated in tetraploid material", "qtl-dreb-candidate-genes", "en"),
    RetrievalCase("Solanum chacoense interspecific hybrids participatory selection", "wild-relatives-breeding", "en"),
    RetrievalCase("canopy temperature thermal imagery unmanned aerial vehicles", "uav-phenotyping-canopy", "en"),
    RetrievalCase("Phytophthora infestans fungicide modes of action", "late-blight-fungicide", "en"),
    RetrievalCase("cierre estomático y ácido abscísico en papa", "stomatal-aba-andean-potato", "es"),
    RetrievalCase("arquitectura radicular y absorción de agua", "root-architecture-water-uptake", "es"),
    RetrievalCase("prolina y ajuste osmótico en variedades nativas", "osmotic-adjustment-proline", "es"),
    RetrievalCase("fenotipado con drones e imágenes térmicas", "uav-phenotyping-canopy", "es"),
]

VERIFIER_CASES = [
    VerifierCase(
        "Stomatal conductance decreased by 58 percent when soil water content fell below 60 percent of field capacity.",
        "stomatal-aba-andean-potato",
        1,
        "supported",
    ),
    VerifierCase(
        "Root length density below 40 cm explained 63 percent of the variation in tuber yield under terminal drought.",
        "root-architecture-water-uptake",
        1,
        "supported",
    ),
    VerifierCase(
        "Tolerant landraces accumulated proline up to 12 times the control level.",
        "osmotic-adjustment-proline",
        1,
        "supported",
    ),
    VerifierCase(
        "Canopy temperature measured at midday predicted final tuber yield.",
        "uav-phenotyping-canopy",
        1,
        "supported",
    ),
    VerifierCase(
        "Thermal imagery reduced the cost of drought phenotyping by 80 percent compared with manual measurements.",
        "uav-phenotyping-canopy",
        2,
        "supported",
    ),
    VerifierCase(
        "Stomatal conductance decreased by 75 percent before any visible wilting.",
        "stomatal-aba-andean-potato",
        1,
        "partial",
        "número alterado",
    ),
    VerifierCase(
        "Root length density explained 90 percent of the variation in tuber yield.",
        "root-architecture-water-uptake",
        1,
        "partial",
        "número alterado",
    ),
    VerifierCase(
        "Interspecific hybrids maintained 85 percent of their well-watered yield under drought.",
        "wild-relatives-breeding",
        1,
        "partial",
        "número alterado",
    ),
    VerifierCase(
        "Twelve QTL explained 60 percent of the phenotypic variance in tuber yield.",
        "qtl-dreb-candidate-genes",
        1,
        "partial",
        "número alterado",
    ),
    VerifierCase(
        "Late blight resistance genes were mapped on chromosome 9.",
        "stomatal-aba-andean-potato",
        1,
        "unsupported",
        "tema ajeno",
    ),
    VerifierCase(
        "Fungicide rotation doubled tuber yield in lowland environments.",
        "late-blight-fungicide",
        1,
        "unsupported",
        "afirmación inventada",
    ),
    VerifierCase(
        "Proline accumulation was the best predictor of yield in all genotypes.",
        "osmotic-adjustment-proline",
        2,
        "unsupported",
        "contradice la fuente",
    ),
]


def gold_page(slug: str, page: int) -> str:
    paper = next(paper for paper in PAPERS if paper.slug == slug)
    return " ".join(paper.pages[page - 1])


def gold_citation(slug: str) -> str:
    paper = next(paper for paper in PAPERS if paper.slug == slug)
    first = paper.authors[0][0]
    suffix = " et al." if len(paper.authors) > 2 else ""
    return f"{first}{suffix}, {paper.year}"
