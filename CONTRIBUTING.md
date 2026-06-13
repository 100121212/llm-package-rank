# Contributing

LLM Package Rank is early. The best contributions are small, reproducible benchmark
improvements.

## Good First Contributions

- Add task prompts for one ecosystem.
- Add package metadata fixtures for a known package category.
- Improve package mention extraction.
- Add tests for ambiguous package names.
- Improve report language for maintainers.

## Development

Run the test suite:

```bash
python3 -m unittest discover -s tests
```

Generate the sample report:

```bash
python3 -m llm_package_rank.cli run \
  --tasks fixtures/tasks.json \
  --responses fixtures/responses.json \
  --packages fixtures/packages.json \
  --as-of-date 2026-06-13 \
  --out reports/sample.md \
  --json-out reports/sample.json
```

Check a live sampling estimate without spending API credits:

```bash
python3 -m llm_package_rank.cli sample-openai \
  --tasks fixtures/tasks.json \
  --model <openai-model> \
  --dry-run
```

## Safety

API-backed samplers are explicitly opt-in, print an estimate before running,
and write reproducible run artifacts. Do not add commands that spend credits by
default.
