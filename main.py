def get_name():
    name = input("Enter your name: ")
    return name

def get_email():
    email = input("Enter your email: ")
    return email

def get_phone_number():
    phone_number = input("Enter your phone number: ")
    return phone_number

def get_outlet_name():
    outlet_name = input("Enter outlet/branch name: ")
    return outlet_name

def get_incident_date():
    incident_date = input("Enter date of incident: ")
    return incident_date

def get_incident_time():
    incident_time = input("Enter time of incident: ")
    return incident_time

# def get_order_channel():
#     order_channel = input("Enter order channel (In-store, Mobile App, Delivery Platform): ")
#     return order_channel

def get_order_reference(): # not sure if this is applicable yet
    order_reference = input("Enter order/transaction reference (if applicable): ") # This should be able to accept no input
    return order_reference

def get_complaint_category():
    complaint_category = input("Enter complaint category (Food Quality, Service, Hygiene, Billing, Other): ")
    return complaint_category

def get_complaint_description():
    complaint_description = input("Enter complaint description: ")
    return complaint_description

def get_follow_up_preference():
    follow_up = input("Would your like a respnse/follow-up? (Yes/No): ")
    return follow_up

def collect_complaint(): 
    pass