import json
import os

def load_data():
    path = os.path.join(os.path.dirname(__file__), 'college_data.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_response(user_input):
    data = load_data()
    user_input = user_input.lower()

    if "department" in user_input:
        return data["departments"]
    elif "admission" in user_input:
        return data["admissions"]
    elif "library" in user_input:
        return data["library"]
    elif "event" in user_input or "fest" in user_input:
        return data["events"]
    else:
        return "Sorry, I don’t have that information right now."
