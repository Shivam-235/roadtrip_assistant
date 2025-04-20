import re
import os
import json
import requests
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from datetime import datetime

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
            return {"temperature": f"{temp}°C ({round(temp * 9/5 + 32)}°F)", "description": description}
        else:
            return {"temperature": "N/A", "description": "Unable to fetch weather data"}
    except Exception as e:
        print("Weather API error:", e)
        return {"temperature": "N/A", "description": "Weather fetch failed"}

def extract_trip_info(user_input):
    print(f"Extracting trip info for input: {user_input}")
    prompt = f"""
    Extract the road trip details from the following message:
    "{user_input}"
    Respond in JSON format with keys: 
    intents (array: route, budget, stops, weather, food, lodging), 
    start (starting location), 
    end (destination), 
    budgets (object with fuel, lodging, food as keys), 
    preferences (string, e.g. scenic, quickest, family-friendly), 
    departure (departure time),
    vehicle (vehicle type or model if mentioned),
    mpg (fuel efficiency if mentioned),
    fuel_price (price per gallon if mentioned)
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
        
        # Clean up the raw text to ensure it's valid JSON
        json_text = re.search(r'({.*})', raw_text, re.DOTALL)
        if json_text:
            cleaned_text = json_text.group(1)
            trip_info = json.loads(cleaned_text)
            return trip_info
        else:
            raise ValueError("No valid JSON found in response")
            
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

def format_response(text):
    """Format the response to be more concise and professional"""
    # Remove excessive asterisks/bullets from the response
    text = re.sub(r'\*\*', '', text)  # Remove bold markdown
    text = re.sub(r'\* ', '• ', text)  # Replace asterisk bullets with proper bullet points
    
    # Remove excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Simplify any overly verbose phrases
    text = re.sub(r'I would recommend', 'Try', text)
    text = re.sub(r'You might want to consider', 'Consider', text)
    text = re.sub(r'It is worth noting that', 'Note:', text)
    
    # Add travel-focused icons to improve readability
    text = re.sub(r'(?i)hotel|accommodation|stay|lodge', '🏨 \\g<0>', text, count=1)
    text = re.sub(r'(?i)restaurant|food|eat|dining', '🍽️ \\g<0>', text, count=1)
    text = re.sub(r'(?i)attraction|visit|sight|landmark', '🏛️ \\g<0>', text, count=1)
    text = re.sub(r'(?i)beach|ocean|sea', '🏖️ \\g<0>', text, count=1)
    text = re.sub(r'(?i)mountain|hill|trek', '⛰️ \\g<0>', text, count=1)
    text = re.sub(r'(?i)budget|cost|money|expense', '💰 \\g<0>', text, count=1)
    text = re.sub(r'(?i)time|duration|hours|minutes', '⏱️ \\g<0>', text, count=1)
    text = re.sub(r'(?i)distance|kilometers|miles', '📏 \\g<0>', text, count=1)
    
    # Limit response length if too long
    if len(text) > 800:
        # Find a good breakpoint around 800 chars
        breakpoint = text[:800].rfind('.')
        if breakpoint > 0:
            text = text[:breakpoint+1] + "\n\n(More details available on request)"
    
    return text

def beautify_route_response(text, start, end):
    """Create a more structured and visually appealing response for routes"""
    # Try to extract key information
    distance_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:miles|mi|kilometers|km)', text, re.IGNORECASE)
    time_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hours|hrs|hour|hr)(?:\s*and\s*\d+\s*(?:minutes|mins|min))?', text, re.IGNORECASE)
    fuel_match = re.search(r'(?:fuel cost|gas cost|cost of fuel|cost of gas).*?(?:\$|Rs\.?|INR)?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    
    # Format response in a cleaner structure
    result = f"🚗 {start} to {end}\n\n"
    
    if distance_match:
        result += f"📏 Distance: {distance_match.group(0)}\n"
    if time_match:
        result += f"⏱️ Duration: {time_match.group(0)}\n"
    if fuel_match:
        result += f"⛽ Est. Fuel Cost: {fuel_match.group(0)}\n"
        
    # Add a clean section for stops
    stops_section = ""
    
    # Look for stops/attractions sections in the text
    stops_match = re.search(r'(?:stops|attractions|places|visit).*?:(.*?)(?:\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
    if stops_match:
        stops_text = stops_match.group(1).strip()
        # Clean up the stops formatting
        stops_text = re.sub(r'\*\*', '', stops_text)  # Remove markdown
        stops_text = re.sub(r'\*\s*([^*\n]+)', '• \\1', stops_text)  # Replace * with bullets
        stops_section = "\n\n🏛️ Recommended Stops:\n" + stops_text
    
    # Extract road conditions if available
    road_match = re.search(r'(?:road condition|road quality|driving condition).*?:(.*?)(?:\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
    if road_match:
        road_text = road_match.group(1).strip()
        result += f"\n\n🛣️ Road Conditions:\n{road_text}"
    
    # Add tips section if available
    tips_match = re.search(r'(?:tip|advice|suggestion|recommendation).*?:(.*?)(?:\n\n|\Z)', text, re.DOTALL | re.IGNORECASE)
    if tips_match:
        tips_text = tips_match.group(1).strip()
        tips_text = re.sub(r'\*\s*([^*\n]+)', '• \\1', tips_text)  # Replace * with bullets
        result += f"\n\n💡 Travel Tips:\n{tips_text}"
    
    result += stops_section
    
    return result

def generate_trip_suggestions(start, end, preferences=None):
    """Generate trip suggestions based on the route"""
    if not (start and end):
        return []
    
    contextual_suggestions = [
        f"What's the best time to travel from {start} to {end}?",
        f"How much should I budget for a trip from {start} to {end}?",
        f"What are some must-see stops between {start} and {end}?",
        f"What's the weather forecast along the route from {start} to {end}?",
        f"Are there any scenic detours between {start} and {end}?"
    ]
    
    # Add more specialized suggestions based on preferences
    if preferences:
        if "scenic" in preferences.lower():
            contextual_suggestions.append(f"Most picturesque spots between {start} and {end}")
        if "family" in preferences.lower():
            contextual_suggestions.append(f"Family-friendly activities between {start} and {end}")
        if "budget" in preferences.lower() or "cheap" in preferences.lower():
            contextual_suggestions.append(f"Budget accommodations between {start} and {end}")
        if "food" in preferences.lower() or "culinary" in preferences.lower():
            contextual_suggestions.append(f"Must-try foods between {start} and {end}")
    
    # Add time of year specific suggestions
    current_month = datetime.now().month
    if 5 <= current_month <= 8:  # Summer
        contextual_suggestions.append(f"Swimming spots between {start} and {end}")
    elif 9 <= current_month <= 11:  # Fall
        contextual_suggestions.append(f"Fall foliage viewing between {start} and {end}")
    elif current_month == 12 or current_month <= 2:  # Winter
        contextual_suggestions.append(f"Winter driving tips from {start} to {end}")
    else:  # Spring
        contextual_suggestions.append(f"Spring festivals between {start} and {end}")
    
    # Randomize and limit the suggestions
    random.shuffle(contextual_suggestions)
    return contextual_suggestions[:5]

def is_trip_related(query):
    """Strictly determine if the query is ONLY related to trip planning or weather"""
    # Core trip-related keywords with higher specificity
    trip_keywords = [
        'trip', 'travel', 'journey', 'road', 'drive', 'driving', 'route', 
        'map', 'direction', 'distance', 'hotel', 'motel', 'gas station',
        'fuel', 'stops', 'attractions', 'weather', 'forecast', 'restaurants',
        'highway', 'interstate', 'scenic route', 'fastest', 'shortest',
        'lodging', 'accommodation', 'destination', 'vacation', 'visit',
        'car rental', 'flight', 'airport', 'train', 'bus', 'taxi', 'uber',
        'rest area', 'tourist', 'sightseeing', 'landmark', 'national park',
        'campground', 'camping', 'rv', 'scenic', 'toll', 'traffic'
    ]
    
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Check if this is a simple location query first
    location_only_pattern = r'^[A-Z][a-zA-Z\s\'\-,.]+$'
    if re.match(location_only_pattern, query):
        return True
    
    # Explicit location or map request patterns
    location_patterns = [
        r'(show|display|where\s+is|locate|find|map\s+of)\s+([A-Za-z\s,\'\.]+)',
        r'from\s+([A-Za-z\s,]+)\s+to\s+([A-Za-z\s,]+)',  
        r'between\s+([A-Za-z\s,]+)\s+and\s+([A-Za-z\s,]+)',  
        r'(nearby|near|around)\s+([A-Za-z\s,]+)', 
        r'(weather|temperature|raining|snowing|forecast)\s+(in|at|for|near)?\s*([a-zA-Z\s,]+)',
        r'how\s+(far|long|much)\s+.*?\s+to\s+([A-Za-z\s,]+)'
    ]
    
    # Check for location patterns first
    for pattern in location_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    
    # Now check for explicit trip keywords
    for keyword in trip_keywords:
        if keyword in query_lower:
            return True
    
    # If we reach here, the query isn't clearly travel-related
    print(f"Rejected non-travel query: '{query}'")
    return False

def format_trip_response_as_json(summary, details, steps, recommendations):
    """Format the trip response in a structured JSON format."""
    return {
        "summary": summary,
        "details": details,
        "steps": steps,
        "recommendations": recommendations
    }

def convert_location_query_to_descriptive(query):
    """Convert map/location queries to descriptive information requests instead"""
    # Handle "Show me X" patterns
    location_patterns = [
        (r'^show\s+(?:me\s+)?([A-Za-z\s,\'\.]+)(?:\s+on\s+(?:the\s+)?map)?$', "Tell me about {}"),
        (r'^where\s+is\s+([A-Za-z\s,\'\.]+)(?:\s+on\s+(?:the\s+)?map)?$', "What's interesting about {}?"),
        (r'^display\s+(?:a\s+)?map\s+of\s+([A-Za-z\s,\'\.]+)$', "Describe {} for travelers"),
        (r'^map\s+of\s+([A-Za-z\s,\'\.]+)$', "What should I know about {} as a traveler?"),
        (r'^([A-Za-z\s,\'\.]+)\s+map$', "Tell me about {} as a travel destination")
    ]
    
    # Try all location patterns
    for pattern, template in location_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            return template.format(location)
    
    return query  # Return original if no match

def roadie_chat(user_input, json_format=False):
    # Convert map queries to descriptive information requests
    original_input = user_input
    user_input = convert_location_query_to_descriptive(user_input)

    # First, strictly verify if the query is travel-related
    if not is_trip_related(user_input):
        return {
            "text": "I'm solely focused on travel assistance. I can help with routes, weather, accommodations, and trip planning. Please ask me travel-related questions only.",
            "suggestions": [
                "Weather in Mumbai",
                "Best stops between Delhi and Jaipur",
                "Plan a trip from Bangalore to Mysore",
                "Travel time from Chennai to Pondicherry"
            ]
        }

    # Example: Route from Delhi to Goa
    if "delhi" in user_input.lower() and "goa" in user_input.lower():
        summary = "Route from Delhi to Goa"
        details = "The journey from Delhi to Goa covers approximately 1,900-2,100 km and takes 35-40 hours of driving."
        steps = [
            "Start from Delhi and head towards Jaipur on NH48",
            "Continue on NH48 to Chittorgarh via Ajmer",
            "Proceed to Vadodara via Udaipur on NH48",
            "Drive to Mumbai on NH48",
            "Finally, take NH66 from Mumbai to Goa"
        ]
        recommendations = [
            "Plan for 3-4 days of driving with breaks",
            "Best stopovers: Jaipur, Udaipur, and Mumbai",
            "October to March is the ideal time for this journey",
            "Book accommodations in advance, especially during peak season",
            "The Mumbai-Goa stretch along NH66 offers stunning coastal views",
            "Carry sufficient cash for tolls and emergencies"
        ]

        if json_format:
            return format_trip_response_as_json(summary, details, steps, recommendations)
        else:
            formatted_text = (
                f"🚗 {summary}\n\n"
                f"📏 Distance: 1,900-2,100 km\n"
                f"⏱️ Duration: 35-40 hours of driving (recommended 3-4 days with stops)\n"
                f"🛣️ Best Season: October to March\n\n"
                f"📍 Route Details:\n" + 
                "\n".join(f"• {step}" for step in steps) + 
                "\n\n💡 Travel Tips:\n" + 
                "\n".join(f"• {rec}" for rec in recommendations)
            )
            return {
                "text": formatted_text,
                "suggestions": generate_trip_suggestions("Delhi", "Goa")
            }

    # Handle location queries with descriptive information instead of maps
    simple_location_match = None
    
    # Very simple pattern first - just a place name
    if re.match(r'^[A-Z][a-zA-Z\s,]+$', user_input.strip()):
        simple_location_match = user_input.strip()
    
    # If this was originally a map request (detected by our conversion function)
    if user_input != original_input:
        gemini_prompt = f"""
        You are Roadie, a travel assistant that provides helpful information about destinations.
        Provide a comprehensive travel guide for {simple_location_match if simple_location_match else original_input}.
        Include:
        1. A brief introduction about the location
        2. Best time to visit with seasonal highlights
        3. Top 3-4 must-see attractions with brief descriptions
        4. Local cuisine or food specialties to try
        5. Transportation options within the area
        6. 2-3 practical travel tips specific to this destination

        Keep your response well-organized with clear sections. Total length around 250 words.
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={google_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": gemini_prompt}]}],
            "generationConfig": {
                "temperature": 0.6,
                "maxOutputTokens": 400,
                "topP": 0.8
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            location_text = data['candidates'][0]['content']['parts'][0]['text']
            
            location_name = simple_location_match or "this destination"
            
            # Format the response with emojis and structure
            formatted_text = f"🌍 {location_name} Travel Guide\n\n{location_text}"
            formatted_text = formatted_text.replace("Best time to visit:", "⏰ Best time to visit:")
            formatted_text = formatted_text.replace("Attractions:", "🏛️ Attractions:")
            formatted_text = formatted_text.replace("Local cuisine:", "🍽️ Local cuisine:")
            formatted_text = formatted_text.replace("Transportation:", "🚌 Transportation:")
            formatted_text = formatted_text.replace("Travel tips:", "💡 Travel tips:")
            
            return {
                "text": formatted_text,
                "suggestions": [
                    f"Weather in {location_name}",
                    f"Things to do in {location_name}",
                    f"Hotels in {location_name}",
                    f"How to reach {location_name}",
                    f"Budget for {location_name} trip"
                ]
            }
        except Exception as e:
            print(f"Error generating location info: {e}")
    
    # Check for weather-specific queries with enhanced patterns
    weather_patterns = [
        r"(?:what'?s\s+(?:the\s+)?)?weather(?:\s+like)?\s+(?:in|at|for)\s+([a-zA-Z\s,]+)",
        r"(?:is\s+it\s+)(?:raining|snowing|sunny|cloudy|cold|hot|warm)\s+in\s+([a-zA-Z\s,]+)",
        r"temperature(?:\s+in)?\s+([a-zA-Z\s,]+)",
        r"forecast(?:\s+for)?\s+([a-zA-Z\s,]+)"
    ]
    
    for pattern in weather_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            weather = get_weather(city)
            
            # Get current date for the weather report
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Check if the query was about specific conditions
            rain_query = re.search(r"is\s+it\s+raining", user_input, re.IGNORECASE)
            snow_query = re.search(r"is\s+it\s+snowing", user_input, re.IGNORECASE)
            
            # Create a more detailed weather response
            weather_text = f"☁️ Weather in {city} ({current_date}):\n\n"
            weather_text += f"🌡️ Temperature: {weather['temperature']}\n"
            weather_text += f"🌤️ Conditions: {weather['description']}\n"
            
            # Add specific response for rain/snow queries
            if rain_query and "rain" in weather['description'].lower():
                weather_text += "\n☔ Yes, it is currently raining."
            elif rain_query:
                weather_text += "\n☀️ No, it is not currently raining."
            elif snow_query and "snow" in weather['description'].lower():
                weather_text += "\n❄️ Yes, it is currently snowing."
            elif snow_query:
                weather_text += "\n☀️ No, it is not currently snowing."
            
            # Add travel recommendations based on weather
            if "rain" in weather['description'].lower():
                weather_text += "\n\n💡 Travel Tip: Pack an umbrella and waterproof clothing. Check for indoor attractions."
            elif "snow" in weather['description'].lower():
                weather_text += "\n\n💡 Travel Tip: Roads may be slippery. Carry winter gear and check road conditions."
            elif "clear" in weather['description'].lower() or "sunny" in weather['description'].lower():
                weather_text += "\n\n💡 Travel Tip: Great day for outdoor activities! Don't forget sunscreen."
            
            return {
                "text": weather_text,
                "suggestions": [
                    f"Road conditions in {city}",
                    f"Things to do in {city} when it's {weather['description'].lower()}",
                    f"Plan a trip to {city}",
                    f"Hotels in {city}",
                    f"Restaurants in {city}"
                ]
            }

    # Extract trip information from user_input
    trip_info = extract_trip_info(user_input)
    print("Extracted Info:", trip_info)
    
    # Store trip info in session
    if "trip_info" not in session:
        session["trip_info"] = {}
    
    # Update any new information while preserving existing info
    for key, value in trip_info.items():
        if value and value != session["trip_info"].get(key):
            session["trip_info"][key] = value
    
    # Construct a prompt for Gemini that forces detailed travel-focused responses
    gemini_prompt = "You are Roadie, an AI assistant specialized in detailed road trip planning. Provide comprehensive travel advice with practical details. "
    
    if "route" in trip_info.get("intents", []) and trip_info.get("start") and trip_info.get("end"):
        gemini_prompt += f"Plan a detailed road trip from {trip_info['start']} to {trip_info['end']}. "
        
        if trip_info.get("departure"):
            gemini_prompt += f"Departure time: {trip_info['departure']}. "
        
        if trip_info.get("preferences"):
            gemini_prompt += f"Consider these preferences: {trip_info['preferences']}. "
        
        if trip_info.get("budgets"):
            budgets = trip_info['budgets']
            if budgets.get('fuel'):
                gemini_prompt += f"Fuel budget: {budgets.get('fuel')}. "
            if budgets.get('lodging'):
                gemini_prompt += f"Lodging budget: {budgets.get('lodging')}. "
            if budgets.get('food'):
                gemini_prompt += f"Food budget: {budgets.get('food')}. "
        
        if trip_info.get("mpg"):
            gemini_prompt += f"Vehicle gets {trip_info['mpg']} MPG. "
        
        if trip_info.get("fuel_price"):
            gemini_prompt += f"Fuel price is {trip_info['fuel_price']} per gallon. "
            
        gemini_prompt += "Include: total distance, driving time, best route options, estimated fuel cost, recommended stops with attractions, best time to travel, road conditions, and practical travel tips. Organize the information in clear sections."
    
    elif "budget" in trip_info.get("intents", []):
        gemini_prompt += "Provide a detailed budget breakdown for this trip including fuel costs, accommodation options at different price points, food expenses, attraction fees, and miscellaneous costs. Add money-saving tips specific to this route."
    
    elif "stops" in trip_info.get("intents", []):
        gemini_prompt += "List 5-7 excellent stops along this route. For each stop, include the name, what makes it special, one must-see attraction, a food recommendation, and approximately how long travelers should spend there."
    
    elif "weather" in trip_info.get("intents", []):
        gemini_prompt += "Provide seasonal weather information along this route, best time to travel, and how weather might affect the journey. Include practical packing suggestions based on typical weather conditions."
    
    elif "food" in trip_info.get("intents", []):
        gemini_prompt += "Recommend regional cuisine specialties along this route, noting 5-7 specific restaurants or food stops worth trying. Include price ranges and signature dishes for each recommendation."
    
    elif "lodging" in trip_info.get("intents", []):
        gemini_prompt += "Suggest accommodation options along this route for different budgets (budget, mid-range, luxury). Include specific hotel names, approximate prices, and what makes each place special or convenient for road trippers."
    
    else:
        gemini_prompt += f"Provide a detailed, travel-focused answer to this road trip question: '{user_input}'. Include practical information that will help the traveler make decisions or enhance their journey."

    # Call the Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={google_api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": gemini_prompt}]}],
        "generationConfig": {
            "temperature": 0.7,  # Slightly higher temperature for more detailed, creative responses
            "maxOutputTokens": 600,  # Increased token count for more detailed responses
            "topP": 0.85
        }
    }

    # Special handling for stops between locations
    stops_between_match = re.search(r'(?:stops|attractions|places)(?:\s+to\s+visit)?\s+between\s+([A-Za-z\s,\.]+)\s+and\s+([A-Za-z\s,\.]+)', user_input, re.IGNORECASE)
    if stops_between_match:
        start = stops_between_match.group(1).strip()
        end = stops_between_match.group(2).strip()
        
        # Construct a prompt specifically optimized for stops queries
        stops_prompt = f"""
        You are a travel expert specialized in road trips. A traveler wants to know about stops between {start} and {end}.
        Provide a detailed, helpful response with 5-7 excellent stops along this route.
        
        For each stop, include:
        1. The name of the location and its approximate distance from the starting point
        2. What makes it special or why travelers should visit
        3. The top 1-2 attractions or activities
        4. A specific food or restaurant recommendation
        5. How long travelers should ideally spend there (hours or days)
        
        Write in a concise, helpful style - no asterisks or markdown. Use normal punctuation.
        Keep the entire response well-structured with clear sections for each stop.
        """
        
        # Call the Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={google_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": stops_prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 650,
                "topP": 0.85
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            stops_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # Format the response to be more stylish and structured
            formatted_text = f"🛣️ Best Stops: {start} to {end}\n\n{stops_text}"
            
            # Add emojis to section headers in the text
            formatted_text = re.sub(r'(?m)^(\d+\.\s*[A-Z][^:]+):', r'🏙️ \1:', formatted_text)
            formatted_text = re.sub(r'(?i)(attractions?|activities):', r'🏛️ \1:', formatted_text)
            formatted_text = re.sub(r'(?i)(food|restaurant|dining):', r'🍽️ \1:', formatted_text)
            formatted_text = re.sub(r'(?i)(time|duration|spend):', r'⏱️ \1:', formatted_text)
            
            return {
                "text": formatted_text,
                "suggestions": [
                    f"Weather along {start} to {end} route",
                    f"How long is the drive from {start} to {end}?",
                    f"Hotels in {end}",
                    f"Best viewpoints between {start} and {end}",
                    f"Budget for {start} to {end} road trip"
                ]
            }
        except Exception as e:
            print(f"Error generating stops response: {e}")
            # Continue with regular processing if stops handling fails

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        bot_text = data['candidates'][0]['content']['parts'][0]['text']
        
        # Use specific formatting for route responses
        if "route" in trip_info.get("intents", []) and trip_info.get("start") and trip_info.get("end"):
            bot_text = beautify_route_response(bot_text, trip_info["start"], trip_info["end"])
        else:
            # Use general formatting for other responses
            bot_text = format_response(bot_text)
        
        # Generate contextual suggestions
        suggestions = generate_trip_suggestions(
            trip_info.get("start") or session["trip_info"].get("start"),
            trip_info.get("end") or session["trip_info"].get("end"),
            trip_info.get("preferences")
        )
        
        # Add Indian city suggestions
        indian_suggestions = [
            "Weather in Mumbai",
            "Best stops between Delhi and Jaipur",
            "Plan a trip from Bangalore to Mysore",
            "Travel time from Chennai to Pondicherry",
            "Tourist spots in Kolkata",
            "Drive from Ahmedabad to Udaipur"
        ]
        
        # Mix in some Indian suggestions with context-specific ones
        if suggestions:
            combined_suggestions = suggestions[:3] + indian_suggestions[:2]
        else:
            combined_suggestions = indian_suggestions
        
        return {
            "text": bot_text,
            "suggestions": combined_suggestions
        }
    except Exception as e:
        print("Gemini API error:", e)
        print("Raw response:", response.text if 'response' in locals() else "No response")
        return {
            "text": "Sorry, I couldn't get that information. Please try asking about another route or destination.",
            "suggestions": [
                "Plan a trip from Delhi to Agra",
                "Weather in Mumbai",
                "Best stops between Jaipur and Udaipur",
                "Travel time from Chennai to Bangalore"
            ]
        }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    json_format = request.json.get("json_format", False)
    print("User Input:", user_input)

    try:
        reply = roadie_chat(user_input, json_format=json_format)
        print("Bot Reply:", reply)
        return jsonify(reply)
    except Exception as e:
        print("Chat handler error:", e)
        return jsonify({"text": "Sorry, I'm having trouble right now. Please try again with a travel-related question.", "suggestions": []}), 500

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
    app.run(host='0.0.0.0', port=8080, debug=True)
