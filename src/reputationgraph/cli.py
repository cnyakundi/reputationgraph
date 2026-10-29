from __future__ import annotations

import argparse
import json
from pathlib import Path

from reputationgraph.models import AnalysisRequest
from reputationgraph.pipeline import analyze
from reputationgraph.report import render_html


def main() -> None:
    parser = argparse.ArgumentParser(prog="reputationgraph")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze", help="analyze a JSON mentions file")
    analyze_parser.add_argument("input", type=Path)
    analyze_parser.add_argument("--subject", required=True)
    analyze_parser.add_argument("--output", type=Path, default=Path("brief.html"))
    analyze_parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    mentions = json.loads(args.input.read_text(encoding="utf-8"))
    result = analyze(AnalysisRequest(subject=args.subject, mentions=mentions))
    args.output.write_text(render_html(result), encoding="utf-8")
    if args.json_output:
        args.json_output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(f"Analyzed {result.mention_count} mentions; overall risk {result.overall_risk}/100")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
