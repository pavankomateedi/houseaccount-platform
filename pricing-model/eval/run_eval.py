"""Evaluation harness — the pass/fail gate for the pricing model.

Reports baseline vs model on three views (see pricing.evaluation) and exits
non-zero unless the model beats baseline where it must:

1. Blended (full priced set). Gate: beat the published 11.6% baseline.
2. Held-out (unseen test split). Gate: beat baseline on the same rows.
3. Held-out "real-like" subset (high baseline APE). Informational.

Refuses synthetic data unless --allow-synthetic (which stamps the run and the
served model_version). On a passing run, writes functions/model.json.

Usage: python eval/run_eval.py [--data ...] [--seed 42] [--allow-synthetic]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pricing.data import guard_dataset, load_pricing_csv  # noqa: E402
from pricing.evaluation import PUBLISHED_BLENDED_BASELINE, Scored, evaluate  # noqa: E402

DEFAULT_DATA = ROOT / "data" / "pricing_real.csv"
DEFAULT_ARTIFACT = ROOT / "functions" / "model.json"


def _row(scored: Scored) -> str:
    verdict = "PASS" if scored.beats_baseline else "FAIL"
    return (
        f"  {scored.label:<24} n={scored.n:<5} "
        f"baseline={scored.baseline_mape * 100:6.2f}%  "
        f"model={scored.model_mape * 100:6.2f}%  [{verdict}]"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--version", default="pavan-v1.0.0")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-frac", type=float, default=0.2)
    parser.add_argument("--real-threshold", type=float, default=0.25)
    parser.add_argument("--allow-synthetic", action="store_true")
    parser.add_argument("--no-save", action="store_true", help="do not write the artifact")
    args = parser.parse_args(argv)

    frame = load_pricing_csv(args.data)
    synthetic = guard_dataset(frame, allow_synthetic=args.allow_synthetic)

    version = args.version
    if synthetic and not version.endswith("-synthetic"):
        version += "-synthetic"

    results, full_model = evaluate(
        frame,
        version=version,
        seed=args.seed,
        test_frac=args.test_frac,
        real_threshold=args.real_threshold,
    )

    if synthetic:
        print("\n" + "=" * 60)
        print("  !! SYNTHETIC DATA - model beats baseline partly by")
        print("     construction. This validates the pipeline, NOT accuracy.")
        print("=" * 60)
    print(f"\nEval: {args.data.name}  (model_version={version})\n")
    for scored in results:
        print(_row(scored))

    blended, heldout = results[0], results[1]
    pass_blended = blended.model_mape < min(blended.baseline_mape, PUBLISHED_BLENDED_BASELINE)
    pass_heldout = heldout.beats_baseline
    passed = pass_blended and pass_heldout

    print()
    print(f"  blended < {PUBLISHED_BLENDED_BASELINE:.1%} published baseline: "
          f"{'PASS' if pass_blended else 'FAIL'}")
    print(f"  held-out beats baseline:                 {'PASS' if pass_heldout else 'FAIL'}")

    if passed and not args.no_save:
        artifact = args.artifact.resolve()
        artifact.parent.mkdir(parents=True, exist_ok=True)
        full_model.save_json(artifact)
        try:
            shown = artifact.relative_to(ROOT)
        except ValueError:
            shown = artifact
        print(f"\n  artifact written: {shown}")

    print(f"\nRESULT: {'PASS' if passed else 'FAIL'}\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
