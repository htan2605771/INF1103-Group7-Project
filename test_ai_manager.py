from io_manager import collect_complaint
from ai_manager import build_prompt, call_ai_api


complaint = collect_complaint()

prompt = build_prompt(complaint)

response = call_ai_api(prompt)

print("\nGemini response:")
print(response)