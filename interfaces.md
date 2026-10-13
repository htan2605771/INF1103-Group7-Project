# F&B Customer Complaint Triage — Function Interfaces

This document describes how the four managers fit together, the data passed
between them, and every function each module provides. If a function's inputs
or outputs need to change, tell the whole team first, because other modules
depend on these contracts.

## Pipeline overview

```
User -> io_manager -> ai_manager -> logic_manager -> data_manager
                  (orchestrated by main.py)
```

`main.process_complaint()` runs these steps for each complaint:

1. `io_manager.collect_complaint()` collects and validates the customer's input.
2. `ai_manager.get_ai_output(complaint, on_retry=...)` sends the complaint to the AI and returns validated, structured output (or a safe fallback if the AI fails).
3. `data_manager.filter_by_outlet_and_date(outlet_id, days=7)` retrieves the outlet's recent complaints (history).
4. `logic_manager.evaluate_complaint(...)` applies the business rules, then `logic_manager.calculate_score(...)` adds a priority score. The two are combined into `result`.
5. `data_manager.save_complaint(complaint, ai_output, result)` saves the full record to `complaints_data.json`.
6. `io_manager.display_result(...)` shows the final triage decision.

---

## Shared data structures

### Complaint record
Created by `io_manager`. `complaint_id` is left empty here and assigned by `data_manager.save_complaint()` the first time the complaint is saved.

```python
complaint = {
    "complaint_id": str,        # "" at collection; assigned on save, e.g. "CMP-0001"
    "name": str,
    "email": str,
    "phone": str,               # 8 digits
    "outlet_id": str,
    "datetime": str,            # incident time, ISO format e.g. "2026-09-18T14:30:00", not in the future
    "order_ref": str,           # optional, "" if not applicable
    "category": str,            # customer-selected: "food_quality" | "service" | "hygiene" | "billing" | "other"
    "description": str,         # free-text complaint
    "wants_followup": bool
}
```

### AI output
Created by `ai_manager` and validated against the schema before it is used.

```python
ai_output = {
    "ai_category": str,         # "food_quality" | "service" | "hygiene" | "billing" | "other"
    "key_details": list[str],   # e.g. ["cold food", "rude staff"]
    "severity": str,            # "low" | "medium" | "high"
    "reason": str,              # short explanation, not empty
    "reputational_risk": bool,  # true if the complaint suggests public posting/review threat
    "confidence": str           # "low" | "medium" | "high"
}
```

### Final result
Created in `main.py` from `logic_manager.evaluate_complaint()` plus the score.

```python
result = {
    "final_severity": str,      # "low" | "medium" | "high"
    "outcome": str,             # "log" | "flag_for_review" | "escalate" | "route_to_manager"
    "outlet_flagged": bool,     # true if the repeat-complaint rule triggered
    "override_applied": bool,   # true if a business rule changed the AI's result
    "override_reason": str,     # "" if no override, else the explanation
    "score": int                # priority score from calculate_score()
}
```

### Stored record
`data_manager` saves one flat record per complaint by merging the three dictionaries: `{**complaint, **ai_output, **result}`. The key names do not overlap, so the record has all 22 fields. Any field added later by another module is stored automatically.

---

## io_manager.py
Handles all communication with the user. All `print()` and `input()` calls belong here, apart from the main menu in `main.py`.

```python
def collect_complaint() -> dict:
    """Prompt for every complaint field via the terminal and validate it.
    Rejects and re-prompts on bad input: name, outlet ID and description must not
    be empty; email must match a valid format; phone must be 8 digits; incident
    datetime must be ISO format and not in the future; category must be one of
    the five options; follow-up must be Yes or No. Returns a complaint dict."""

def display_result(complaint: dict, ai_output: dict, result: dict) -> None:
    """Print the complaint details, AI analysis and final triage decision."""

def display_summary(complaints: list[dict]) -> None:
    """Print a table of stored complaint records."""

def display_ai_retry(sleep_time: int, attempt: int, max_retries: int) -> None:
    """Callback passed to ai_manager; shows a message when an AI call is retried."""
```

Single-field input helpers used by `collect_complaint()`: `get_name()`, `get_email()`, `get_phone_number()`, `get_outlet_id()`, `get_incident_datetime()`, `get_order_reference()`, `get_complaint_category()`, `get_complaint_description()`, `get_follow_up_preference()`.

---

## ai_manager.py
The only module that talks to the AI API. It contains no business rules.

```python
def build_prompt(complaint: dict) -> str:
    """Build the prompt from the complaint, asking for JSON in a fixed structure."""

def call_ai_api(prompt: str, max_retries: int = 3, on_retry=None) -> str | None:
    """Send the prompt to the Gemini API and return the response text.
    Requests a JSON response. Retries with a growing delay (2s, 4s) and calls
    on_retry(sleep_time, attempt, max_retries) before each retry. Returns None
    if the API key is missing or every attempt fails. Never raises."""

def parse_ai_response(response: str | None) -> dict | None:
    """Strip any code fences and parse the response text as JSON.
    Returns a dict, or None if the response is empty, not valid JSON, or not an object."""

def ai_output_schema() -> dict:
    """Return the expected fields, data types and allowed values."""

def check_schema_fields(ai_output: dict) -> bool:
    """True if every schema field exists, has the right type and an allowed value."""

def check_additional_rules(ai_output: dict) -> bool:
    """True if every key_details item is a string and reason is not empty."""

def validate_ai_response(ai_output: dict | None) -> bool:
    """True only if ai_output is a dict that passes both checks above."""

def fallback_ai_output(complaint: dict) -> dict:
    """Safe default used when the AI fails: customer's category, medium severity,
    low confidence, and a reason saying it needs manual review."""

def get_ai_output(complaint: dict, on_retry=None) -> dict:
    """Top-level function: build_prompt -> call_ai_api -> parse_ai_response ->
    validate_ai_response. API failures are retried in call_ai_api; if the output is still
    invalid, returns the fallback output. Always returns a valid ai_output dict."""
```

