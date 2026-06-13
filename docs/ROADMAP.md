# Roadmap

## 0.1 Offline Benchmark

- Deterministic fixture-based benchmark.
- Markdown and JSON reports.
- Package metadata scoring for release recency, issue load, and funding status.
- Flags for overlooked healthy packages and stale packages receiving attention.
- Opt-in OpenAI sampler with dry-run estimates and cached response artifacts.

## 0.2 Live Sampling

- Store prompt text, model names, and answer metadata in richer run artifacts.
- Support repeat runs for drift measurement.
- Add model pricing presets for dollar estimates before API calls.

## 0.3 Ecosystem Adapters

- Fetch GitHub repository metadata for packages.
- Fetch package metadata for Python, npm, Rust, and Go.
- Join funding metadata from `FUNDING.yml` and public sponsor fields.
- Cache external metadata locally.

## 0.4 Maintainer Report

- Accept a target package or repository URL.
- Generate a discoverability report against task suites in the same ecosystem.
- Suggest documentation changes that improve accurate model retrieval.
- Compare model answers before and after README/example changes.
