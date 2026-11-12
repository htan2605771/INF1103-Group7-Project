from io_manager import IOComplaintCollector, IOManager
from logic_manager import ComplaintEvaluator
from data_manager import ComplaintDataManager
from ai_manager import AIManager, GeminiClient


class TriageApp:
    # Main Application which owns and calls the four managers and runs the triage menu options.
    def __init__(self):
        self.__collector = IOComplaintCollector()
        self.__io = IOManager()
        self.__ai = AIManager(GeminiClient())
        self.__data = ComplaintDataManager()
        self.__logic = ComplaintEvaluator() 

    def process_complaint(self) -> None:
        """Executes the end-to-end triage pipeline for a single complaint."""
        # 1. Collect and validate user input from terminal
        complaint = self.__collector.collect_complaint()

        # 2. Get AI classification & sentiment analysis (falls back safely on failure)
        ai_output = self.__ai.get_ai_output(complaint, on_retry=self.__io.display_ai_retry)

        # 3. Retrieve historical records for pattern checking (e.g., recent outlet issues)
        history = self.__data.filter_by_outlet_and_date(
            complaint["outlet_id"], days=7
        )

        # 4. Evaluate business rules and determine final triage severity/action
        evaluation = self.__logic.evaluate_complaint(complaint, ai_output, history)
        
        score = self.__logic.calculate_score(
            evaluation["final_severity"],
            ai_output.get("reputational_risk", False),
            evaluation["outlet_flagged"]
        )

        # Combine evaluation result and score into final decision object
        result = {
            **evaluation,
            "score": score
        }
        
        # 5. Persist complete record (complaint + ai_output + result)
        self.__data.save_complaint(complaint, ai_output, result)

        # 6. Output the final decision back to the user
        self.__io.display_result(complaint, ai_output, result)

    def main(self) -> None:
        """Loads stored records on startup and runs the main interactive loop."""
        print("=" * 55)
        print("      F&B CUSTOMER COMPLAINT TRIAGE SYSTEM      ")
        print("=" * 55)

        # Load existing complaint database on startup
        existing_records = self.__data.load_complaints()
        print(f"Loaded {len(existing_records)} existing complaint record(s).\n")


        while True:
            print("\n--- Main Menu ---")
            print("1. Submit new complaint")
            print("2. View complaint history summary")
            print("3. Exit")

            choice = input("Select an option (1-3): ").strip()

            if choice == "1":
                self.process_complaint()
            elif choice == "2":
                # Refresh and view stored records
                records = self.__data.load_complaints()
                self.__io.display_summary(records)
            elif choice == "3":
                print("\nExiting F&B Complaint Triage System. Goodbye!")
                break
            else:
                print("Invalid option. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    TriageApp().main()