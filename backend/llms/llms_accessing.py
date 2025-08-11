"""
LLM response module using Groq API and gpt-oss-120b model.

This module defines a function `llm_response` that sends a user message to the Groq-hosted
OpenAI-compatible API endpoint using the gpt-oss-120b model (`gpt-oss-120b`). It constructs
a chat-style payload, sends it via a POST request, and returns the model's textual response.

Environment:
    Expects a .env file with the following variable:
        GROQ_API_KEY - your API key for authenticating with the Groq API.

Dependencies:
    - requests: for making HTTP requests
    - python-dotenv: for loading environment variables

Functions:
    - llm_response(msg_to_repond_to): Sends a message to the model and returns its reply.
        Returns a string on success, or a tuple (status_code, error_message) on failure.
"""
import os
from dotenv import load_dotenv
import requests
import json
from llms.tools import get_weather, convert_currency, get_news_headlines,search_wikipedia, search_web

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# ------------------- TOOL DEFINITIONS -------------------
tool_kit = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City and state"}
                },
                "required": ["location"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "convert_currency",
        "description": "Convert an amount from one currency to another",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": { "type": "number" },
                "from_currency": { "type": "string" },
                "to_currency": { "type": "string" }
            },
            "required": ["amount", "from_currency", "to_currency"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_headlines",
            "description": "Fetch latest news headlines for a given category and country",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "business, tech, sports, etc."},
                    "country": {"type": "string", "description": "Two-letter country code"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["category", "country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia and return a summary",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "sentences": {"type": "integer", "default": 2},
                    "language": {"type": "string", "default": "en"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for general information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]
# ------------------- Tool Function -------------------
tool_functions = {
    "get_weather": get_weather,
    "convert_currency": convert_currency,
    "get_news_headlines": get_news_headlines,
    "search_wikipedia": search_wikipedia,
    "search_web": search_web
}

# ------------- LLM Response --------
def llm_response(msg_to_repond_to):
    """
    Send a user message to the Groq API using the LLaMA 3 model and return the generated response.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "user", "content": msg_to_repond_to},
        ],
        "tools": tool_kit,      # Correct way to pass tools
        "tool_choice": "auto",  # Let model decide when to call tools
        "temperature": 0.3,
        "max_tokens": 512,
        "top_p": 0.9
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)

    if response.status_code == 200:
        result = response.json()
        message = result["choices"][0]["message"]

        # If the model calls a tool
        if "tool_calls" in message:
            for call in message["tool_calls"]:
                func_name = call["function"]["name"]
                args = json.loads(call["function"]["arguments"])
                if func_name in tool_functions:
                    tool_result = tool_functions[func_name](**args)
                    return str(tool_result)

        # Otherwise, just return text
        return message.get("content", "")

    return (response.status_code, response.text)
