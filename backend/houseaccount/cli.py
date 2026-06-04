"""Command-line entry points: build the corpus and run the eval.

    python -m houseaccount.cli gen
    python -m houseaccount.cli eval [--mode mock|live]
"""

from __future__ import annotations

import argparse
import sys

from .corpus.build import build_and_save, load_golden
from .eval.harness import evaluate
from .intel.engine import get_classifier


def _cmd_gen(_: argparse.Namespace) -> int:
    n_corpus, n_golden = build_and_save()
    print(f"generated corpus={n_corpus} golden={n_golden}")
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    golden = load_golden()
    classifier = get_classifier(args.mode)
    report = evaluate(golden, classifier)
    print(report.summary())
    return 0 if report.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="houseaccount")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("gen", help="generate corpus + golden set").set_defaults(func=_cmd_gen)

    p_eval = sub.add_parser("eval", help="run eval against the golden set")
    p_eval.add_argument("--mode", choices=["mock", "live"], default=None)
    p_eval.set_defaults(func=_cmd_eval)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
