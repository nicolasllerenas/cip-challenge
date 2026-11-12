import pandas as pd
from cip_evals.metrics import rank_of, retrieval_summary, verifier_summary
from cip_evals.report import THRESHOLDS, check
from cip_evals.run import evaluate, main


def test_rank_of_is_one_based_and_none_when_missing():
    assert rank_of("b", ["a", "b", "c"]) == 2
    assert rank_of("z", ["a", "b"]) is None


def test_retrieval_summary_computes_recall_and_mrr_per_language():
    rows = pd.DataFrame(
        [
            {"query": "q1", "language": "en", "rank": 1},
            {"query": "q2", "language": "en", "rank": 2},
            {"query": "q3", "language": "es", "rank": None},
        ]
    ).astype({"rank": "Float64"})

    summary = retrieval_summary(rows, 5)

    assert summary.loc["en", "recall_at_1"] == 0.5
    assert summary.loc["en", "recall_at_5"] == 1.0
    assert summary.loc["en", "mrr"] == 0.75
    assert summary.loc["es", "mrr"] == 0.0


def test_verifier_summary_reports_confusion_matrix():
    rows = pd.DataFrame(
        {"expected": ["supported", "partial", "unsupported"], "predicted": ["supported", "partial", "partial"]}
    )

    summary = verifier_summary(rows)

    assert summary["accuracy"] == 0.667
    assert summary["confusion"].loc["real: unsupported", "predicho: partial"] == 1


def test_missing_metrics_fail_their_threshold():
    checks = check({})

    assert len(checks) == len(THRESHOLDS)
    assert not any(item.passed for item in checks)


def test_offline_evaluation_meets_every_threshold():
    report, passed = evaluate("offline", "hashing")

    assert passed, report
    assert "## Verificador de citas" in report


def test_cli_writes_the_report(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    output = tmp_path / "report.md"

    assert main(["--output", str(output)]) == 0
    assert output.read_text().startswith("# Reporte de evaluación de calidad")
