# F&B Customer Complaint Triage (INF1103 Group 7)

A command-line application that collects customer complaints for an F&B chain, analyses each one with an AI model (Google Gemini), applies business rules to decide how urgent it is, and stores every record so history is available across runs.

The application is organised around four managers, each in its own module or package:

| Manager | Where | Responsibility |
|---|---|---|
| IO Manager | `io_manager/` | All terminal input and output: collecting and validating complaint details, showing results, summaries and retry messages. |
| AI Manager | `ai_manager/` | Builds the prompt, calls the AI (through an `AIClient` abstraction), parses the JSON response and validates it. Falls back safely if the AI fails. |
| Logic Manager | `logic_manager.py` | Business rules: safety-keyword override, repeat-complaint pattern at an outlet, outcome routing and priority score. |
| Data Manager | `data_manager/` | Saving, loading and filtering complaint records (`ComplaintStorage` abstract class, `ComplaintDataManager` JSON implementation). Missing or corrupt files are handled without crashing. |

`main.py` connects the four managers: collect complaint, AI analysis, load the outlet's recent history, apply business rules, save, display.

## Project layout

```
main.py                 entry point
io_manager/             IO classes (collector, validator, result/summary/retry displays)
ai_manager/             AIClient (abstract), GeminiClient, MockAIClient, ResponseValidator, AIManager
logic_manager.py        ComplaintEvaluator
data_manager/           ComplaintStorage (abstract), ComplaintDataManager (JSON file)
complaints_data.json    stored complaint records
test_*.py, pytest.ini   automated tests (run offline)
Dockerfile              container image
requirements.txt        Python dependencies
.github/workflows/      CI workflow
```

## Data passed between the managers

Each complaint is a dictionary that grows as it moves through the pipeline. `ComplaintDataManager` saves one flat record per complaint by merging the three dictionaries below (`{**complaint, **ai_output, **result}`). Their key names do not overlap.

**Complaint** (created by the IO Manager; `complaint_id` is assigned when saved, e.g. `CMP-0001`)

| Field | Type / values |
|---|---|
| `complaint_id` | str, `""` at collection |
| `name`, `email`, `phone` (8 digits), `outlet_id` | str |
| `datetime` | str, ISO format `2026-09-18T14:30:00`, not in the future |
| `order_ref` | str, optional |
| `category` | `food_quality`, `service`, `hygiene`, `billing` or `other` |
| `description` | str |
| `wants_followup` | bool |

**AI output** (created by the AI Manager and validated before use)

| Field | Type / values |
|---|---|
| `ai_category` | same five categories as above |
| `key_details` | list of str |
| `severity` | `low`, `medium` or `high` |
| `reason` | non-empty str |
| `reputational_risk` | bool |
| `confidence` | `low`, `medium` or `high` |

**Result** (created in `main.py` from the Logic Manager)

| Field | Type / values |
|---|---|
| `final_severity` | `low`, `medium` or `high` |
| `outcome` | `log`, `flag_for_review`, `escalate` or `route_to_manager` |
| `outlet_flagged` | bool, true if the repeat-complaint rule triggered |
| `override_applied`, `override_reason` | bool, str (`""` if no override) |
| `score` | int priority score |

## Credentials

The AI model needs a Gemini API key. **Never commit it.** `.env` is listed in `.gitignore` and `.dockerignore`.

Create a file named `.env` in the repository root with exactly one line (no spaces around `=`, no quotes):

```
GEMINI_API_KEY=your_key_here
```

The automated tests do not need a key. If the key is missing, the application still runs: the AI step uses a safe fallback and the complaint is flagged for manual review.

## Run the application in Docker

Docker Desktop must be running. From the repository root:

```
docker build -t fnb-triage .
docker run -it --rm --env-file .env fnb-triage
```

`-it` is required because the program asks for input in the terminal.

To keep saved complaints between runs, mount the data file (PowerShell):

```
docker run -it --rm --env-file .env -v "${PWD}/complaints_data.json:/app/complaints_data.json" fnb-triage
```

Note: the container clock is UTC, so an incident time that is only a few hours old may be rejected as "in the future". Use an earlier time when demonstrating.

## Run the automated tests

The tests run **offline**: no API key, network connection or live AI is used. AI behaviour is simulated with sample responses and a mock client, and the data tests use temporary files.

In Docker (no local setup needed):

```
docker build -t fnb-triage .
docker run --rm fnb-triage python -m pytest -v
```

Locally:

```
python -m pip install -r requirements.txt
python -m pytest -v
```

What is covered:

| File | Covers |
|---|---|
| `test_logic_manager.py` | Core logic: ambiguous input, safety override, outlet flagging, score. |
| `test_core_rules.py` | Outcome precedence, outlet pattern edge cases, score table, the multi-condition outlet rule. |
| `test_data_manager.py` | Missing, empty, corrupt and wrong-shape data files, failed writes, ID generation, filtering, abstract class behaviour and swapping storage backends. |
| `test_io_manager.py` | Input validation, re-prompting on bad input (with scripted input), result/summary/retry displays. |

`pytest.ini` limits test discovery to the offline test files. Files listed with `--ignore` are older scripts that are not yet converted to offline tests.

## Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push to `main` and every pull request into `main`:

1. **Tests (Python):** installs `requirements.txt` on Python 3.11 and runs `python -m pytest`.
2. **Tests (Docker):** builds the Docker image and runs `python -m pytest` inside the container.

Both jobs must be green before a pull request is merged. Results appear in the pull request's **Checks** section and in the repository's **Actions** tab.

## Git workflow

- Work on a branch, not directly on `main` (for example `ci-and-tests`, `ai_manager`, `io_manager`).
- Make small commits with descriptive messages.
- Open a pull request into `main`, wait for CI to pass, then merge.
- Never commit `.env` or any API key.

## Team

INF1103 Group 7. Task management and contributions are recorded in TeamAId.