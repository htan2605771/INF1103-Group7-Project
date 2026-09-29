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


def call_ai_api(prompt): # Send the prompt to the AI API and handle API failures
    pass


def parse_ai_response(response): # parse the AI response into JSON
    pass


def validate_ai_response(ai_output): # validate that the AI output follows the required schema
    pass


def process_complaint(complaint): # run a complaint through the complete AI processing flow
    pass