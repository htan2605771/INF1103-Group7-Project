from .result_display import IOResultDisplay

class IOManager:
    """Handles formatting and printing outputs, summaries, and retry alerts."""

    @staticmethod
    def display_result(complaint: dict, ai_output: dict, result: dict) -> None:
        """Displays the final triage result using IOResultDisplay."""
        result_display = IOResultDisplay()
        result_display.display_result(complaint, ai_output, result)


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