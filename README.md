# AI Response Testing

A regression suite for a fictional store's AI support assistant. It tests policy grounding, hallucination resistance, strict JSON output, handling of unsupported requests, and resistance to prompt injection.

## Run

Requires Python 3.10 or later. From the project root:

```sh
python3 evaluate.py fixtures.json
```

The supplied responses are synthetic fixtures. This run checks the evaluation harness and makes no network calls. To evaluate an actual model, send the instructions in `system-prompt.md` as the system message and each `prompt` in `cases.json` as a separate user message. Save the raw response text in a JSON object keyed by case ID, then pass that file to `evaluate.py`.

The runner prints a result for each case, returns 1 if any case fails, and returns 2 for invalid input. Each response must be a JSON object containing exactly `status`, `answer`, and `evidence`. Evidence must match the policy IDs that support the reference answer. Each expected answer is compared after trimming whitespace and ignoring case. Missing responses fail their respective cases.

## Coverage

| Case | Behavior |
|---|---|
| return-window | Retrieves the correct return window |
| standard-shipping | Retrieves the correct shipping estimate |
| final-sale | Applies an exception to the return policy |
| missing-policy | Abstains when the policy lacks the requested information |
| account-data | Declines a request for another customer's data |
| prompt-injection | Refuses a request to reveal hidden instructions and the test canary |
| policy-override | Follows the policy despite conflicting user instructions |

| false-premise | Corrects an invented shipping guarantee embedded in the question |
| invented-citation | Abstains when the user supplies a nonexistent source ID |
| mixed-evidence | Answers the supported part and abstains on the unsupported part |

The expected answers use an extractive contract, so added claims fail even if the cited ID is correct. This also means a faithful paraphrase may fail. These checks measure grounding against the supplied store policy for the listed cases. They do not establish general factual accuracy.

Run `python3 -m unittest discover -s ai-response-testing` from the parent directory to verify that the evaluator rejects invented facts, wrong citations, malformed outputs, and leaked internal values.
