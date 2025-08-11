# llms/tools.py
import os
import json
import requests
import wikipedia
from io import BytesIO
from PIL import Image

def format_api_response(response):
    """
    General-purpose API response formatter for news, currency, weather, etc.
    """

    if not isinstance(response, dict):
        try:
            response = json.loads(response)
        except Exception:
            return "⚠️ Invalid API response format."

    # --- NEWS ---
    if "headlines" in response and isinstance(response["headlines"], list):
        category = response.get("category", "News").capitalize()
        country = response.get("country", "").upper()
        lines = [f"📰 **{category} Headlines** {f'({country})' if country else ''}"]
        for idx, item in enumerate(response["headlines"], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            lines.append(f"{idx}. [{title}]({url})")
        return "\n".join(lines)

    # --- CURRENCY (Format 1: from/to/rate) ---
    if "from" in response and "to" in response and "rate" in response:
        return f"💱 **{response['from']} → {response['to']}**: {response['rate']}\n_Last updated: {response.get('timestamp', 'unknown')}_"

    # --- CURRENCY (Format 2: amount/from_currency/to_currency/converted_amount) ---
    if all(k in response for k in ["amount", "from_currency", "to_currency", "converted_amount"]):
        return (
            f"💱 **Currency Conversion**\n"
            f"{response['amount']} {response['from_currency']} → {response['converted_amount']:.2f} {response['to_currency']}"
        )

    # --- WEATHER ---
    if "temperature" in response and "condition" in response:
        return (
            f"🌤 **Weather in {response.get('location', 'Unknown')}**\n"
            f"Temp: {response['temperature']}°C\n"
            f"Condition: {response['condition']}\n"
            f"Humidity: {response.get('humidity', 'N/A')}%"
        )

    # --- FALLBACK: Generic JSON Pretty Print ---
    try:
        return "📦 **API Response:**\n```json\n" + json.dumps(response, indent=2) + "\n```"
    except Exception:
        return str(response)


def geocode_location(location):
    """Convert location string to (lat, lon) using OpenStreetMap Nominatim API."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location.strip(), "format": "json", "limit": 1}
    headers = {"User-Agent": "weather-tool/1.0 (mohamed541416@gmail.com)"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        results = response.json()
        if not results:
            return None, None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        return None, None


def get_weather(location):
    """
    Fetch current weather for a location string using Open-Meteo API.
    Returns a structured JSON string so the LLM can use it.
    """
    lat, lon = geocode_location(location)
    if lat is None or lon is None:
        return json.dumps({"error": f"Could not find coordinates for '{location}'"})

    weather_url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current_weather": True, "timezone": "auto"}

    try:
        response = requests.get(weather_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        current = data.get("current_weather")
        if not current:
            return json.dumps({"error": "No current weather data available."})

        weather_descriptions = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
            55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        }
        description = weather_descriptions.get(current.get("weathercode"), "Unknown weather")

        return format_api_response(json.dumps({
            "location": location,
            "description": description,
            "temperature_c": current.get("temperature"),
            "windspeed_kmh": current.get("windspeed")
        }))

    except Exception as e:
        return json.dumps({"error": f"Error fetching weather data: {str(e)}"})


def convert_currency(amount, from_currency, to_currency):
    api_key = os.getenv("currency_key")
    url = (
        f"http://api.currencylayer.com/convert"
        f"?access_key={api_key}"
        f"&from={from_currency}"
        f"&to={to_currency}"
        f"&amount={amount}"
    )
    
    try:
        response = requests.get(url)
        data = response.json()

        if not data.get("success"):
            return {"error": f"API reported failure: {data}"}

        return format_api_response({
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": data.get("result")
        })

    except Exception as e:
        return {"error": f"Currency conversion failed: {e}"}

def get_news_headlines(category, country, limit=5):
    """
    Fetch the latest news headlines for a given category and country using TheNewsAPI.com.
    Returns a JSON string with headlines or error information.
    """
    api_key = os.getenv("news_key")  # Replace with your actual key
    url = "https://api.thenewsapi.com/v1/news/top"
    params = {
        "api_token": api_key,
        "category": category,
        "country": country,
        "limit": limit
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        if not data.get("data"):
            return json.dumps({"error": f"No headlines found for category={category}, country={country}"})

        headlines = [
            {"title": item.get("title"), "url": item.get("url")}
            for item in data["data"][:limit]
        ]
        return format_api_response(json.dumps({
            "category": category,
            "country": country,
            "headlines": headlines
        }))

    except Exception as e:
        return json.dumps({"error": f"Error fetching news: {str(e)}"})

def search_wikipedia(query: str, sentences: int = 2, language: str = "en") -> str:
    """
    Search Wikipedia and return a summary.

    Args:
        query (str): Search term.
        sentences (int, optional): Number of sentences to return. Default is 2.
        language (str, optional): Wikipedia language code (e.g., 'en', 'fr'). Default is English.

    Returns:
        str: Wikipedia summary or error message.
    """
    try:
        wikipedia.set_lang(language)
        summary = wikipedia.summary(query, sentences=sentences)
        return summary
    except wikipedia.DisambiguationError as e:
        return f"Multiple results found: {', '.join(e.options[:5])}..."
    except wikipedia.PageError:
        return "No page found for your query."
    except Exception as e:
        return f"Error: {str(e)}"

def search_web(query: str):
    """
    Search the web for general information using DuckDuckGo's Instant Answer API.
    Returns a short summary or related topics.
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        # Prefer the abstract text if available
        if data.get("AbstractText"):
            return data["AbstractText"]
        
        # If no abstract, try related topics
        elif data.get("RelatedTopics"):
            topics = [t.get("Text") for t in data["RelatedTopics"] if "Text" in t][:3]
            if topics:
                return "Related topics: " + "; ".join(topics)
        
        return "No relevant information found."
    
    except Exception as e:
        return f"Error during search: {str(e)}"
