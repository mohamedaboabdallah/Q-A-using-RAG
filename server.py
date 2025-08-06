"""
Flask web application for chatting with a language model.

This app serves a web interface where users can input messages, which are
then processed using an LLM (Large Language Model) function. The LLM
response is returned and displayed on the frontend.

Dependencies:
- Flask: for creating the web server and routes
- python-dotenv: for loading environment variables from a .env file
- llm_response: custom function from LLMS.llms_accessing used to generate replies

Routes:
- GET /       → Serves the main HTML page.
- POST /chat  → Accepts a JSON message and returns an LLM-generated reply.

Usage:
Run this script to start a local development server:
    python app.py
"""
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout,HTTPError
from llms.llms_accessing import llm_response

load_dotenv()
app = Flask(__name__)
@app.route('/')
def index():
    """
    Render the main chat interface.

    Returns:
        The rendered HTML page (index.html) as a response to the client.
    """
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat requests sent via POST and return a response from the LLM.

    Expects:
        A JSON payload with a 'message' field containing the user's input.

    Returns:
        A JSON response with a 'reply' field containing the LLM-generated reply,
        or an error message if processing fails.
    """
    user_message = request.json['message']
    try:
        reply = llm_response(user_message)
    except Timeout:
        reply = "Request timed out."
    except ConnectionError:
        reply = "Connection error occurred."
    except HTTPError as e:
        reply = f"HTTP error: {e.response.status_code}"
    except RequestException as e:
        reply = f"Unexpected request error: {str(e)}"

    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
