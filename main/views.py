import json
import os
import re
from django.http import JsonResponse
from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')


def get_response(request):
    if request.method != "POST":
        return JsonResponse({"response": "Invalid request method."})

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
        if isinstance(value, dict):
            return ", ".join([str(v) for v in value.values() if isinstance(v, str)])
        if isinstance(value, list):
            if all(isinstance(i, dict) for i in value):
                answers = []
                for item in value:
                    if "house_answer" in item:
                        answers.append(item["house_answer"])
                return "\n".join(answers)
            return ", ".join(str(i) for i in value)
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

    # --- Handle Houses ---
    houses_data = data.get("houses", {})
    house_found = False

    for key, house in houses_data.items():
        if key == "houses_answer":
            continue
        house_name_lower = key.replace("_house", "").replace("_", " ")
        # Full word match for house
        if re.search(rf'\b{re.escape(house_name_lower)}\b', user_message):
            answer_key = list(house.keys())[0]
            response = house[answer_key]
            house_found = True
            break

    if not house_found and re.search(r'\b(house|houses)\b', user_message):
        response = houses_data.get("houses_answer", "MCM has the following houses:")
        return JsonResponse({"response": response})

    # --- Search flattened JSON ---
    if not house_found:
        # 1. Exact phrase match
        for key, value in flat_data.items():
            key_words = key.split("_")
            if all(re.search(rf'\b{re.escape(word)}\b', user_message) for word in key_words):
                response = fetch_answer(key, value)
                return JsonResponse({"response": response})

        # 2. Partial match on individual words (only meaningful)
        stopwords = {"is", "the", "a", "an", "of", "to", "and", "in", "for", "on"}
        user_words = [w for w in re.findall(r'\w+', user_message) if w not in stopwords]

        for key, value in flat_data.items():
            key_words = key.split("_")
            if any(kw in user_words for kw in key_words):
                response = fetch_answer(key, value)
                return JsonResponse({"response": response})

    return JsonResponse({"response": response})
