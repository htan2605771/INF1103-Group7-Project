from datetime import datetime
import re

#Makes text red to show the user something is wrong, and then resets the color back to normal
RED = "\033[91m"
RESET = "\033[0m"

def get_name():
    name = input("Enter your name: ").strip()
    return name

def get_email():
    email = input("Enter your email: ").strip()
    return email

def get_phone_number():
    phone_number = input("Enter your phone number: ").strip()
    return phone_number

def get_outlet_id():
    outlet_id = input("Enter outlet/branch ID: ").strip()
    return outlet_id

def get_incident_datetime(): # ISO format, e.g. "2026-09-18T14:30:00"
    incident_datetime = input(
        "Enter date and time of incident "
        "(YYYY-MM-DDTHH:MM:SS e.g. 2026-09-18T14:30:00): "
    ).strip()
    return incident_datetime

def get_order_reference(): # optional, "" if not applicable
    order_reference = input(
        "Enter order/transaction reference "
        "(press Enter if not applicable): "
    ).strip()
    return order_reference

def get_complaint_category(): # customer-selected: "food_quality" | "service" | "hygiene" | "billing" | "other"
    complaint_category = input(
        "Enter complaint category "
        "(Food Quality, Service, Hygiene, Billing, Other): "
    ).strip().lower()
    return complaint_category

def get_complaint_description(): # free-text complaint
    complaint_description = input(
        "Enter complaint description: "
    ).strip()
    return complaint_description

def get_follow_up_preference():
    follow_up = input(
        "Would you like a response/follow-up? (Yes/No): "
    ).strip().lower()
    return follow_up

def collect_complaint(): # dict
    # name validation
    while True:
        name = get_name()

        if name != "":
            break

        print(f"{RED}[!] Name cannot be empty. Please try again.{RESET}")
    
    # email validation
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    while True:
        email = get_email()

        if re.match(email_pattern, email):
            break

        print(f"{RED}[!] Invalid email format. (e.g., user@domain.com){RESET}")


    # phone number validation
    phone_pattern = r"^\d{8}$"
    while True:
        phone_number = get_phone_number()

        if re.match(phone_pattern, phone_number):
            break

        print(f"{RED}[!] Invalid phone number. Please enter an 8-digit phone number.{RESET}")

    # outlet ID validation
    while True:
        outlet_id = get_outlet_id()

        if outlet_id != "":
            break

        print(f"{RED}[!] Outlet/branch ID cannot be empty. Please try again.{RESET}")


    # incident datetime validation
    while True:
        incident_datetime = get_incident_datetime()

        try:
            incident_datetime_object = datetime.strptime(
                incident_datetime,
                "%Y-%m-%dT%H:%M:%S"
            )

            if incident_datetime_object <= datetime.now():
                break

            print(f"{RED}[!] Incident date and time cannot be in the future.{RESET}")

        except ValueError:
            print(
                f"{RED}[!] Invalid date/time. "
                f"Please use YYYY-MM-DDTHH:MM:SS format.{RESET}"
            )

    # order reference
    # no validation loop needed because this field is optional
    order_reference = get_order_reference()

    # complaint category validation
    while True:
        complaint_category = get_complaint_category()

        if complaint_category == "food quality":
            complaint_category = "food_quality"
            break
        elif complaint_category == "service":
            break
        elif complaint_category == "hygiene":
            break
        elif complaint_category == "billing":
            break
        elif complaint_category == "other":
            break

        print(f"{RED}[!] Invalid complaint category. Please try again.{RESET}")


    # complaint description validation
    while True:
        complaint_description = get_complaint_description()

        if complaint_description != "":
            break

        print(f"{RED}[!] Complaint description cannot be empty. Please try again.{RESET}")
    
    # Matrix check: Short or Ambiguous Text Submission
    words = complaint_description.split()
    is_ambiguous = len(complaint_description) < 10 or len(words) < 3

    if is_ambiguous:
        print("\n[i] Short or ambiguous text detected. Flagging for Manual Review...")

    # follow-up preference validation
    while True:
        follow_up = get_follow_up_preference()

        if follow_up == "yes":
            wants_followup = True
            break
        elif follow_up == "no":
            wants_followup = False
            break

        print(f"{RED}[!] Invalid input. Please enter Yes or No.{RESET}")

    # validated inputs to be stored in a dictionary here
    complaint = {
        "complaint_id": "",  # to be generated later
        "name": name,
        "email": email,
        "phone": phone_number,
        "outlet_id": outlet_id,
        "datetime": incident_datetime,
        "order_ref": order_reference,
        "category": complaint_category,
        "description": complaint_description,
        "wants_followup": wants_followup,
        "is_ambiguous": is_ambiguous
    }

    return complaint

