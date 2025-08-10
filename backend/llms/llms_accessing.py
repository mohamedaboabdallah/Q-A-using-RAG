"""
LLM response module using Groq API and LLaMA 3 model.

This module defines a function `llm_response` that sends a user message to the Groq-hosted
OpenAI-compatible API endpoint using the LLaMA 3 model (`llama3-8b-8192`). It constructs
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
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")


def llm_response(msg_to_repond_to):
    """
    Send a user message to the Groq API using the LLaMA 3 model and return the generated response.

    Args:
        msg_to_repond_to (str): The input message from the user to be processed
        by the language model.

    Returns:
        str: The model-generated response if the request is successful.
        tuple: A tuple (status_code, error_message) if the API request fails.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": msg_to_repond_to},
        ],
        "temperature": 0.7,   # more randomness → more flexible answers
        "max_tokens": 1024,   # allow longer, more nuanced responses
        "top_p": 0.9          # include a wider set of possible tokens
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    return (response.status_code, response.text)
