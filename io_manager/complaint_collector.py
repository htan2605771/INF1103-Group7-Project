from .complaint_validator import IOComplaintValidator

class IOComplaintCollector:
    """Handles interactive input collection for customer complaints."""

    RED = "\033[91m"
    RESET = "\033[0m"

    def __init__(self) -> None:
        self.__validator = IOComplaintValidator()

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

    # order reference is optional
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
        """Collects and validates all customer complaint inputs before storing them in a dictionary."""
        # Name validation
        while True:
            name = self.get_name()
            if self.__validator.validate_name(name):
                break
            print(f"{self.RED}[!] Name cannot be empty. Please try again.{self.RESET}")

        # Email validation
        while True:
            email = self.get_email()
            if self.__validator.validate_email(email):
                break
            print(f"{self.RED}[!] Invalid email format. (e.g., user@domain.com){self.RESET}")

        # Phone number validation
        while True:
            phone_number = self.get_phone_number()
            if self.__validator.validate_phone_number(phone_number):
                break
            print(f"{self.RED}[!] Invalid phone number. Please enter an 8-digit phone number.{self.RESET}")

        # Outlet ID validation
        while True:
            outlet_id = self.get_outlet_id()
            if self.__validator.validate_outlet_id(outlet_id):
                break
            print(f"{self.RED}[!] Outlet/branch ID cannot be empty. Please try again.{self.RESET}")

        # Incident datetime validation
        while True:
            incident_datetime = self.get_incident_datetime()
            validation_result = self.__validator.validate_incident_datetime(incident_datetime)

            if validation_result == "valid":
                break
            elif validation_result == "future":
                print(f"{self.RED}[!] Incident date and time cannot be in the future.{self.RESET}")
            elif validation_result == "invalid_format":
                print(
                    f"{self.RED}[!] Invalid date/time. "
                    f"Please use YYYY-MM-DDTHH:MM:SS format.{self.RESET}"
                )
        
        order_reference = self.get_order_reference()

        # Complaint category validation
        while True:
            complaint_category = self.get_complaint_category()
            if self.__validator.validate_complaint_category(complaint_category):
                complaint_category = self.__validator.normalise_complaint_category(complaint_category)
                break
            print(f"{self.RED}[!] Invalid complaint category. Please try again.{self.RESET}")

        # Complaint description validation
        while True:
            complaint_description = self.get_complaint_description()
            if self.__validator.validate_complaint_description(complaint_description):
                break
            print(f"{self.RED}[!] Complaint description cannot be empty. Please try again.{self.RESET}")

        # Follow-up preference validation
        while True:
            follow_up = self.get_follow_up_preference()
            if self.__validator.validate_follow_up_preference(follow_up):
                wants_followup = self.__validator.normalise_follow_up_preference(follow_up)
                break
            print(f"{self.RED}[!] Invalid input. Please enter Yes or No.{self.RESET}")

        """Construct Complaint Dictionary"""
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