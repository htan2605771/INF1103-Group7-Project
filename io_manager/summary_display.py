
class IOSummaryDisplay:
    """Handles formatting and displaying customer complaint summaries."""

    def display_summary(self, complaints: list[dict]) -> None:
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