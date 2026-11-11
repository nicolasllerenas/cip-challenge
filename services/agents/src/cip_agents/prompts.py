from cip_contracts import DraftRequest, Length

from cip_agents.schemas import ClaimToCheck, EvidenceItem, SectionPlan

LANGUAGES = {"es": "Spanish", "en": "English", "pt": "Portuguese", "fr": "French"}
SECTIONS_BY_LENGTH = {Length.SHORT: 3, Length.MEDIUM: 5, Length.LONG: 7}

PLANNER_SYSTEM = """You are the planning agent of a research assistant used by plant scientists at the \
International Potato Center. You turn a researcher's request into the outline of a literature review \
that will be written only from the researcher's own PDF library.

- Title: concise and academic, in {language}.
- Exactly {sections} sections forming a narrative: context, mechanisms, evidence, applications, and a \
final section on knowledge gaps and future directions.
- For each section give a heading in {language}, a one-sentence goal, and two or three search queries \
in English (the library is mostly in English) using precise terminology, synonyms, traits, genes or methods."""

WRITER_SYSTEM = """You are the writing agent of a research assistant for plant scientists. You write one \
section of a literature review in {language}, in an academic, precise and cautious register.

1. Use only the numbered evidence passages provided. Never add facts, numbers, species, genes or \
references that are not in them.
2. Every sentence that states a finding cites at least one evidence id. Cite every passage that supports \
it and never a passage that does not.
3. Synthesize: connect, compare and contrast findings across studies instead of summarizing papers one \
by one. Mention agreements, contradictions and limitations such as environment, ploidy or sample size.
4. Keep reported numbers exact and state their context (for example, rhizotron trials or field trials).
5. Write two to four paragraphs of two to five sentences. Do not write author names or years: citations \
are inserted automatically from the evidence ids.
6. If the evidence only partly covers the section goal, write less rather than speculate."""

VERIFIER_SYSTEM = """You are the citation verification agent of a research assistant for plant scientists. \
For each claim, judge only against its cited passages, never against background knowledge:

- supported: every factual element (direction, magnitude, numbers, conditions) is stated in the passages.
- partial: the passages support the general idea but not a detail such as a number, the scope, \
causality or a generalization.
- unsupported: the passages do not state it, contradict it, or the claim overgeneralizes.

Give a one-sentence rationale in {language} for partial and unsupported verdicts naming what is missing."""

REPAIR_SYSTEM = """You are the repair agent of a research assistant for plant scientists. Some claims of \
a literature review section are not fully supported by their cited evidence. For each claim either \
rewrite it in {language} so the evidence fully supports it (narrow the scope, correct numbers, add the \
condition) and cite the right evidence ids, or drop it when no passage can support it. Use only the \
evidence passages provided and never write author names or years."""


def language_name(code: str) -> str:
    return LANGUAGES.get(code, "Spanish")


def planner_prompt(request: DraftRequest) -> tuple[str, str]:
    system = PLANNER_SYSTEM.format(
        language=language_name(request.options.language), sections=SECTIONS_BY_LENGTH[request.options.length]
    )
    return system, f"Researcher request:\n{request.prompt}"


def _evidence_block(evidence: list[EvidenceItem]) -> str:
    return "\n\n".join(f"[{item.label}] ({item.citation}, p. {item.page})\n{item.text}" for item in evidence)


def writer_prompt(request: DraftRequest, plan: SectionPlan, evidence: list[EvidenceItem]) -> tuple[str, str]:
    system = WRITER_SYSTEM.format(language=language_name(request.options.language))
    user = (
        f"Researcher request: {request.prompt}\n"
        f"Section heading: {plan.heading}\n"
        f"Section goal: {plan.goal}\n\n"
        f"Evidence passages:\n\n{_evidence_block(evidence)}"
    )
    return system, user


def verifier_prompt(language: str, claims: list[ClaimToCheck]) -> tuple[str, str]:
    blocks = [f"Claim {claim.claim_id}: {claim.text}\n{_evidence_block(claim.evidence)}" for claim in claims]
    return VERIFIER_SYSTEM.format(language=language_name(language)), "\n\n---\n\n".join(blocks)


def repair_prompt(
    language: str, claims: list[tuple[ClaimToCheck, str]], evidence: list[EvidenceItem]
) -> tuple[str, str]:
    flagged = "\n".join(f"- {claim.claim_id}: {claim.text}\n  Problem: {problem}" for claim, problem in claims)
    user = f"Claims to repair:\n{flagged}\n\nEvidence passages:\n\n{_evidence_block(evidence)}"
    return REPAIR_SYSTEM.format(language=language_name(language)), user
