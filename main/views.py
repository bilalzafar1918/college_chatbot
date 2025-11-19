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

            # Case: dictionary has an "xyz_answer" key
            if isinstance(value, dict) and answer_key in value:
                return value[answer_key]

            # Special case: environment
            if key in ['flora', 'fauna', 'landscape_features', 'environment']:
                env_answer = data.get('environment', {}).get('', None)
                if env_answer:
                    return env_answer

            # If value itself is a dict: combine its child values
            if isinstance(value, dict):
                return ", ".join([
                    str(v) for v in value.values()
                    if isinstance(v, str)
                ])

            # If value is list
            if isinstance(value, list):
                # House answers list
                if all(isinstance(i, dict) for i in value):
                    answers = []
                    for item in value:
                        if "house_answer" in item:
                            answers.append(item["house_answer"])
                    return "\n".join(answers)
                return ", ".join(str(i) for i in value)

            # Simply return the value (string, number etc.)
            return str(value)

        # --- Flatten JSON keys ---
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

        # --- Handle Houses (Sarwar, Tufail, etc.) ----
        houses_data = data.get("houses", {})
        house_found = False

        for key, house in houses_data.items():
            if key == "houses_answer":
                continue  # Skip general answer

            house_name_lower = key.replace("_house", "").replace("_", " ")

            if house_name_lower in user_message:
                # Example: key = "sarwar_house", house = {"sarwar_answer": "..."}
                answer_key = list(house.keys())[0]
                response = house[answer_key]
                house_found = True
                break

        # If user asked about houses generally
        if not house_found and ("house" in user_message or "houses" in user_message):
            general = houses_data.get("houses_answer", "MCM has the following houses:")
            response = general
            return JsonResponse({"response": response})

        # --- Search flattened JSON if not house-related ---
        if not house_found:
            # 1. Try exact match
            exact_key = user_message.replace(" ", "_")
            if exact_key in flat_data:
                response = fetch_answer(exact_key, flat_data[exact_key])
                return JsonResponse({"response": response})

            # 2. Try partial match: any word matches JSON key
            for key, value in flat_data.items():
                if any(word in key for word in user_message.split()):
                    response = fetch_answer(key, value)
                    return JsonResponse({"response": response})

        return JsonResponse({"response": response})

    return JsonResponse({"response": "Invalid request method."})
