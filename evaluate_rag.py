import argparse
import json
import re
from pathlib import Path

from evaluate import ROOT, check_response, unique_object

TOP_K = 2


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.casefold()))


def retrieve(query, corpus):
    query_tokens = tokens(query)
    scores = {
        chunk_id: len(query_tokens & tokens(chunk))
        for chunk_id, chunk in corpus.items()
    }
    ranked = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))
    return [chunk_id for chunk_id in ranked if scores[chunk_id] > 0][:TOP_K]


def check_trace(case, trace, corpus):
    if not isinstance(trace, dict):
        return "missing trace", "missing response"

    retrieved = trace.get("retrieved")
    valid_retrieval = (
        isinstance(retrieved, list)
        and all(isinstance(chunk_id, str) and chunk_id in corpus for chunk_id in retrieved)
        and len(retrieved) == len(set(retrieved))
    )
    if not valid_retrieval:
        return "retrieved IDs must be unique corpus IDs", "invalid retrieval trace"

    missing = set(case["evidence"]) - set(retrieved)
    missing_distractors = set(case.get("required_distractors", [])) - set(retrieved)
    retrieval_issue = None
    if missing:
        retrieval_issue = f"missing supporting chunks: {', '.join(sorted(missing))}"
    elif missing_distractors:
        retrieval_issue = f"missing required distractors: {', '.join(sorted(missing_distractors))}"

    response_issue = check_response(case, trace.get("response"))
    if response_issue is None and missing:
        response_issue = "answer cites evidence absent from the retrieved context"
    return retrieval_issue, response_issue


def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval and grounded answers.")
    parser.add_argument("traces", nargs="?", type=Path, help="Recorded pipeline traces")
    args = parser.parse_args()

    cases = json.loads((ROOT / "rag-cases.json").read_text(encoding="utf-8"))
    corpus = json.loads((ROOT / "rag-corpus.json").read_text(encoding="utf-8"))
    try:
        if args.traces:
            traces = json.loads(
                args.traces.read_text(encoding="utf-8"), object_pairs_hook=unique_object
            )
            if not isinstance(traces, dict):
                raise ValueError("expected a JSON object keyed by case ID")
        else:
            fixtures = json.loads((ROOT / "rag-fixtures.json").read_text(encoding="utf-8"))
            traces = {
                case["id"]: {
                    "retrieved": retrieve(case["prompt"], corpus),
                    "response": fixtures[case["id"]],
                }
                for case in cases
            }
    except (OSError, ValueError) as error:
        parser.exit(2, f"Could not load RAG traces: {error}\n")

    retrieval_passes = answer_passes = 0
    for case in cases:
        retrieval_issue, response_issue = check_trace(case, traces.get(case["id"]), corpus)
        retrieval_passes += retrieval_issue is None
        answer_passes += response_issue is None
        print(
            f"{case['id']}: retrieval {retrieval_issue or 'PASS'} | "
            f"answer {response_issue or 'PASS'}"
        )

    total = len(cases)
    print(f"Retrieval {retrieval_passes}/{total} | Grounded answers {answer_passes}/{total}")
    return int(retrieval_passes != total or answer_passes != total)


if __name__ == "__main__":
    raise SystemExit(main())
