"""Command-line entry points for the public CASR reference package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .controller import load_policy, recover_condition_strength
from .protocol import select_protocol, write_protocol


def _recover(args: argparse.Namespace) -> None:
    policy = load_policy(args.policy)
    payload = json.loads(args.predictions.read_text(encoding="utf-8"))
    rows = payload["utterances"] if isinstance(payload, dict) else payload
    selected = [
        row for row in rows if args.condition is None or row.get("condition") == args.condition
    ]
    result = recover_condition_strength(selected, policy, apply_calibration=not args.no_calibration)
    print(json.dumps(result, indent=2))


def _build_protocol(args: argparse.Namespace) -> None:
    protocol = select_protocol(args.data_root, seed=args.seed)
    write_protocol(protocol, args.output)
    print(args.output)


def main() -> None:
    parser = argparse.ArgumentParser(description="CASR reference implementation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    recover = subparsers.add_parser("recover", help="recover strength from utterance predictions")
    recover.add_argument("--policy", type=Path, required=True)
    recover.add_argument("--predictions", type=Path, required=True)
    recover.add_argument("--condition")
    recover.add_argument("--no-calibration", action="store_true")
    recover.set_defaults(handler=_recover)

    protocol = subparsers.add_parser("build-protocol", help="build the fixed LibriSpeech protocol")
    protocol.add_argument("--data-root", type=Path, required=True)
    protocol.add_argument("--output", type=Path, required=True)
    protocol.add_argument("--seed", type=int, default=2026)
    protocol.set_defaults(handler=_build_protocol)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
