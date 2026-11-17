from .result_display import IOResultDisplay
from .summary_display import IOSummaryDisplay
from .retry_display import IORetryDisplay

class IOManager:
    """Coordinates complaint result, summary, and AI retry displays."""

    @staticmethod
    def display_result(complaint: dict, ai_output: dict, result: dict) -> None:
        """Displays the final triage result using IOResultDisplay."""
        result_display = IOResultDisplay()
        result_display.display_result(complaint, ai_output, result)

    @staticmethod
    def display_summary(complaints: list[dict]) -> None:
        """Displays complaint summaries using IOSummaryDisplay."""
        summary_display = IOSummaryDisplay()
        summary_display.display_summary(complaints)

    @staticmethod
    def display_ai_retry(sleep_time: int | float, attempt: int, max_retries: int) -> None:
        """Displays AI retry notifications using IORetryDisplay."""
        retry_display = IORetryDisplay()
        retry_display.display_ai_retry(sleep_time, attempt, max_retries)

    @staticmethod
    def display_banner(record_count: int) -> None:
        """Displays the application title and how many records were loaded."""
        print("=" * 55)
        print("      F&B CUSTOMER COMPLAINT TRIAGE SYSTEM      ")
        print("=" * 55)
        print(f"Loaded {record_count} existing complaint record(s).\n")

    @staticmethod
    def get_menu_choice() -> str:
        """Shows the main menu and returns the option the user typed."""
        print("\n--- Main Menu ---")
        print("1. Submit new complaint")
        print("2. View complaint history summary")
        print("3. Exit")
        return input("Select an option (1-3): ").strip()

    @staticmethod
    def display_message(message: str) -> None:
        """Displays a plain message to the user."""
        print(message)