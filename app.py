from flask import Flask, render_template, request, jsonify, session
import requests
import os
import json
import re
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

app = Flask(__name__)
app.secret_key = "supersecretkey"

geolocator = Nominatim(user_agent="roadie-ai")

def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            temp = data["main"]["temp"]
            description = data["weather"][0]["description"].capitalize()
            return {"temperature": f"{temp}°C", "description": description}
        else:
            return {"temperature": "N/A", "description": "Unable to fetch weather data"}
    except Exception as e:
        print("Weather API error:", e)
        return {"temperature": "N/A", "description": "Weather fetch failed"}

def get_route_info(start, end, departure_time=None):
    return {"distance": "350 miles", "duration": "5 hours 30 minutes"}

def suggest_stops(route_info, preferences=None):
    return ["Stop 1: Scenic View", "Stop 2: Famous Restaurant"]

def calculate_trip_costs(route_info, fuel_budget=None, lodging_budget=None, food_budget=None, mpg=25, fuel_price=3.5):
    return {"total_cost": "$100"}

def extract_trip_info(user_input):
    print(f"Extracting trip info for input: {user_input}")
    prompt = f"""
    Extract the road trip details from the following message:
    "{user_input}"
    Respond in JSON format with keys: intents, start, end, budgets (fuel, lodging, food), preferences, departure.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={google_api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        print("Extracted raw text:", raw_text)
        trip_info = json.loads(raw_text)
        return trip_info
    except Exception as e:
        print("Error extracting trip info:", e)
        return {
            "intents": ["route"],
            "start": None,
            "end": None,
            "budgets": {},
            "preferences": None,
            "departure": None
        }

def roadie_chat(user_input):
    weather_match = re.search(r"(?:weather|temperature)\s+(?:in\s+)?([a-zA-Z\s]+)", user_input, re.IGNORECASE)
    if weather_match:
        city = weather_match.group(1).strip()
        weather = get_weather(city)
        return {
            "text": f"The current weather in {city} is {weather['temperature']} with {weather['description']}.",
            "suggestions": [
                "Suggest a road trip",
                "Estimate budget",
                "Best stops along the way"
            ]
        }

    trip_info = extract_trip_info(user_input)
    print("Extracted Info:", trip_info)
    session["trip_info"] = trip_info

    if "route" in trip_info.get("intents", []) and trip_info.get("start") and trip_info.get("end"):
        user_input = f"Plan a road trip from {trip_info['start']} to {trip_info['end']}. "
        if trip_info.get("departure"):
            user_input += f"Departure time: {trip_info['departure']}. "
        if trip_info.get("preferences"):
            user_input += f"Preferences: {trip_info['preferences']}. "
        if trip_info.get("budgets"):
            budgets = trip_info['budgets']
            user_input += f"Budgets: Fuel - {budgets.get('fuel')}, Lodging - {budgets.get('lodging')}, Food - {budgets.get('food')}."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={google_api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": user_input}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        bot_text = data['candidates'][0]['content']['parts'][0]['text']
        return {
            "text": bot_text,
            "suggestions": [
                "Suggest a road trip",
                "Estimate budget",
                "Best stops along the way"
            ]
        }
    except Exception as e:
        print("Gemini API error:", e)
        print("Raw response:", response.text if response else "No response")
        return {
            "text": "Sorry, I couldn't fetch the data. Try again later.",
            "suggestions": []
        }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    print("User Input:", user_input)

    try:
        reply = roadie_chat(user_input)
        print("Bot Reply:", reply)
        return jsonify(reply)
    except Exception as e:
        print("Chat handler error:", e)
        return jsonify({"text": "Internal Server Error", "suggestions": []}), 500

@app.route("/reverse-geocode", methods=["POST"])
def reverse_geocode():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    try:
        location = geolocator.reverse((lat, lon), language="en")
        return jsonify({"location": location.address})
    except Exception as e:
        print("Geocoding error:", e)
        return jsonify({"location": "Unknown location"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
