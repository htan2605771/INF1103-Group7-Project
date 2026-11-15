from datetime import datetime
import os
import json
from collections import defaultdict
from flask import Flask, redirect, render_template, request, session, url_for, abort
from ai_manager.ai_manager import AIManager
from ai_manager.gemini_client import GeminiClient
from data_manager.complaint_data_manager import ComplaintDataManager
from data_manager.merchant_config_manager import MerchantConfigManager  
from logic_manager.evaluator import ComplaintEvaluator
from io_manager.complaint_validator import IOComplaintValidator

app = Flask(__name__)

# Register custom Jinja filter for friendly date/time formatting
@app.template_filter('friendly_date')
def friendly_date_filter(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d %Y, %I:%M %p")
    except Exception:
        return iso_str

# Secret key required to use Flask sessions securely
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

# Manager password
MANAGER_PASSWORD = os.environ.get("MANAGER_PASSWORD", "admin123")

db_manager = ComplaintDataManager()
config_manager = MerchantConfigManager() 
ai = AIManager(GeminiClient())
evaluator = ComplaintEvaluator() 
validator = IOComplaintValidator()


def _is_urgent(severity_str):
    """Helper to check if a severity level is high or critical."""
    return str(severity_str or "").lower() in ["high", "critical"]


def _update_record_status(complaint_id, update_callback):
    """Helper function to load records, update a specific complaint, persist, and return its outlet ID."""
    records = db_manager.load_complaints()
    target_outlet_id = None
    
    for r in records:
        if r.get("complaint_id") == complaint_id:
            target_outlet_id = r.get("outlet_id")
            update_callback(r)
            break

    # Persist changes back to storage
    saved = False
    try:
        if hasattr(db_manager, "save_complaints"):
            db_manager.save_complaints(records)
            saved = True
        elif hasattr(db_manager, "save_data"):
            db_manager.save_data(records)
            saved = True
    except Exception as e:
        print(f"Manager save method error: {e}")

    # Fallback to direct JSON file write if manager methods aren't available
    if not saved:
        for filename in ["complaints_data.json", "data/complaints_data.json", "data/complaints.json"]:
            try:
                if os.path.exists(filename) or filename == "complaints_data.json":
                    with open(filename, "w") as f:
                        json.dump(records, f, indent=4)
                    saved = True
                    break
            except Exception as e:
                print(f"Error saving records to {filename}: {e}")

    return target_outlet_id


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/customer")
def customer_portal():
    config = config_manager.load_config()
    return render_template("customer.html", config=config)


@app.route("/submit", methods=["POST"])
def submit_complaint():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    outlet_id = request.form.get("outlet_id")
    incident_datetime = request.form.get("incident_datetime")
    
    # Ensure ISO timestamp includes seconds if the browser sends minute-level format
    if incident_datetime and len(incident_datetime) == 16:
        incident_datetime = incident_datetime + ":00"

    order_ref = request.form.get("order_reference", "").strip()
    category = request.form.get("category", "").strip().lower()
    description = request.form.get("description")
    raw_followup = request.form.get("wants_followup", "no").lower()

    # Validator checks
    if not validator.validate_name(name):
        return "Validation Error: Name cannot be empty.", 400
        
    if not validator.validate_email(email):
        return "Validation Error: Invalid email format.", 400
        
    if not validator.validate_phone_number(phone):
        return "Validation Error: Phone number must be exactly 8 digits.", 400
        
    if not validator.validate_outlet_id(outlet_id):
        return "Validation Error: Outlet ID cannot be empty.", 400

    date_check = validator.validate_incident_datetime(incident_datetime)
    if date_check == "future":
        return "Validation Error: Incident date and time cannot be in the future.", 400
    elif date_check == "invalid_format":
        return "Validation Error: Invalid date format. Use YYYY-MM-DDTHH:MM:SS.", 400

    if not validator.validate_complaint_category(category):
        return f"Validation Error: Invalid complaint category. Received: {repr(category)}", 400

    normalised_category = validator.normalise_complaint_category(category)

    if not validator.validate_complaint_description(description):
        return "Validation Error: Description cannot be empty.", 400

    if not validator.validate_follow_up_preference(raw_followup):
        return "Validation Error: Invalid follow-up choice.", 400
    
    wants_followup_bool = validator.normalise_follow_up_preference(raw_followup)
    outlet_name = config_manager.get_store_name(outlet_id)

    complaint = {
        "complaint_id": "",
        "name": name,
        "email": email,
        "phone": phone,
        "outlet_id": outlet_id,
        "outlet_name": outlet_name, 
        "datetime": incident_datetime,
        "order_ref": order_ref,
        "category": normalised_category,
        "description": description,
        "wants_followup": wants_followup_bool,
        "is_addressed": False
    }

    # Run AI evaluation and save data
    ai_output = ai.get_ai_output(complaint, on_retry=None)
    
    # Automatic override: Force follow-up request if insufficient info or nonsensical text detected
    ai_details = str(ai_output.get("key_details", "")).lower()
    ai_reason = str(ai_output.get("reason", "")).lower()
    if any(phrase in ai_details or phrase in ai_reason for phrase in ["insufficient information", "nonsensical", "lacks sufficient context"]):
        complaint["wants_followup"] = True

    history = db_manager.filter_by_outlet_and_date(complaint["outlet_id"], days=7)
    evaluation = evaluator.evaluate_complaint(complaint, ai_output, history)
    score = evaluator.calculate_score(
        evaluation["final_severity"],
        ai_output.get("reputational_risk", False),
        evaluation["outlet_flagged"],
    )

    result = {**evaluation, "score": score}
    db_manager.save_complaint(complaint, ai_output, result)

    return render_template(
        "result.html", complaint=complaint, ai_output=ai_output, result=result
    )


# Manager Authentication Routes
@app.route("/manager-login", methods=["GET", "POST"])
def manager_login():
    error = None
    if request.method == "POST":
        entered_password = request.form.get("password")
        if entered_password == MANAGER_PASSWORD:
            session["manager_logged_in"] = True
            return redirect(url_for("manager_dashboard"))
        else:
            error = "Incorrect password. Please try again."
    return render_template("login.html", error=error)


@app.route("/manager-logout")
def manager_logout():
    session.pop("manager_logged_in", None)
    return redirect(url_for("manager_login"))


@app.route("/manager")
def manager_dashboard():
    if not session.get("manager_logged_in"):
        return redirect(url_for("manager_login"))

    merchant_config = config_manager.load_config()
    configured_outlets = merchant_config.get("outlets", [])

    all_records = db_manager.load_complaints()
    records = [r for r in all_records if not r.get("is_addressed")]
    records = sorted(records, key=lambda x: x.get("score", 0), reverse=True)

    complaints_by_outlet = defaultdict(list)
    for r in records:
        complaints_by_outlet[r.get("outlet_id")].append(r)

    outlet_overview = []
    for outlet in configured_outlets:
        outlet_id = outlet.get("outlet_id")
        store_name = outlet.get("store_name")
        outlet_recs = complaints_by_outlet.get(outlet_id, [])
        
        # Dynamically evaluate flag status on the fly using full record history
        latest_rec = outlet_recs[0] if outlet_recs else None
        is_flagged, _ = evaluator.check_outlet_pattern(all_records, outlet_id, latest_rec)
        
        outlet_overview.append({
            "id": outlet_id,
            "name": store_name,
            "active_count": len(outlet_recs),
            "is_flagged": is_flagged,
            "urgent_count": sum(1 for r in outlet_recs if _is_urgent(r.get("final_severity"))),
            "followup_count": sum(1 for r in outlet_recs if r.get("wants_followup"))
        })

    stats = {
        "total": len(records),
        "urgent": sum(1 for r in records if _is_urgent(r.get("final_severity"))),
        "flagged": sum(1 for o in outlet_overview if o["is_flagged"])
    }

    return render_template(
        "manager.html", 
        stats=stats, 
        outlet_overview=outlet_overview
    )


@app.route("/manager/outlet/<outlet_id>")
def outlet_detail(outlet_id):
    if not session.get("manager_logged_in"):
        return redirect(url_for("manager_login"))

    merchant_config = config_manager.load_config()
    configured_outlets = merchant_config.get("outlets", [])
    
    current_outlet = next((o for o in configured_outlets if o.get("outlet_id") == outlet_id), None)
    if not current_outlet:
        return abort(404, description="Outlet not found.")

    all_records = db_manager.load_complaints()
    store_records = [r for r in all_records if r.get("outlet_id") == outlet_id and not r.get("is_addressed")]
    store_records = sorted(store_records, key=lambda x: x.get("score", 0), reverse=True)

    urgent_count = sum(1 for r in store_records if _is_urgent(r.get("final_severity")))
    followup_count = sum(1 for r in store_records if r.get("wants_followup"))
    
    latest_rec = store_records[0] if store_records else None
    is_flagged, attention_reasons = evaluator.check_outlet_pattern(all_records, outlet_id, latest_rec)

    # Display message only for Attention Required; leave blank when normal
    if urgent_count > 0 and not attention_reasons:
        fallback_summary = "High-severity issue requires immediate escalation review."
    else:
        fallback_summary = ""

    return render_template(
        "outlet_detail.html",
        outlet=current_outlet,
        records=store_records,
        active_count=len(store_records),
        urgent_count=urgent_count,
        followup_count=followup_count,
        is_flagged=is_flagged,
        attention_reasons=attention_reasons,
        fallback_summary=fallback_summary
    )


@app.route("/manager/resolve/<complaint_id>", methods=["POST"])
def resolve_complaint(complaint_id):
    if not session.get("manager_logged_in"):
        return redirect(url_for("manager_login"))

    def _resolve(r):
        if r.get("wants_followup"):
            print(f"Cannot resolve ticket {complaint_id}: Follow-up pending.")
        else:
            r["is_addressed"] = True

    target_outlet_id = _update_record_status(complaint_id, _resolve)

    if target_outlet_id:
        return redirect(url_for('outlet_detail', outlet_id=target_outlet_id) + f"#card-{complaint_id}")
    return redirect(url_for('manager_dashboard'))


@app.route("/manager/resolve-followup/<complaint_id>", methods=["POST"])
def resolve_followup(complaint_id):
    if not session.get("manager_logged_in"):
        return redirect(url_for("manager_login"))

    def _clear_followup(r):
        r["wants_followup"] = False

    target_outlet_id = _update_record_status(complaint_id, _clear_followup)

    if target_outlet_id:
        return redirect(url_for('outlet_detail', outlet_id=target_outlet_id) + f"#card-{complaint_id}")
    return redirect(url_for('manager_dashboard'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)