---

## logic_manager.py
Applies the business rules to the AI-enriched complaint.

```python
def evaluate_complaint(complaint: dict, ai_output: dict, history: list[dict]) -> dict:
    """Apply the business rules in order:
    1. Repeat-complaint pattern -> outlet_flagged via check_outlet_pattern(history + [complaint]).
    2. Safety keyword in the description -> severity forced to 'high', override recorded.
    3. Outcome chosen by determine_outcome().
    Returns final_severity, outcome, override_applied, override_reason, outlet_flagged."""

def calculate_score(final_severity: str, reputational_risk: bool, outlet_flagged: bool) -> int:
    """Priority score: low 10, medium 25, high 50;
    +30 for reputational risk, +20 if the outlet is flagged."""

def check_outlet_pattern(history: list[dict]) -> bool:
    """history is the outlet's complaints from the last 7 days including the
    current one. True if there are 2 or more AND at least one is hygiene
    (customer category or ai_category)."""

def determine_outcome(final_severity: str, ai_output: dict, outlet_flagged: bool, description: str) -> str:
    """First match wins:
    reputational risk -> 'route_to_manager'; outlet flagged -> 'route_to_manager';
    high severity -> 'escalate' (even if description is short);
    low AI confidence or very short description (under 10 characters or 3 words) -> 'flag_for_review';
    otherwise 'log'."""
```

`SAFETY_KEYWORDS` is the list of food-safety terms (e.g. food poisoning, allergy, cockroach) scanned for in step 2.

---

## data_manager.py
Persists complaints across runs in the flat file `complaints_data.json` (a JSON array of stored records).

```python
def generate_complaint_id(records: list[dict]) -> str:
    """Next sequential ID (CMP-0001, CMP-0002, ...): one more than the highest
    existing ID, so IDs are never reused."""

def save_complaint(complaint: dict, ai_output: dict, result: dict) -> None:
    """Assign complaint_id if it is empty (written back onto the complaint dict so
    display_result can show it), merge the three dicts into one record, and append
    it to the file."""

def load_complaints() -> list[dict]:
    """Return all stored records. Returns an empty list if the file is missing or
    corrupt, and logs a warning for a corrupt file. Never raises."""

def filter_by_outlet_and_date(outlet_id: str, days: int) -> list[dict]:
    """Return the records for one outlet whose incident datetime is within the last
    `days` days. Records with an invalid datetime are skipped."""
```

---

## main.py
Orchestrates the pipeline. It is the only file that imports all four managers.

```python
def process_complaint() -> None:
    """Run the six pipeline steps above for one complaint."""

def main() -> None:
    """Show the banner, load existing records, and run the menu loop:
    1 Submit new complaint, 2 View complaint history summary, 3 Exit."""
```

---

## Docker container
The application runs inside a Docker container so it behaves the same on any machine. Docker does not change any function interface above; it only packages and starts the same `main.py`.

### Files (repository root)
- `Dockerfile` builds the image.
- `requirements.txt` lists the Python packages installed in the image (`requests`, `python-dotenv`, `google-genai`).
- `.dockerignore` keeps `.env`, `.git`, `__pycache__` and `venv` out of the image, so the API key is never baked in.

### What the Dockerfile does
1. Starts from the official `python:3.11-slim` image.
2. Sets the working directory to `/app`.
3. Copies `requirements.txt` and runs `pip install` (done before copying the code so Docker can reuse the cached layer when only code changes).
4. Copies the rest of the project into `/app`.
5. Starts the application with `python main.py`.

### Configuration
The AI API key is read from the environment variable `GEMINI_API_KEY`. It is not stored in the image and is passed in when the container starts, from a local `.env` file containing one line, with no spaces and no quotes:

```
GEMINI_API_KEY=your_key_here
```

If no key is supplied, the application still runs: `ai_manager` logs the problem and uses its fallback output (low confidence, flagged for manual review).

### Commands

Build the image:

```
docker build -t fnb-triage .
```

Run the application (`-it` is required because the program reads input from the terminal):

```
docker run -it --rm --env-file .env fnb-triage
```

Run the application and keep saved complaints between runs (create the file first if it does not exist: `Set-Content complaints_data.json "[]"` in PowerShell):

```
docker run -it --rm --env-file .env -v "${PWD}/complaints_data.json:/app/complaints_data.json" fnb-triage
```

Run the unit tests inside the container (offline, no API key needed):

```
docker run --rm fnb-triage python test_script.py
```

### Data persistence
`data_manager` writes `complaints_data.json` inside the container at `/app`. Because the container is removed on exit (`--rm`), that file is lost unless it is mounted from the host with `-v`, as in the third command above. Mounting the file means separate runs load the records saved by earlier runs.

---

## Ground rules
1. Do not change a function's name, parameters or return type without telling the whole team.
2. All `print()` calls live in `io_manager.py` (and the main menu in `main.py`) and nowhere else. Other managers use `logging` instead.
3. Managers do not import each other; only `main.py` connects them.
4. `ai_manager` contains no business rules and `logic_manager` makes no AI calls.
5. Every module can be tested on its own; the team's `test_script.py` runs the logic and AI tests offline.