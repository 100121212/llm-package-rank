import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from llm_package_rank.cli import main
from llm_package_rank.sampler import collect_responses, extract_output_text


class FakeClient:
    def create_response(self, model, prompt, max_output_tokens):
        return f"Answer from {model}: use typer and click."


class SamplerCliTests(unittest.TestCase):
    def test_openai_dry_run_prints_estimate_without_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp) / "tasks.json"
            tasks.write_text(
                json.dumps(
                    [
                        {"id": "one", "prompt": "Which package should I use for charts?"},
                        {"id": "two", "prompt": "Which package should I use for CLIs?"},
                    ]
                ),
                encoding="utf-8",
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "sample-openai",
                        "--tasks",
                        str(tasks),
                        "--model",
                        "test-model",
                        "--dry-run",
                    ]
                )

        self.assertEqual(exit_code, 0)
        estimate = json.loads(stdout.getvalue())
        self.assertTrue(estimate["dry_run"])
        self.assertEqual(estimate["model"], "test-model")
        self.assertEqual(estimate["task_count"], 2)
        self.assertGreater(estimate["estimated_total_tokens"], 0)

    def test_openai_sampling_requires_explicit_spend_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp) / "tasks.json"
            tasks.write_text(json.dumps([{"id": "one", "prompt": "Which package?"}]), encoding="utf-8")

            with self.assertRaises(SystemExit) as error:
                main(
                    [
                        "sample-openai",
                        "--tasks",
                        str(tasks),
                        "--model",
                        "test-model",
                    ]
                )

        self.assertIn("--confirm-spend", str(error.exception))

    def test_openai_sampling_requires_api_key_env_after_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp) / "tasks.json"
            tasks.write_text(json.dumps([{"id": "one", "prompt": "Which package?"}]), encoding="utf-8")

            old_value = os.environ.pop("LLM_PACKAGE_RANK_TEST_KEY", None)
            try:
                with self.assertRaises(SystemExit) as error:
                    main(
                        [
                            "sample-openai",
                            "--tasks",
                            str(tasks),
                            "--model",
                            "test-model",
                            "--api-key-env",
                            "LLM_PACKAGE_RANK_TEST_KEY",
                            "--confirm-spend",
                            "--out",
                            str(Path(tmp) / "responses.json"),
                        ]
                    )
            finally:
                if old_value is not None:
                    os.environ["LLM_PACKAGE_RANK_TEST_KEY"] = old_value

        self.assertIn("LLM_PACKAGE_RANK_TEST_KEY", str(error.exception))

    def test_collect_responses_matches_analysis_fixture_shape(self):
        responses = collect_responses(
            tasks=[{"id": "cli-framework", "prompt": "Which package for a CLI?"}],
            model="test-model",
            max_output_tokens=100,
            client=FakeClient(),
        )

        self.assertEqual(
            responses,
            [
                {
                    "task_id": "cli-framework",
                    "model": "test-model",
                    "answer": "Answer from test-model: use typer and click.",
                }
            ],
        )

    def test_extracts_responses_api_output_text(self):
        payload = {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": "Use typer for typed CLIs."},
                        {"type": "refusal", "refusal": "ignored"},
                    ]
                }
            ]
        }

        self.assertEqual(extract_output_text(payload), "Use typer for typed CLIs.")


if __name__ == "__main__":
    unittest.main()
