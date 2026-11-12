from collections.abc import Sequence

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

LABELS = ["supported", "partial", "unsupported"]


def rank_of(expected: str, retrieved: Sequence[str]) -> int | None:
    return next((position for position, item in enumerate(retrieved, start=1) if item == expected), None)


def retrieval_summary(frame: pd.DataFrame, k: int) -> pd.DataFrame:
    scored = frame.assign(
        hit_at_1=frame["rank"].le(1).fillna(False),
        hit_at_k=frame["rank"].le(k).fillna(False),
        reciprocal_rank=(1 / frame["rank"]).fillna(0.0),
    )
    summary = scored.groupby("language").agg(
        queries=("query", "count"),
        recall_at_1=("hit_at_1", "mean"),
        recall_at_k=("hit_at_k", "mean"),
        mrr=("reciprocal_rank", "mean"),
    )
    return summary.rename(columns={"recall_at_k": f"recall_at_{k}"}).round(3)


def verifier_summary(frame: pd.DataFrame) -> dict:
    expected, predicted = frame["expected"], frame["predicted"]
    return {
        "accuracy": round(float(accuracy_score(expected, predicted)), 3),
        "macro_f1": round(float(f1_score(expected, predicted, labels=LABELS, average="macro", zero_division=0)), 3),
        "report": pd.DataFrame(
            classification_report(expected, predicted, labels=LABELS, output_dict=True, zero_division=0)
        )
        .transpose()
        .round(3),
        "confusion": pd.DataFrame(
            confusion_matrix(expected, predicted, labels=LABELS),
            index=[f"real: {label}" for label in LABELS],
            columns=[f"predicho: {label}" for label in LABELS],
        ),
    }
