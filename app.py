import os
from flask import Flask, redirect, render_template, request, session, url_for
from ai_manager.ai_manager import AIManager
from ai_manager.gemini_client import GeminiClient
from data_manager.complaint_data_manager import ComplaintDataManager
from logic_manager import ComplaintEvaluator
from io_manager.complaint_validator import IOComplaintValidator

app = Flask(__name__)

db_manager = ComplaintDataManager()
ai = AIManager(GeminiClient())
evaluator = ComplaintEvaluator() 
validator = IOComplaintValidator()

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/customer")
def customer_portal():
  return render_template("customer.html")

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)