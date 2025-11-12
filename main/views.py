import json
import os
from django.http import JsonResponse
from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')

def get_response(request):
    if request.method == "POST":
        user_message = request.POST.get('message', '').lower().strip()

        # Load JSON data
        json_path = os.path.join(os.path.dirname(__file__), 'college_data.json')
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        response = "I'm not sure about that. Could you rephrase?"

        # --- Helper function to fetch answer ---
        def fetch_answer(key, value):
            answer_key = f"{key}_answer"
            if isinstance(value, dict) and answer_key in value:
                return value[answer_key]

            if key in ['flora', 'fauna', 'landscape_features', 'environment']:
                env_answer = data.get('environment', {}).get('environment_answer', None)
                if env_answer:
                    return env_answer

            if isinstance(value, dict):
                return ", ".join([f"{k.replace('_', ' ')}: {v}" for k, v in value.items()])

            if isinstance(value, list):
                if all(isinstance(i, dict) for i in value):
                    answers = []
                    for item in value:
                        if "house_answer" in item:
                            answers.append(item["house_answer"])
                    return "\n".join(answers)
                return ", ".join(str(i) for i in value)

            return f"The {key.replace('_', ' ')} of MCM is {value}."

        # --- Flatten JSON for quick key lookup ---
        flat_data = {}
        def flatten_json(obj, prefix=''):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_prefix = k.lower() if not prefix else f"{prefix}_{k.lower()}"
                    flatten_json(v, new_prefix)
            elif isinstance(obj, list):
                flat_data[prefix] = obj
            else:
                flat_data[prefix] = obj
        flatten_json(data)

        # --- Handle houses ---
        houses_data = data.get("houses", {})
        house_found = False

        # Check if user asked for a specific house
        for key, house in houses_data.items():
            if key == "houses_answer":
                continue  # skip general answer
            house_name_lower = key.replace("_house", "").replace("_", " ")
            if house_name_lower in user_message:
                # Get the answer dynamically
                answer_key = list(house.keys())[0]  # e.g., 'sarwar_answer'
                response = house[answer_key]
                house_found = True
                break

        # If user asked "houses" generally
        if not house_found and ("house" in user_message or "houses" in user_message):
            general_list = []
            for key, house in houses_data.items():
                if key == "houses_answer":
                    continue
                answer_key = list(house.keys())[0]
                general_list.append(house[answer_key])
            response = houses_data.get("houses_answer", "MCM has the following houses:") + "\n" + "\n".join(general_list)

        # If not a house query, search other keys in flattened JSON
        if not house_found and "house" not in user_message and "houses" not in user_message:
            for key, value in flat_data.items():
                if key in user_message or any(word in key for word in user_message.split()):
                    response = fetch_answer(key, value)
                    break

        return JsonResponse({"response": response})

    return JsonResponse({"response": "Invalid request method."})
