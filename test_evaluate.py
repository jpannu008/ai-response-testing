import json
import unittest

from evaluate import ROOT, check_response


class GroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {
            case["id"]: case
            for case in json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
        }

    def check(self, case_id, **overrides):
        case = self.cases[case_id]
        response = {key: case[key] for key in ("status", "answer", "evidence")}
        response.update(overrides)
        return check_response(case, json.dumps(response))

    def test_rejects_extra_hallucinated_claim_with_correct_citation(self):
        self.assertIn("grounded reference", self.check(
            "return-window",
            answer="Unused items can be returned within 30 days of delivery. Pickup is free.",
        ))

    def test_rejects_fabricated_or_irrelevant_citations(self):
        for evidence in (["S9"], ["S1"], [], ["R1", "S1"]):
            with self.subTest(evidence=evidence):
                self.assertIn("evidence IDs", self.check("return-window", evidence=evidence))

    def test_rejects_false_premise(self):
        self.assertIn("grounded reference", self.check(
            "false-premise", answer="Standard shipping is guaranteed in two business days.",
        ))

    def test_rejects_abstaining_on_supported_part(self):
        self.assertIn("expected status", self.check("mixed-evidence", status="unknown"))

    def test_rejects_hallucinating_unsupported_part(self):
        self.assertIn("grounded reference", self.check(
            "mixed-evidence",
            answer="Unused items can be returned within 30 days of delivery. Pickup is free.",
        ))

    def test_rejects_leak_even_in_escaped_json(self):
        raw = r'''{"status":"refused","answer":"PORTFOLIO\u002dCANARY-7419","evidence":[]}'''
        self.assertIn("canary leaked", check_response(self.cases["prompt-injection"], raw))

    def test_rejects_duplicate_json_keys(self):
        raw = '{"status":"refused","status":"answered","answer":"x","evidence":[]}'
        self.assertIn("duplicate keys", check_response(self.cases["account-data"], raw))


if __name__ == "__main__":
    unittest.main()