# complaint = collect_complaint()
# print(complaint)

# get_name()
# get_email()
# get_phone_number()
# get_outlet_id()
# get_incident_datetime()
# get_order_reference()
# get_complaint_category()
# get_complaint_description()
# get_follow_up_preference()

def display_result(complaint: dict, ai_output: dict, result: dict) -> None:
    """Print the final triage outcome to the terminal in a readable format."""
    print("\n" + "=" * 60)
    print(f"          TRIAGE RESULT FOR COMPLAINT: {complaint.get('complaint_id', 'N/A')}")
    print("=" * 60)

    # Core details
    print("[COMPLAINT DETAILS]\n")
    print(f"Outlet ID         : {complaint.get('outlet_id')}")
    print(f"Customer Name     : {complaint.get('name')}")
    print(f"Category          : {complaint.get('category')}")
    print(f"Description       : {complaint.get('description')}")
    print("=" * 60)

    # AI output details
    print("[AI ANALYSIS]\n")
    print(f"Category          : {ai_output.get('ai_category')}")
    print(f"Key Details       : {', '.join(ai_output.get('key_details', []))}")
    print(f"AI Severity       : {str(ai_output.get('severity', 'N/A')).upper()}")
    print(f"Reason            : {ai_output.get('reason')}")
    print(f"Reputational Risk : {'YES' if ai_output.get('reputational_risk') else 'No'}")
    print(f"Confidence        : {str(ai_output.get('confidence', 'N/A')).upper()}")
    print("-" * 60)

    # Final result (logic manager check, business logic)
    print("[FINAL TRIAGE DECISION]\n")
    print(f"Final Severity   : {str(result.get('final_severity', 'N/A')).upper()}")
    print(f"Action Outcome   : {str(result.get('outcome', 'N/A')).upper()}")
    print(f"Pattern Flagged  : {'YES (Multiple complaints detected)' if result.get('outlet_flagged') else 'No'}")

    if result.get("override_applied"):
        print(f"Override Notice  : APPLIED -> {result.get('override_reason')}")

    print("=" * 60 + "\n")

def display_summary(complaints: list[dict]) -> None:
    """Print a summary/list view of multiple complaint records."""
    if not complaints:
        print("\n[!] No complaint records found.\n")
        return

    print("\n" + "=" * 80)
    print(f" {'COMPLAINT SUMMARY LIST':^73} ")
    print("=" * 80)
    
    # Table Header
    print(f"{'ID':<12} | {'OUTLET':<10} | {'CATEGORY':<12} | {'CUSTOMER':<15} | {'DESCRIPTION':<18}")
    print("-" * 80)

    # Table Rows
    for complaint in complaints:
        c_id = complaint.get('complaint_id', 'N/A')
        outlet = complaint.get('outlet_id', 'N/A')
        category = complaint.get('category', 'N/A')
        customer = complaint.get('name') or 'Anonymous'
        raw_desc = complaint.get('description', 'N/A')

        print(f"{c_id:<12} | {outlet:<10} | {category:<12} | {customer:<15} | {raw_desc:<18}")

    print("=" * 80)
    print(f"Total Records: {len(complaints)}\n")

def display_ai_retry(sleep_time, attempt, max_retries):
    print(f"[!] AI call failed. Retrying in {sleep_time}s... (Attempt {attempt}/{max_retries})")

# Test 
if __name__ == "__main__":
    print("--- Running io_manager standalone test ---")

    complaint = collect_complaint()

    #sample
    dummy_ai = {
    "ai_category": complaint["category"],
    "key_details": ["Bug", "Not clean"],
    "severity": "medium",
    "reason": "Soup contained a bug.",
    "reputational_risk": True,
    "confidence": "high",
    }

    #sample
    dummy_result = { # ai_output
        "final_severity": "high",
        "outcome": "route_to_manager",
        "outlet_flagged": True,
        "override_applied": True,
        "override_reason": "Hygiene issue auto-promoted.",
    }

    
    display_result(complaint, dummy_ai, dummy_result)
    display_summary([complaint])