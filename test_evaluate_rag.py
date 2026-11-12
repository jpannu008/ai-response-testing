import json
import unittest

from evaluate import ROOT
from evaluate_rag import check_trace, retrieve


class RagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads((ROOT / "rag-corpus.json").read_text(encoding="utf-8"))
        cls.cases = {
            case["id"]: case
            for case in json.loads((ROOT / "rag-cases.json").read_text(encoding="utf-8"))
        }
        cls.fixtures = json.loads((ROOT / "rag-fixtures.json").read_text(encoding="utf-8"))

    def test_baseline_retrieval_and_fixture_responses(self):
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                trace = {
                    "retrieved": retrieve(case["prompt"], self.corpus),
                    "response": self.fixtures[case_id],
                }
                self.assertEqual(check_trace(case, trace, self.corpus), (None, None))

    def test_correct_answer_cannot_cite_unretrieved_source(self):
        trace = {"retrieved": ["R1"], "response": self.fixtures["multi-source"]}
        retrieval_issue, answer_issue = check_trace(self.cases["multi-source"], trace, self.corpus)
        self.assertIn("R2", retrieval_issue)
        self.assertIn("absent from the retrieved context", answer_issue)

    def test_injection_case_requires_the_untrusted_chunk(self):
        trace = {"retrieved": ["R1"], "response": self.fixtures["retrieved-injection"]}
        retrieval_issue, answer_issue = check_trace(self.cases["retrieved-injection"], trace, self.corpus)
        self.assertIn("X1", retrieval_issue)
        self.assertIsNone(answer_issue)

    def test_retrieved_instructions_cannot_override_policy(self):
        response = json.loads(self.fixtures["retrieved-injection"])
        response["answer"] = "The return window is 90 days."
        trace = {"retrieved": ["R1", "X1"], "response": json.dumps(response)}
        retrieval_issue, answer_issue = check_trace(self.cases["retrieved-injection"], trace, self.corpus)
        self.assertIsNone(retrieval_issue)
        self.assertIn("grounded reference", answer_issue)


if __name__ == "__main__":
    unittest.main()
