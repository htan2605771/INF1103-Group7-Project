"""Offline tests for the new feature: customer complaint form + manager dashboard (Flask GUI).

Every test uses a temporary data file, so the real complaints_data.json is never touched,
and the AI is replaced by a stub, so no API key or network is needed.
"""

import os
from datetime import datetime, timedelta

import pytest

import app as app_module
from data_manager import ComplaintDataManager, MerchantConfigManager

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merchant_config.json")
FMT = "%Y-%m-%dT%H:%M:%S"

AI_OUTPUT = {
    "ai_category": "service", "key_details": ["slow"], "severity": "low",
    "reason": "Minor delay.", "reputational_risk": False, "confidence": "high",
}


class StubAI:
    """Stands in for AIManager: always returns a valid AI output."""

    def get_ai_output(self, complaint, on_retry=None):
        return dict(AI_OUTPUT)


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # anything written by relative path lands in the temp folder
    storage = ComplaintDataManager(str(tmp_path / "complaints_data.json"))
    monkeypatch.setattr(app_module, "db_manager", storage)
    monkeypatch.setattr(app_module, "config_manager", MerchantConfigManager(CONFIG_PATH))
    monkeypatch.setattr(app_module, "ai", StubAI())
    return storage


@pytest.fixture
def client(store):
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


@pytest.fixture
def manager(client):
    with client.session_transaction() as session:
        session["manager_logged_in"] = True
    return client


def add_complaint(store, **overrides):
    complaint = {
        "complaint_id": "", "name": "Ann Lee", "email": "ann@example.com", "phone": "91234567",
        "outlet_id": "OUT-001", "datetime": (datetime.now() - timedelta(hours=5)).strftime(FMT),
        "order_ref": "", "category": "service", "description": "Staff were slow to serve us today.",
        "wants_followup": False, "is_addressed": False,
    }
    complaint.update(overrides)
    result = {"final_severity": "low", "outcome": "log", "outlet_flagged": False,
              "override_applied": False, "override_reason": "", "score": 10}
    store.save_complaint(complaint, AI_OUTPUT, result)
    return complaint["complaint_id"]


def stored(store, complaint_id):
    return next(r for r in store.load_complaints() if r["complaint_id"] == complaint_id)


def form(**overrides):
    data = {
        "name": "Ann Lee", "email": "ann@example.com", "phone": "91234567", "outlet_id": "OUT-001",
        "incident_datetime": (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M"),
        "order_reference": "ORD-1", "category": "food quality",
        "description": "The soup was cold when it arrived.", "wants_followup": "yes",
    }
    data.update(overrides)
    return data


# ---------- manager login ----------
def test_wrong_password_is_rejected(client):
    response = client.post("/manager-login", data={"password": "wrong"})
    assert response.status_code == 200
    assert b"Incorrect password" in response.data


def test_correct_password_logs_in_and_redirects_to_dashboard(client):
    response = client.post("/manager-login", data={"password": app_module.MANAGER_PASSWORD})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/manager")


def test_logout_removes_access(manager):
    manager.get("/manager-logout")
    assert manager.get("/manager").status_code == 302


@pytest.mark.parametrize("path", ["/manager", "/manager/outlet/OUT-001"])
def test_manager_pages_require_login(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/manager-login" in response.headers["Location"]


def test_resolve_requires_login_and_changes_nothing(client, store):
    cid = add_complaint(store)
    response = client.post(f"/manager/resolve/{cid}")
    assert response.status_code == 302
    assert "/manager-login" in response.headers["Location"]
    assert stored(store, cid)["is_addressed"] is False


# ---------- dashboard ----------
def test_dashboard_lists_configured_outlets(manager, store):
    add_complaint(store)
    response = manager.get("/manager")
    assert response.status_code == 200
    assert b"Jewel Changi" in response.data


def test_unknown_outlet_returns_404(manager):
    assert manager.get("/manager/outlet/OUT-999").status_code == 404


def test_outlet_page_shows_active_complaints_only(manager, store):
    add_complaint(store, description="ACTIVE-COMPLAINT-TEXT")
    add_complaint(store, description="RESOLVED-COMPLAINT-TEXT", is_addressed=True)
    page = manager.get("/manager/outlet/OUT-001").data
    assert b"ACTIVE-COMPLAINT-TEXT" in page
    assert b"RESOLVED-COMPLAINT-TEXT" not in page


# ---------- resolve / follow-up ----------
def test_resolve_marks_complaint_as_addressed_and_persists(manager, store):
    cid = add_complaint(store)
    response = manager.post(f"/manager/resolve/{cid}")
    assert response.status_code == 302
    assert stored(store, cid)["is_addressed"] is True


def test_resolve_is_blocked_while_a_follow_up_is_pending(manager, store):
    cid = add_complaint(store, wants_followup=True)
    manager.post(f"/manager/resolve/{cid}")
    assert stored(store, cid)["is_addressed"] is False


def test_clearing_follow_up_then_resolving_works(manager, store):
    cid = add_complaint(store, wants_followup=True)
    manager.post(f"/manager/resolve-followup/{cid}")
    assert stored(store, cid)["wants_followup"] is False
    manager.post(f"/manager/resolve/{cid}")
    assert stored(store, cid)["is_addressed"] is True


def test_resolving_an_unknown_complaint_does_not_touch_the_data_file(manager, store):
    add_complaint(store)
    with open(store.data_file) as f:
        before = f.read()
    response = manager.post("/manager/resolve/CMP-9999")
    assert response.status_code == 302
    with open(store.data_file) as f:
        assert f.read() == before


# ---------- customer complaint form ----------
@pytest.mark.parametrize("field,value,message", [
    ("name", "", b"Name cannot be empty"),
    ("email", "not-an-email", b"Invalid email"),
    ("phone", "123", b"8 digits"),
    ("outlet_id", "", b"Outlet ID"),
    ("incident_datetime", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"), b"future"),
    ("incident_datetime", "yesterday", b"Invalid date"),
    ("category", "rude", b"Invalid complaint category"),
    ("description", "   ", b"Description cannot be empty"),
    ("wants_followup", "maybe", b"follow-up"),
])
def test_invalid_submission_is_rejected_and_not_saved(client, store, field, value, message):
    response = client.post("/submit", data=form(**{field: value}))
    assert response.status_code == 400
    assert message in response.data
    assert store.load_complaints() == []


def test_valid_submission_is_triaged_and_saved(client, store):
    response = client.post("/submit", data=form())
    assert response.status_code == 200
    records = store.load_complaints()
    assert len(records) == 1
    record = records[0]
    assert record["complaint_id"] == "CMP-0001"
    assert record["outlet_name"] == "Jewel Changi"   # looked up from merchant_config.json
    assert record["category"] == "food_quality"
    assert record["wants_followup"] is True
    assert record["is_addressed"] is False
    assert record["outcome"] in {"log", "flag_for_review", "escalate", "route_to_manager"}
    assert "score" in record