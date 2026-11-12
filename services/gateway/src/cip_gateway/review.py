from cip_contracts import Claim, ClaimAction, ClaimReview, Draft, ReviewStatus


class InvalidReviewError(ValueError):
    pass


def reviewed_claim(claim: Claim, review: ClaimReview) -> Claim:
    match review.action:
        case ClaimAction.ACCEPT:
            return claim.model_copy(update={"review": ReviewStatus.ACCEPTED})
        case ClaimAction.REMOVE:
            return claim.model_copy(update={"review": ReviewStatus.REMOVED})
        case ClaimAction.RESTORE:
            return claim.model_copy(update={"review": ReviewStatus.PENDING})
        case ClaimAction.EDIT:
            text = (review.text or "").strip()
            if not text:
                raise InvalidReviewError("El texto editado no puede quedar vacío.")
            return claim.model_copy(update={"text": text, "review": ReviewStatus.ACCEPTED})


def apply_review(draft: Draft, claim_id: str, review: ClaimReview) -> Draft:
    sections = []
    for section in draft.sections:
        paragraphs = [
            paragraph.model_copy(
                update={
                    "claims": [
                        reviewed_claim(claim, review) if claim.claim_id == claim_id else claim
                        for claim in paragraph.claims
                    ]
                }
            )
            for paragraph in section.paragraphs
        ]
        sections.append(section.model_copy(update={"paragraphs": paragraphs}))
    return draft.model_copy(update={"sections": sections})
