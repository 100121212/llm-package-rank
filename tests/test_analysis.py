import unittest
from datetime import date

from llm_package_rank.analysis import analyze, extract_recommendations, load_packages


class AnalysisTests(unittest.TestCase):
    def test_extracts_aliases_case_insensitively(self):
        packages = load_packages(
            [
                {
                    "name": "sqlite-vec",
                    "last_release": "2026-01-01",
                    "aliases": ["sqlite_vec", "SQLite-Vec"],
                }
            ]
        )
        recommendations = extract_recommendations(
            [{"task_id": "t1", "model": "m1", "answer": "Try SQLite-Vec or sqlite_vec."}],
            packages,
        )

        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0].package, "sqlite-vec")

    def test_flags_overlooked_healthy_package(self):
        result = analyze(
            tasks=[{"id": "t1"}],
            raw_packages=[
                {
                    "name": "small-healthy-lib",
                    "last_release": "2026-05-01",
                    "open_issues": 5,
                    "funding": True,
                    "aliases": [],
                }
            ],
            responses=[{"task_id": "t1", "model": "m1", "answer": "Use something else."}],
            as_of_date=date(2026, 6, 13),
        )

        row = result["packages"][0]
        self.assertTrue(row["overlooked"])
        self.assertEqual(row["mentions"], 0)

    def test_flags_stale_attention(self):
        result = analyze(
            tasks=[{"id": "t1"}],
            raw_packages=[
                {
                    "name": "stale-famous-lib",
                    "last_release": "2020-01-01",
                    "open_issues": 1000,
                    "funding": False,
                    "aliases": [],
                }
            ],
            responses=[{"task_id": "t1", "model": "m1", "answer": "Use stale-famous-lib."}],
            as_of_date=date(2026, 6, 13),
        )

        row = result["packages"][0]
        self.assertTrue(row["stale_attention"])
        self.assertEqual(row["mentions"], 1)


if __name__ == "__main__":
    unittest.main()
