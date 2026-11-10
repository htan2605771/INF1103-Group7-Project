class IORetryDisplay:
    """Handles displaying AI retry notifications."""

    def display_ai_retry(self, sleep_time: int | float, attempt: int, max_retries: int) -> None:
        """Prints a retry notification when an AI call fails."""
        print(f"[!] AI call failed. Retrying in {sleep_time}s... (Attempt {attempt}/{max_retries})")