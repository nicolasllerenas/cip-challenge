from dataclasses import dataclass, field


@dataclass(frozen=True)
class SyntheticPaper:
    slug: str
    title: str
    authors: list[tuple[str, str]]
    year: int
    journal: str
    doi: str
    pages: list[list[str]]
    references: list[str] = field(default_factory=list)


PAPERS = [
    SyntheticPaper(
        slug="stomatal-aba-andean-potato",
        title="Stomatal regulation and abscisic acid signalling in Andean potato under progressive drought",
        authors=[("Quispe", "Rosa Elena"), ("Huaman", "Carlos"), ("Vargas", "Lucia")],
        year=2019,
        journal="Synthetic Journal of Potato Physiology",
        doi="10.5555/spp.2019.0142",
        pages=[
            [
                "Drought is the main abiotic constraint for potato (Solanum tuberosum) production in the "
                "Andean highlands, where rainfed systems depend on irregular precipitation.",
                "Under progressive soil drying, potato plants closed their stomata early: stomatal "
                "conductance decreased by 58 percent when soil water content fell below 60 percent of "
                "field capacity, before any visible wilting.",
                "Leaf abscisic acid (ABA) concentration increased fourfold during the first week of water "
                "deficit and was strongly correlated with the reduction in stomatal conductance (r = -0.81).",
            ],
            [
                "Early stomatal closure protected leaf water potential but reduced net photosynthesis by "
                "45 percent, which explains part of the tuber yield penalty observed under drought.",
                "Genotypes that maintained moderate stomatal opening under mild deficit sustained higher "
                "carbon assimilation and produced 22 percent more tuber biomass than sensitive genotypes.",
                "These results suggest that the sensitivity of stomata to ABA is a useful physiological "
                "trait for selecting drought tolerant potato clones.",
            ],
        ],
        references=["Mamani, J. (2015). Water relations in tuber crops. Synthetic Agronomy, 3, 1-10."],
    ),
    SyntheticPaper(
        slug="root-architecture-water-uptake",
        title="Root system architecture determines water uptake and yield stability of potato under drought",
        authors=[("Condori", "Miguel Angel"), ("Flores", "Ana")],
        year=2021,
        journal="Synthetic Field Crops Research",
        doi="10.5555/sfcr.2021.0077",
        pages=[
            [
                "Potato has a shallow and sparse root system compared with cereals, which limits access to "
                "water stored in deeper soil layers during dry spells.",
                "In rhizotron experiments with 24 cultivars, root length density below 40 cm explained 63 "
                "percent of the variation in tuber yield under terminal drought.",
            ],
            [
                "Drought tolerant cultivars allocated more biomass to deep roots during early tuber "
                "initiation, maintaining transpiration for ten additional days after irrigation stopped.",
                "Root traits showed moderate to high broad-sense heritability (0.52 to 0.71), indicating "
                "that root architecture can be improved through breeding.",
                "We recommend combining root phenotyping with yield trials because root vigor alone did not "
                "guarantee tuber yield when heat stress coincided with drought.",
            ],
        ],
        references=["Paredes, S. (2017). Phenotyping roots in tuber crops. Synthetic Methods, 5, 22-30."],
    ),
    SyntheticPaper(
        slug="osmotic-adjustment-proline",
        title="Osmotic adjustment and proline accumulation as markers of drought tolerance in native potato",
        authors=[("Mamani", "Julia"), ("Rojas", "Pedro"), ("Ticona", "Elena"), ("Apaza", "Raul")],
        year=2018,
        journal="Synthetic Plant Stress Biology",
        doi="10.5555/spsb.2018.0310",
        pages=[
            [
                "Native potato landraces from the Peruvian Altiplano were evaluated for osmotic adjustment "
                "under controlled water deficit.",
                "Tolerant landraces accumulated proline up to 12 times the control level and lowered their "
                "osmotic potential by 0.6 MPa, which helped maintain leaf turgor.",
            ],
            [
                "Osmotic adjustment was associated with higher relative water content and with a smaller "
                "yield reduction (31 percent versus 64 percent in sensitive landraces).",
                "However, proline accumulation alone was a weak predictor of yield, because some sensitive "
                "genotypes also accumulated proline as a symptom of stress damage.",
                "Native landraces represent a valuable source of alleles for osmotic adjustment that could be "
                "introgressed into modern cultivars.",
            ],
        ],
    ),
    SyntheticPaper(
        slug="qtl-dreb-candidate-genes",
        title="QTL mapping and DREB candidate genes for drought tolerance in a diploid potato population",
        authors=[("Gutierrez", "Daniel"), ("Choque", "Maribel")],
        year=2022,
        journal="Synthetic Theoretical and Applied Genetics",
        doi="10.5555/stag.2022.0019",
        pages=[
            [
                "A diploid potato population of 180 individuals was genotyped with 8,300 SNP markers and "
                "phenotyped for tuber yield and canopy cover under well-watered and drought conditions.",
                "Twelve quantitative trait loci (QTL) for drought tolerance were detected on chromosomes 2, "
                "5 and 11, together explaining 38 percent of the phenotypic variance in tuber yield.",
            ],
            [
                "The major QTL on chromosome 5 co-localized with StDREB2, a dehydration responsive element "
                "binding transcription factor whose expression increased sixfold under drought.",
                "Markers linked to the chromosome 5 QTL are candidates for marker assisted selection, although "
                "their effect must be validated in tetraploid breeding material.",
            ],
        ],
    ),
    SyntheticPaper(
        slug="wild-relatives-breeding",
        title="Crop wild relatives and participatory breeding for drought resilient potato varieties",
        authors=[("Ccori", "Wilfredo"), ("Salazar", "Patricia"), ("Lopez", "Hugo")],
        year=2020,
        journal="Synthetic Euphytica",
        doi="10.5555/seu.2020.0458",
        pages=[
            [
                "Wild potato species such as Solanum acaule and Solanum chacoense grow in arid environments "
                "and carry adaptations to water deficit that are absent in cultivated potato.",
                "Interspecific hybrids with Solanum chacoense maintained 70 percent of their well-watered yield "
                "under drought, compared with 41 percent for the cultivated parent.",
            ],
            [
                "Participatory variety selection with farming communities in Huancavelica identified clones "
                "that combined drought tolerance with culinary quality valued by local markets.",
                "Farmer participation reduced the time needed to release a new variety by about three years, "
                "because unacceptable clones were discarded early.",
            ],
        ],
    ),
    SyntheticPaper(
        slug="uav-phenotyping-canopy",
        title="High-throughput phenotyping of potato canopy responses to drought using UAV thermal imagery",
        authors=[("Nina", "Roberto")],
        year=2023,
        journal="Synthetic Plant Phenomics",
        doi="10.5555/sphen.2023.0005",
        pages=[
            [
                "Unmanned aerial vehicles equipped with thermal and multispectral cameras were used to monitor "
                "300 potato plots under contrasting irrigation regimes.",
                "Canopy temperature measured at midday was 3.4 degrees higher in drought sensitive clones and "
                "predicted final tuber yield with an accuracy of R2 = 0.67.",
            ],
            [
                "Thermal imagery reduced the cost of drought phenotyping by 80 percent compared with manual "
                "measurements of stomatal conductance.",
                "Remote sensing indicators can accelerate breeding cycles, but they should be calibrated for "
                "each environment because cloud cover and wind affect canopy temperature.",
            ],
        ],
    ),
    SyntheticPaper(
        slug="late-blight-fungicide",
        title="Fungicide rotation strategies for late blight management in highland potato",
        authors=[("Torres", "Mariana"), ("Cruz", "Javier")],
        year=2017,
        journal="Synthetic Plant Pathology",
        doi="10.5555/spp.2017.0611",
        pages=[
            [
                "Late blight caused by Phytophthora infestans remains the most destructive disease of potato "
                "in humid highland environments.",
                "Rotating fungicides with different modes of action reduced disease severity by 35 percent and "
                "delayed the appearance of resistant pathogen strains.",
            ],
        ],
    ),
]
