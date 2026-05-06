"""Command-line interface for VIX analysis."""

from __future__ import annotations

import argparse
import json

from vix_alert.analyzer import VIXAnalyzer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch and analyze VIX data")
    parser.add_argument(
        "--period",
        default="1y",
        help="Historical period to analyze, e.g. 1y, 6mo, 30d",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output statistics as JSON",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    analyzer = VIXAnalyzer()
    analyzer.fetch_data(period=args.period)
    analyzer.calculate_statistics()

    if args.json:
        print(json.dumps(analyzer.to_dict(), indent=2))
    else:
        print(analyzer.get_summary())


if __name__ == "__main__":
    main()
