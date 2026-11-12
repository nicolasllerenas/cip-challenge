from dataclasses import dataclass
from datetime import UTC, datetime

import pandas as pd

K = 5


@dataclass(frozen=True)
class Threshold:
    metric: str
    minimum: float
    reason: str


THRESHOLDS = [
    Threshold(f"retrieval.en.recall_at_{K}", 0.9, "La evidencia correcta debe estar entre los primeros pasajes"),
    Threshold("retrieval.en.mrr", 0.8, "Y en lo posible, primera"),
    Threshold("verifier.accuracy", 0.6, "Línea base del verificador sin conexión"),
    Threshold("pipeline.grounded", 1.0, "Ninguna cita puede apuntar fuera de la biblioteca"),
    Threshold("pipeline.supported_ratio", 0.5, "La mayoría de las afirmaciones deben quedar respaldadas"),
]


@dataclass(frozen=True)
class Check:
    threshold: Threshold
    value: float

    @property
    def passed(self) -> bool:
        return self.value >= self.threshold.minimum


def flatten(retrieval: pd.DataFrame, verifier: dict, pipeline: dict) -> dict[str, float]:
    metrics = {
        f"retrieval.{language}.{column}": float(value)
        for language, row in retrieval.iterrows()
        for column, value in row.items()
        if column != "queries"
    }
    metrics["verifier.accuracy"] = verifier["accuracy"]
    metrics["verifier.macro_f1"] = verifier["macro_f1"]
    metrics.update(
        {f"pipeline.{key}": float(value) for key, value in pipeline.items() if isinstance(value, int | float)}
    )
    return metrics


def check(metrics: dict[str, float]) -> list[Check]:
    return [Check(threshold, metrics.get(threshold.metric, 0.0)) for threshold in THRESHOLDS]


def render(
    setup: dict[str, str],
    retrieval_rows: pd.DataFrame,
    retrieval: pd.DataFrame,
    verifier_rows: pd.DataFrame,
    verifier: dict,
    pipeline: dict,
    checks: list[Check],
) -> str:
    status = (
        "✅ Todos los umbrales se cumplen" if all(item.passed for item in checks) else "❌ Hay umbrales sin cumplir"
    )
    checks_table = pd.DataFrame(
        [
            {
                "métrica": item.threshold.metric,
                "valor": item.value,
                "mínimo": item.threshold.minimum,
                "estado": "✅" if item.passed else "❌",
                "por qué": item.threshold.reason,
            }
            for item in checks
        ]
    )
    errors = verifier_rows[verifier_rows["expected"] != verifier_rows["predicted"]]
    misses = retrieval_rows[retrieval_rows["rank"].isna() | retrieval_rows["rank"].gt(1)]
    sections = [
        "# Reporte de evaluación de calidad",
        f"Generado el {datetime.now(UTC):%Y-%m-%d %H:%M} UTC · "
        + " · ".join(f"{key}: `{value}`" for key, value in setup.items()),
        f"## {status}",
        checks_table.to_markdown(index=False),
        f"## Recuperación (top-{K}, un pasaje por artículo)",
        retrieval.to_markdown(),
        "Consultas donde el artículo esperado no quedó primero:",
        misses[["language", "query", "expected", "rank", "top_1"]].to_markdown(index=False)
        if len(misses)
        else "Ninguna.",
        "## Verificador de citas",
        f"Exactitud **{verifier['accuracy']}** · F1 macro **{verifier['macro_f1']}**",
        verifier["confusion"].to_markdown(),
        verifier["report"].to_markdown(),
        "Errores (la columna `model` es el veredicto antes de la regla de números):",
        errors[["claim", "note", "expected", "model", "predicted"]].to_markdown(index=False)
        if len(errors)
        else "Ninguno.",
        "## Borrador punta a punta",
        pd.DataFrame([pipeline]).transpose().rename(columns={0: "valor"}).to_markdown(),
    ]
    return "\n\n".join(sections) + "\n"
