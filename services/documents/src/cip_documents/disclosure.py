from cip_contracts import Draft


def ai_disclosure(draft: Draft) -> str:
    stats = draft.stats
    models = ", ".join(sorted(set(draft.models.values()))) or "modelos de lenguaje"
    review = (
        f" {stats.pending_review} afirmaciones están resaltadas con comentarios para tu revisión."
        if stats.pending_review
        else ""
    )
    return (
        f"Este borrador fue generado el {draft.created_at:%d/%m/%Y} por el Asistente de Investigación CIP "
        f"({models}) usando únicamente {stats.sources} artículos de tu biblioteca. "
        f"Cada afirmación fue contrastada automáticamente con el pasaje citado: {stats.supported} respaldadas, "
        f"{stats.partial} con respaldo parcial y {stats.unsupported} sin respaldo.{review} "
        "Quien firme el documento debe validar su contenido antes de usarlo o publicarlo."
    )
