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