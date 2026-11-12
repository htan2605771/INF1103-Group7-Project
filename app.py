import os
from flask import Flask, redirect, render_template, request
from ai_manager.ai_manager import AIManager
from ai_manager.gemini_client import GeminiClient
from data_manager.complaint_data_manager import ComplaintDataManager
from data_manager.merchant_config_manager import MerchantConfigManager  # 1. IMPORT IT HERE
from logic_manager import ComplaintEvaluator
from io_manager.complaint_validator import IOComplaintValidator

app = Flask(__name__)

db_manager = ComplaintDataManager()
config_manager = MerchantConfigManager()  # 2. INITIALIZE IT HERE
ai = AIManager(GeminiClient())
evaluator = ComplaintEvaluator() 
validator = IOComplaintValidator()

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
  order_ref = request.form.get("order_reference", "")
  category = request.form.get("category", "").strip().lower()
  description = request.form.get("description")

  raw_followup = request.form.get("wants_followup", "no").lower()

# Run validator checks from IOComplaintValidator()
  if not validator.validate_name(name):
      return "Validation Error: Name cannot be empty.", 400
      
  if not validator.validate_email(email):
      return "Validation Error: Invalid email format.", 400
      
  if not validator.validate_phone_number(phone):
      return "Validation Error: Phone number must be exactly 8 digits.", 400
      
  if not validator.validate_outlet_id(outlet_id):
      return "Validation Error: Outlet ID cannot be empty.", 400

# Date validation returns a string: "valid", "future", or "invalid_format"
  date_check = validator.validate_incident_datetime(incident_datetime)
  if date_check == "future":
      return "Validation Error: Incident date and time cannot be in the future.", 400
  elif date_check == "invalid_format":
      return "Validation Error: Invalid date format. Use YYYY-MM-DDTHH:MM.", 400

  if not validator.validate_complaint_category(category):
      return f"Validation Error: Invalid complaint category. Received: {repr(category)}", 400

# Normalise the category (e.g. "food quality" -> "food_quality")
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
  }

  # Run AI evaluation and save data
  ai_output = ai.get_ai_output(complaint, on_retry=None)
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

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)