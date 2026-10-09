import io_manager
import ai_manager
import logic_manager
import data_manager

def process_complaint() -> None:
    """Executes the end-to-end triage pipeline for a single complaint."""
    # Collect and validate user input from terminal
    complaint = io_manager.collect_complaint()

    # # 2. Get AI classification & sentiment analysis (falls back safely on failure)
    ai_output = ai_manager.get_ai_output(complaint, on_retry=io_manager.display_ai_retry)

    # # 3. Retrieve historical records for pattern checking (e.g., recent outlet issues)
    history = data_manager.filter_by_outlet_and_date(
        complaint["outlet_id"], days=7
    )

    # # 4. Evaluate business rules and determine final triage severity/action
    evaluation = logic_manager.evaluate_complaint(complaint, ai_output, history)
    
    score = logic_manager.calculate_score(
        evaluation["final_severity"],
        ai_output.get("reputational_risk", False),
        evaluation["outlet_flagged"]
    )

    # Combine evaluation result and score into final decision object
    result = {
        **evaluation,
        "score": score
    }
    
    # # 5. Persist complete record (complaint + ai_output + result)
    data_manager.save_complaint(complaint, ai_output, result)

    # 6. Output the final decision back to the user
    io_manager.display_result(complaint, ai_output, result)

def main() -> None:
    """Loads stored records on startup and runs the main interactive loop."""
    print("=" * 55)
    print("      F&B CUSTOMER COMPLAINT TRIAGE SYSTEM      ")
    print("=" * 55)

    # Load existing complaint database on startup
    existing_records = data_manager.load_complaints()
    print(f"Loaded {len(existing_records)} existing complaint record(s).\n")

    while True:
        print("\n--- Main Menu ---")
        print("1. Submit new complaint")
        print("2. View complaint history summary")
        print("3. Exit")

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            process_complaint()
        elif choice == "2":
            # Refresh and view stored records
            records = data_manager.load_complaints()
            io_manager.display_summary(records)
        elif choice == "3":
            print("\nExiting F&B Complaint Triage System. Goodbye!")
            break
        else:
            print("Invalid option. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()