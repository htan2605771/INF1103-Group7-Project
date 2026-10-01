import os # used to access .env variables
import logging # used to record API errors
import json

from dotenv import load_dotenv # loads variables from the .env file (which is storing the API key)
from google import genai # used to connect to the Gemini API
from google.genai import errors # used to handle Gemini API errors

load_dotenv() # loads the .env file

api_key = os.getenv("GEMINI_API_KEY")

logger = logging.getLogger(__name__) # creates a logger for this file


def build_prompt(complaint): # build the prompt to send to the AI API
    prompt = f"""
    
    You are an AI assistant for an F&B customer complaint triage system.
    Analyse the following customer complaint.
    Customer-selected category: {complaint["category"]}
    Complaint description: {complaint["description"]}

    Your tasks are to:
    1. Classify the complaint into exactly one of the following categories:
    food_quality, service, hygiene, billing, other
    2. Extract the key details or issues mentioned in the complaint.
    3. Assess the severity of the complaint as exactly one of: 
    low, medium, high
    4. Provide a short reason for the classification and severity.
    5. Determine whether the complaint indicates a reputational risk.
    Return true or false.
    6. Assess your confidence in the analysis as exactly one of:
    low, medium, high

    Return only valid JSON in exactly this structure:

    {{
        "ai_category": "food_quality",
        "key_details": ["detail 1", "detail 2"],
        "severity": "low",
        "reason": "short explanation",
        "reputational_risk": false,
        "confidence": "high"
    }}

    Do not include markdown, code fences, or any additional text outside the JSON.
    """

    return prompt


def call_ai_api(prompt): # sends the prompt to the AI API and handle API failures
    if not api_key: # checks if the API key is missing
        logger.error("Gemini API key is missing.")
        return None # stops the function without crashing the program

    try: # tries to call the Gemini API
        client = genai.Client(api_key=api_key) # creates a Gemini client using the API key

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt # sends the prompt to Gemini
        )

        client.close() # closes the Gemini client

        return response.text # returns Gemini's response as text

    except errors.APIError as error: # handles errors from the Gemini API
        logger.error(f"Gemini API error: {error}")
        return None

    except Exception as error: # handles any other unexpected errors
        logger.error(f"Unexpected AI error: {error}")
        return None


def parse_ai_response(response): # parse the AI response into JSON
    if not response: # checks whether the response is empty or None
        logger.error("AI response is empty, there is no response to parse.")
        return None

    else:
        text = response.strip().strip("`") # removes leading and trailing whitespace and backticks from the response
        if text.lower().startswith("json"): # removes the json prefix if it exists, as some AI responses may include it
            text = text[4:]

        try:
            data = json.loads(text) # attempts to parse the response from JSON to a dictionary object

            if not isinstance(data, dict): # checks whether the parsed object is a dictionary
                logger.error("Parsed AI response is not a dictionary object.")
                return None
            
            return data
        
        except json.JSONDecodeError as error:
            logger.error(f"Failed to parse AI response as JSON: {error}")
            return None


def ai_output_schema(): # returns the expected ai_output fields, data types and allowable values
    schema = {
        "ai_category": [str, ("food_quality", "service", "hygiene", "billing", "other")],
        "key_details": [list, None],
        "severity": [str, ("low", "medium", "high")],
        "reason": [str, None],
        "reputational_risk": [bool, None],
        "confidence": [str, ("low", "medium", "high")]
    }
    return schema


def check_schema_fields(ai_output): # checks if each schema field exists in the ai_output, has the correct data type and allowed value
    schema = ai_output_schema()
    for field, rule in schema.items(): # field = key, rule = values. e.g. field = severity, rule = [str, ("low", "medium", "high")]
        if field not in ai_output: # if a schema field is missing in ai_output, log error
            logger.error(f"missing field: {field}")
            return False
        
        data_value = ai_output[field]

        if not isinstance(data_value, rule[0]): # if ai_output data type is not the same as schema, log error
            logger.error(f"wrong data type for {field}")
            return False

        if rule[1] is not None and data_value not in rule[1]: # if allowable value != None and data value is not in the allowable values, log error
            logger.error(f"invalid value: {data_value} for field: {field}")
            return False

    return True


