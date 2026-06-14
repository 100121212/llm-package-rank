# LLM Package Rank

See which open-source packages LLMs recommend for coding tasks.

Developers increasingly ask LLMs which libraries, frameworks, and tools to use.
That turns model recommendations into a new discovery channel for open-source
packages. LLM Package Rank helps maintainers test whether their package is
visible in that channel, whether models over-recommend stale defaults, and which
healthy packages are being ignored.

## What It Does

- Runs a benchmark of realistic development tasks.
- Reads model recommendation answers from JSON fixtures or future API adapters.
- Extracts mentioned packages.
- Joins recommendations with package metadata such as stars, release recency,
  funding status, and maintenance health.
- Produces a report on recommendation share, stale recommendations, and
  overlooked packages.

The current MVP ships with sample tasks and sample model answers so the scoring
and report format can be reviewed without API keys. It also includes an opt-in
OpenAI sampler for collecting real model answers.

## Quick Start

```bash
python3 -m llm_package_rank.cli run \
  --tasks fixtures/tasks.json \
  --responses fixtures/responses.json \
  --packages fixtures/packages.json \
  --as-of-date 2026-06-13 \
  --out reports/sample.md \
  --json-out reports/sample.json
```

Run tests:

```bash
python3 -m unittest discover -s tests
```

Estimate a live OpenAI sampling run without spending credits:

```bash
python3 -m llm_package_rank.cli sample-openai \
  --tasks fixtures/tasks.json \
  --model <openai-model> \
  --dry-run
```

Collect live model answers after reviewing the estimate:

```bash
python3 -m llm_package_rank.cli sample-openai \
  --tasks fixtures/tasks.json \
  --model <openai-model> \
  --out runs/openai-responses.json \
  --confirm-spend
```

Live sampling reads the API key from `OPENAI_API_KEY` by default. Use
`--api-key-env NAME` to point at a different environment variable. The key is
never written to run artifacts.

## Sample Output

The included fixtures produce [a sample Markdown report](reports/sample.md) and
[a sample JSON report](reports/sample.json) that can identify:

- `cyclopts` as a high-maintenance CLI package that received no sample model
  recommendations.
- `faiss` as a package that still receives attention despite a weak maintenance
  signal in the sample metadata.
- `sqlite-vec` as a healthy embedded vector-search package that receives less
  attention than larger defaults.

## Example Questions

LLM Package Rank can answer questions like:

- Which packages dominate model recommendations for a task family?
- Are models still recommending stale or under-maintained libraries?
- Which active, well-documented packages are invisible to model suggestions?
- Does a package's README positioning match the words developers use when
  asking coding assistants for help?

## Status

This repository is an early MVP. The immediate roadmap is:

1. Add package registry and GitHub metadata adapters.
2. Add prompt suites for common OSS ecosystems.
3. Add a maintainer-facing discoverability report for one target package.
4. Add trend reports that compare recommendation drift over time.

## Why This Matters

AI coding assistants are becoming an attention layer between developers and
package maintainers. If that layer systematically favors old defaults or
already-famous packages, small but healthy packages become harder to discover.
LLM Package Rank turns that concern into something measurable.
