"""Accuracy and export-boundary checks for the static results explorer."""

import json
import unittest

from scripts.build_demo import aggregate_cells, build_data, judge_counts, render


class DemoDataTests(unittest.TestCase):
    def test_published_capture_totals_match_known_snapshot(self):
        dataset = next(d for d in build_data()["attacks"] if d["id"] == "mtxA_seedmut")
        totals = {}
        for row in dataset["rows"]:
            runs, captures = totals.get(row["challenge"], (0, 0))
            totals[row["challenge"]] = (runs + row["runs"], captures + row["captures"])
        self.assertEqual(totals, {"LLM02": (33, 5), "LLM06": (33, 4), "LLM07": (28, 5)})

    def test_export_omits_prompts_responses_and_captured_evidence(self):
        cell = {"cell_key": "one", "attacker_model": "fixture/model", "challenge": "LLM02",
                "success": True, "evidence": "fixture-secret", "prompt": "fixture-prompt",
                "response": "fixture-response"}
        self.assertEqual(aggregate_cells([cell]), [
            {"model": "fixture/model", "challenge": "LLM02", "runs": 1, "captures": 1}])
        self.assertNotIn("fixture-secret", json.dumps(aggregate_cells([cell])))

    def test_duplicate_or_non_boolean_cells_are_rejected(self):
        cell = {"cell_key": "one", "attacker_model": "fixture/model", "challenge": "LLM02", "success": False}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            aggregate_cells([cell, cell])
        with self.assertRaisesRegex(ValueError, "boolean"):
            aggregate_cells([{**cell, "success": "false"}])

    def test_judge_export_preserves_counts_instead_of_rounded_scores(self):
        rows = [{"judge": "fixture/model", "tp": 3, "fp": 1, "tn": 5, "fn": 2,
                 "precision": 0, "response": "fixture-private"}]
        self.assertEqual(judge_counts(rows), [{"model": "fixture/model", "tp": 3,
                         "fp": 1, "tn": 5, "fn": 2, "errors": 0}])
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            judge_counts([{**rows[0], "fp": -1}])

    def test_data_export_is_deterministic_and_escapes_script_delimiters(self):
        self.assertEqual(render(build_data()), render(build_data()))
        self.assertNotIn("</script>", render({"model": "</script>"}))


if __name__ == "__main__":
    unittest.main()
