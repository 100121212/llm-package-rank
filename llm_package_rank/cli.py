from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import date

from .analysis import analyze
from .report import render_markdown
from .sampler import OpenAIResponsesClient, collect_responses, estimate_run, read_tasks


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    tasks = read_json(args.tasks)
    responses = read_json(args.responses)
    packages = read_json(args.packages)
    result = analyze(tasks, packages, responses, as_of_date=args.as_of_date)

    if args.out:
        write_text(args.out, render_markdown(result))
    else:
        print(render_markdown(result))

    if args.json_out:
        write_text(args.json_out, json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


def sample_openai(args: argparse.Namespace) -> int:
    tasks = read_tasks(args.tasks)
    estimate = estimate_run(tasks, args.model, args.max_output_tokens)
    if args.dry_run:
        print(json.dumps({"dry_run": True, **estimate}, indent=2, sort_keys=True))
        return 0
    if not args.confirm_spend:
        raise SystemExit("sample-openai requires --confirm-spend for live API calls")
    if not args.out:
        raise SystemExit("sample-openai requires --out for live sampling")
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"sample-openai requires API key in ${args.api_key_env}")

    print(json.dumps({"dry_run": False, **estimate}, indent=2, sort_keys=True), file=sys.stderr)
    client = OpenAIResponsesClient(api_key=api_key)
    responses = collect_responses(tasks, args.model, args.max_output_tokens, client)
    write_text(args.out, json.dumps(responses, indent=2, sort_keys=True) + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-package-rank",
        description="See which open-source packages LLMs recommend for coding tasks.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Analyze recommendation fixtures and generate a report.")
    run_parser.add_argument("--tasks", required=True, type=Path, help="Path to task fixture JSON.")
    run_parser.add_argument("--responses", required=True, type=Path, help="Path to model response fixture JSON.")
    run_parser.add_argument("--packages", required=True, type=Path, help="Path to package metadata JSON.")
    run_parser.add_argument("--as-of-date", type=date.fromisoformat, help="Score release recency as of YYYY-MM-DD.")
    run_parser.add_argument("--out", type=Path, help="Write a Markdown report to this path.")
    run_parser.add_argument("--json-out", type=Path, help="Write structured JSON output to this path.")
    run_parser.set_defaults(func=run)

    sample_parser = subparsers.add_parser(
        "sample-openai",
        help="Estimate or collect OpenAI model recommendations for task fixtures.",
    )
    sample_parser.add_argument("--tasks", required=True, type=Path, help="Path to task fixture JSON.")
    sample_parser.add_argument("--model", required=True, help="OpenAI model name to sample.")
    sample_parser.add_argument("--max-output-tokens", type=int, default=400)
    sample_parser.add_argument("--out", type=Path, help="Write collected model responses to this JSON path.")
    sample_parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Environment variable containing the API key.")
    sample_parser.add_argument("--dry-run", action="store_true", help="Estimate request size without API calls.")
    sample_parser.add_argument("--confirm-spend", action="store_true", help="Allow live API calls that may spend credits.")
    sample_parser.set_defaults(func=sample_openai)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
