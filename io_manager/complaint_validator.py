from datetime import datetime
import re # used to check whether a text matches a specific pattern

class IOComplaintValidator:
    """Handles validation of customer complaint inputs."""

    def __init__(self) -> None:
        self.__email_pattern = r"^[\w.-]+@[\w.-]+\.\w+$"
        self.__phone_pattern = r"^\d{8}$"
        self.__valid_categories = (
            "food quality",
            "service",
            "hygiene",
            "billing",
            "other"
        )

    # helper method reused to check whether inputs are empty
    def _validate_non_empty(self, value: str) -> bool:
        """Checks whether an input is not empty."""
        return value.strip() != ""

    def validate_name(self, name: str) -> bool:
        """Checks whether the customer name is not empty."""
        return self._validate_non_empty(name)

    def validate_email(self, email: str) -> bool:
        """Checks whether the email follows the required format."""
        return re.fullmatch(self.__email_pattern, email) is not None

    def validate_phone_number(self, phone_number: str) -> bool:
        """Checks whether the phone number contains exactly 8 digits."""
        return re.fullmatch(self.__phone_pattern, phone_number) is not None
    
    def validate_outlet_id(self, outlet_id: str) -> bool:
        """Checks whether the outlet ID is not empty."""
        return self._validate_non_empty(outlet_id)

    def validate_incident_datetime(self, incident_datetime: str) -> str:
        try:
            incident_datetime_object = datetime.strptime(
                incident_datetime,
                "%Y-%m-%dT%H:%M:%S"
            )

            if incident_datetime_object > datetime.now():
                return "future"

            return "valid"

        except ValueError:
            return "invalid_format"

    def validate_complaint_category(self, complaint_category: str) -> bool:
        """Checks whether the complaint category is valid."""
        return complaint_category in self.__valid_categories
  
    def normalise_complaint_category(self, complaint_category: str) -> str:
        """Converts the complaint category into the required format."""
        if complaint_category == "food quality":
            return "food_quality"
        return complaint_category

    def validate_complaint_description(self, complaint_description: str) -> bool:
        """Checks whether the complaint description is not empty."""
        return self._validate_non_empty(complaint_description)

    def validate_follow_up_preference(self, follow_up: str) -> bool:
        """Checks whether the follow-up preference is valid."""
        return follow_up in ("yes", "no")

    def normalise_follow_up_preference(self, follow_up: str) -> bool:
        """Converts the follow-up preference into a Boolean."""
        return follow_up == "yes"



