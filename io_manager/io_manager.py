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