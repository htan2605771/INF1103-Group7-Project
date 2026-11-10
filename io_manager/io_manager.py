from __future__ import annotations
from datetime import datetime
import re

class ComplaintCollector:
    """Handles interactive input collection and validation for customer complaints."""
    
    RED = "\033[91m"
    RESET = "\033[0m"

    def get_name(self) -> str:
        return input("Enter your name: ").strip()

    def get_email(self) -> str:
        return input("Enter your email: ").strip()

    def get_phone_number(self) -> str:
        return input("Enter your phone number: ").strip()

    def get_outlet_id(self) -> str:
        return input("Enter outlet/branch ID: ").strip()

    def get_incident_datetime(self) -> str:
        return input(
            "Enter date and time of incident "
            "(YYYY-MM-DDTHH:MM:SS e.g. 2026-09-18T14:30:00): "
        ).strip()

    def get_order_reference(self) -> str:
        return input(
            "Enter order/transaction reference "
            "(press Enter if not applicable): "
        ).strip()

    def get_complaint_category(self) -> str:
        return input(
            "Enter complaint category "
            "(Food Quality, Service, Hygiene, Billing, Other): "
        ).strip().lower()

    def get_complaint_description(self) -> str:
        return input(
            "Enter complaint description: "
        ).strip()

    def get_follow_up_preference(self) -> str:
        return input(
            "Would you like a response/follow-up? (Yes/No): "
        ).strip().lower()

    def collect_complaint(self) -> dict:
        """Validates and collects all complaint fields into a dictionary."""
        # Name validation
        while True:
            name = self.get_name()
            if name != "":
                break
            print(f"{self.RED}[!] Name cannot be empty. Please try again.{self.RESET}")

        # Email validation
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        while True:
            email = self.get_email()
            if re.match(email_pattern, email):
                break
            print(f"{self.RED}[!] Invalid email format. (e.g., user@domain.com){self.RESET}")

        # Phone number validation
        phone_pattern = r"^\d{8}$"
        while True:
            phone_number = self.get_phone_number()
            if re.match(phone_pattern, phone_number):
                break
            print(f"{self.RED}[!] Invalid phone number. Please enter an 8-digit phone number.{self.RESET}")

        # Outlet ID validation
        while True:
            outlet_id = self.get_outlet_id()
            if outlet_id != "":
                break
            print(f"{self.RED}[!] Outlet/branch ID cannot be empty. Please try again.{self.RESET}")

        # Incident datetime validation
        while True:
            incident_datetime = self.get_incident_datetime()
            try:
                incident_datetime_object = datetime.strptime(
                    incident_datetime,
                    "%Y-%m-%dT%H:%M:%S"
                )
                if incident_datetime_object <= datetime.now():
                    break
                print(f"{self.RED}[!] Incident date and time cannot be in the future.{self.RESET}")
            except ValueError:
                print(
                    f"{self.RED}[!] Invalid date/time. "
                    f"Please use YYYY-MM-DDTHH:MM:SS format.{self.RESET}"
                )

        # Order reference (optional)
        order_reference = self.get_order_reference()

        # Complaint category validation
        while True:
            complaint_category = self.get_complaint_category()
            if complaint_category == "food quality":
                complaint_category = "food_quality"
                break
            elif complaint_category in ["service", "hygiene", "billing", "other"]:
                break
            print(f"{self.RED}[!] Invalid complaint category. Please try again.{self.RESET}")

        # Complaint description validation
        while True:
            complaint_description = self.get_complaint_description()
            if complaint_description != "":
                break
            print(f"{self.RED}[!] Complaint description cannot be empty. Please try again.{self.RESET}")

        # Follow-up preference validation
        while True:
            follow_up = self.get_follow_up_preference()
            if follow_up == "yes":
                wants_followup = True
                break
            elif follow_up == "no":
                wants_followup = False
                break
            print(f"{self.RED}[!] Invalid input. Please enter Yes or No.{self.RESET}")

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
            "wants_followup": wants_followup
        }

        return complaint


class IOManager:
    """Handles formatting and printing outputs, summaries, and retry alerts."""

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def display_ai_retry(sleep_time, attempt, max_retries) -> None:
        print(f"[!] AI call failed. Retrying in {sleep_time}s... (Attempt {attempt}/{max_retries})")


# Test 
if __name__ == "__main__":
    print("--- Running io_manager OOP standalone test ---")

    collector = ComplaintCollector()
    complaint = collector.collect_complaint()

    # Sample AI output
    dummy_ai = {
        "ai_category": complaint["category"],
        "key_details": ["Bug", "Not clean"],
        "severity": "medium",
        "reason": "Soup contained a bug.",
        "reputational_risk": True,
        "confidence": "high",
    }

    # Sample final result
    dummy_result = {
        "final_severity": "high",
        "outcome": "route_to_manager",
        "outlet_flagged": True,
        "override_applied": True,
        "override_reason": "Hygiene issue auto-promoted.",
    }

    IOManager.display_result(complaint, dummy_ai, dummy_result)
    IOManager.display_summary([complaint])