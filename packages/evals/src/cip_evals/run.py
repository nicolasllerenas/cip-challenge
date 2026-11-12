import argparse
import os
import sys
import tempfile
from pathlib import Path

from cip_agents.config import Settings as AgentsSettings
from cip_agents.models import AnthropicModel, LanguageModel
from cip_agents.offline import OfflineModel
from cip_agents.routing import ModelRouter

from cip_evals.gold import RETRIEVAL_CASES, VERIFIER_CASES
from cip_evals.metrics import retrieval_summary, verifier_summary
from cip_evals.report import K, check, flatten, render
from cip_evals.suites import pipeline_suite, prepare, retrieval_suite, verifier_suite


def build_model(provider: str) -> LanguageModel:
    if provider == "anthropic":
        return AnthropicModel(ModelRouter(AgentsSettings()))
    return OfflineModel()


def evaluate(provider: str, embedder: str) -> tuple[str, bool]:
    model = build_model(provider)
    with tempfile.TemporaryDirectory() as folder:
        workspace = prepare(Path(folder), embedder)
        retrieval_rows = retrieval_suite(workspace, RETRIEVAL_CASES, K)
        verifier_rows = verifier_suite(model, VERIFIER_CASES)
        pipeline = pipeline_suite(workspace, model)
    retrieval = retrieval_summary(retrieval_rows, K)
    verifier = verifier_summary(verifier_rows)
    checks = check(flatten(retrieval, verifier, pipeline))
    setup = {"modelo": provider, "embeddings": embedder, "artículos": "corpus sintético de cip-testkit"}
    report = render(setup, retrieval_rows, retrieval, verifier_rows, verifier, pipeline, checks)
    return report, all(item.passed for item in checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evalúa recuperación, verificación de citas y borradores.")
    parser.add_argument("--provider", choices=["offline", "anthropic"], default="offline")
    parser.add_argument("--embedder", choices=["hashing", "fastembed"], default="hashing")
    parser.add_argument("--output", type=Path, default=Path("eval-report.md"))
    args = parser.parse_args(argv)
    if args.provider == "anthropic":
        print("Aviso: esta evaluación llama a la API de Claude y tiene costo.", file=sys.stderr)
    report, passed = evaluate(args.provider, args.embedder)
    args.output.write_text(report)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a") as handle:
            handle.write(report)
    print(f"{'Umbrales cumplidos' if passed else 'Umbrales NO cumplidos'} · reporte en {args.output}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