def check_additional_rules(ai_output): # checks whether key details items all are of type string and reason is not empty
    for item in ai_output["key_details"]:
        if not isinstance(item, str): # if item data type is not string, log error
            logger.error(f"key_details item is not a string: {item}")
            return False
        
    reason_value = ai_output["reason"]

    if not reason_value.strip(): # checks if reason value is empty, if empty log error
        logger.error("reason value is empty")
        return False

    return True


def validate_ai_response(ai_output): # validate that the AI output follows the required schema
    if not isinstance(ai_output, dict): # rejects None or non-dictionary ai_output from a failed parse
        logger.error("ai_output data type is not a dictionary")
        return False
    
    if not check_schema_fields(ai_output): # if check_schema_fields function is false, return false
        return False
    
    if not check_additional_rules(ai_output): # if check_additional_rules function is false, return false
        return False
    
    return True


def fallback_ai_output(): # returns a default ai_output when the AI fails, flagged for manual review
    fallback = {
        "ai_category": "other",
        "key_details": [],
        "severity": "medium",
        "reason": "AI analysis unavailable, flagged for manual review",
        "reputational_risk": False,
        "confidence": "low"
    }
    return fallback


def get_ai_output(complaint): # run a complaint through the complete AI processing flow
    prompt = build_prompt(complaint)
    for i in range(2): # tries the AI flow twice (1st attempt + 1 retry)
        response = call_ai_api(prompt)
        ai_output = parse_ai_response(response)
        if validate_ai_response(ai_output): # if validate is successful return the ai_output
            return ai_output
        else:
            logger.error(f"AI validation failed try number: {i+1}")
    logger.error("AI failed after 2 attempts, using fallback output")
    return fallback_ai_output() # returns the fallback ai_output


if __name__ == "__main__":
    dummy_complaint = {
        "complaint_id": "CMP-0191",
        "name": "Sarah Tan",
        "email": "sarah.tan@example.com",
        "phone": "98765432",
        "outlet_id": "OUT-011",
        "datetime": "2026-09-30T14:30:00",
        "order_ref": "ORD-5787",
        "category": "hygiene",
        "description": "There was a hair inside my food and the table had some food stains.",
        "wants_followup": True
    }

    good_output = {
        "ai_category": "service",
        "key_details": ["Staff was rude", "Order was delayed"],
        "severity": "medium",
        "reason": "Poor staff attitude and delayed service can affect customer experience.",
        "reputational_risk": False,
        "confidence": "high"
    }

    print("\n--- parse_ai_response tests ---")
    print(parse_ai_response('```json\n{"a": 1}\n```'))  # {'a': 1}
    print(parse_ai_response('{"a": 1}'))                # {'a': 1}
    print(parse_ai_response('hello'))                   # None
    print(parse_ai_response('[1, 2]'))                  # None
    print(parse_ai_response(None))                      # None

    print("\n--- validate_ai_response tests ---")
    print(validate_ai_response(good_output))            # True
    print(validate_ai_response(None))                   # False

    missing_field = dict(good_output)
    del missing_field["confidence"]
    print(validate_ai_response(missing_field))          # False

    wrong_type = dict(good_output)
    wrong_type["reputational_risk"] = "false" 
    print(validate_ai_response(wrong_type))             # False

    invalid_value = dict(good_output)
    invalid_value["severity"] = "urgent"
    print(validate_ai_response(invalid_value))          # False

    bad_detail = dict(good_output)
    bad_detail["key_details"] = ["staff was rude", 15]
    print(validate_ai_response(bad_detail))             # False

    empty_reason = dict(good_output)
    empty_reason["reason"] = "   "
    print(validate_ai_response(empty_reason))           # False

    print("\n--- fallback_ai_output tests ---")
    print(validate_ai_response(fallback_ai_output()))   # True

    print("\n--- get_ai_output from gemini api tests ---")
    print(get_ai_output(dummy_complaint))