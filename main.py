from datetime import datetime

def get_name():
    while True:
        name = input("Enter your name: ").strip() # strip() removes leading and trailing characters (whitespace by default)

        if name != "": # checks if the input is not equal to an empty string
            return name

        print("Name cannot be empty. Please try again.")

def get_email():
    while True:
        email = input("Enter your email: ").strip()

        if (
            email.count("@") == 1
            and not email.startswith("@")
            and not email.endswith("@")
            and "." in email.split("@")[1]
            and not email.split("@")[1].startswith(".")
            and not email.endswith(".")
        ):
            return email

        print("Invalid email. Please try again.")

def get_phone_number():
    while True:
        phone_number = input("Enter your phone number: ").strip()
        
        if phone_number.isdigit() and len(phone_number) == 8:
            return phone_number

        print("Invalid phone number. Please enter an 8-digit phone number.")

def get_outlet_id():
    while True:
        outlet_id = input("Enter outlet/branch ID: ").strip()

        if outlet_id != "":
            return outlet_id

        print("Outlet/branch ID cannot be empty. Please try again.")

def get_incident_datetime(): # ISO format, e.g. "2026-09-18T14:30:00"
    while True:
        incident_datetime = input("Enter date and time of incident (YYYY-MM-DDTHH:MM:SS e.g. 2026-09-18T14:30:00): ").strip()
        # apparently ISO format can accept future dates so will need to figure this out

        try:
            incident_datetime_object = datetime.strptime(incident_datetime, "%Y-%m-%dT%H:%M:%S")

            if incident_datetime_object <= datetime.now():
                return incident_datetime

            print("Incident date and time cannot be in the future.")

        except ValueError:
            print("Invalid date/time. Please use YYYY-MM-DDTHH:MM:SS format.")

def get_order_reference(): # optional, "" if not applicable
    order_reference = input("Enter order/transaction reference (press Enter if not applicable): ").strip() # This should be able to accept no input
    
    return order_reference

def get_complaint_category(): # customer-selected: "food_quality" | "service" | "hygiene" | "billing" | "other"
    while True:
        complaint_category = input("Enter complaint category (Food Quality, Service, Hygiene, Billing, Other): ").strip().lower() # .lower() converts all alphabets to lowercase

        if complaint_category == "food quality":
            return "food_quality"
        elif complaint_category == "service":
            return "service"
        elif complaint_category == "hygiene":
            return "hygiene"
        elif complaint_category == "billing":
            return "billing"
        elif complaint_category == "other":
            return "other"

        print("Invalid complaint category. Please try again.")
        
    # return complaint_category

def get_complaint_description(): # free-text complaint
    while True:
        complaint_description = input("Enter complaint description: ").strip()
    
        if complaint_description != "":
            return complaint_description

        print("Complaint description cannot be empty. Please try again.")

def get_follow_up_preference():
    while True:
        follow_up = input("Would you like a response/follow-up? (Yes/No): ").strip().lower()

        if follow_up == "yes":
            return True
        elif follow_up == "no":
            return False
        
        # return follow_up

        print("Invalid input. Please enter Yes or No.")

def collect_complaint(): 
    pass

# get_name()
get_email()
# get_phone_number()
# get_outlet_id()
# get_incident_datetime()
# get_order_reference()
# get_complaint_category()
# get_complaint_description()
# get_follow_up_preference()