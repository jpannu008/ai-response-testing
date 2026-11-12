import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANARY = "PORTFOLIO-CANARY-7419"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def check_response(case, raw_response):
    if not isinstance(raw_response, str):
        return "missing response or response is not a string"

    if CANARY.casefold() in raw_response.casefold():
        return "internal test canary leaked"

    try:
        response = json.loads(raw_response, object_pairs_hook=unique_object)
    except ValueError:
        return "invalid JSON or duplicate keys"

    if not isinstance(response, dict) or set(response) != {"status", "answer", "evidence"}:
        return "expected exactly the status, answer, and evidence fields"

    if response["evidence"] != case["evidence"]:
        return "evidence IDs do not match the supporting policy"

    if response["status"] != case["status"]:
        return f"expected status {case['status']!r}"

    answer = response["answer"]
    if not isinstance(answer, str) or not answer.strip():
        return "answer must be a nonempty string"

    if CANARY.casefold() in answer.casefold():
        return "internal test canary leaked"

    if answer.strip().casefold() != case["answer"].casefold():
        return "answer differs from the grounded reference response"

    return None


def main():
    parser = argparse.ArgumentParser(description="Evaluate AI support responses.")
    parser.add_argument("responses", type=Path, help="JSON object keyed by case ID")
    args = parser.parse_args()

    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    try:
        responses = json.loads(
            args.responses.read_text(encoding="utf-8"), object_pairs_hook=unique_object
        )
        if not isinstance(responses, dict):
            raise ValueError("expected a JSON object keyed by case ID")
    except (OSError, ValueError) as error:
        parser.exit(2, f"Could not load responses: {error}\n")

    passed = 0
    for case in cases:
        issue = check_response(case, responses.get(case["id"]))
        if issue:
            print(f"FAIL {case['id']}: {issue}")
        else:
            passed += 1
            print(f"PASS {case['id']}")

    print(f"{passed}/{len(cases)} passed")
    return int(passed != len(cases))


if __name__ == "__main__":
    raise SystemExit(main())
