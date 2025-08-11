"""
Flask Backend API for User Authentication, File Management, and Chatbot Interaction

This module implements a RESTful API server using Flask that supports:

- User registration and login with password hashing and JWT-based authentication.
- Uploading, storing, and managing user-specific documents, including
  text extraction and persistence in a vector database (ChromaDB).
- Secure retrieval of user-uploaded files.
- A chatbot endpoint that performs Retrieval-Augmented Generation (RAG)
  by querying stored documents relevant to user queries and generating
  context-aware responses using an LLM.

Features:
---------
- Password hashing with bcrypt for secure credential storage.
- JWT tokens with expiration for protected API routes.
- CORS enabled for API accessibility.
- File type validation (.txt, .pdf, .docx) with robust error handling.
- Persistent JSON storage for user data and uploaded file metadata.
- Integration with custom modules for text extraction, token handling,
  and vector search.

Usage:
------
Run this module to start the API server listening on port 5000.
Endpoints require an Authorization Bearer token except registration and login.

Environment Variables:
----------------------
- SECRET_KEY: Secret key for JWT encoding/decoding (default provided if unset).
- JWT_EXPIRATION: Token expiration time in seconds (default 3600).

Example Endpoints:
------------------
- POST /api/register: Register a new user.
- POST /api/login: Login and receive a JWT token.
- GET /api/files: Get list of files uploaded by the authenticated user.
- POST /api/upload: Upload and process a document file.
- POST /api/chat: Query chatbot with contextual retrieval from user files.

This module is designed for local development and demonstration purposes.
For production deployment, further security hardening and configuration
are recommended.
"""

import os
from datetime import datetime
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout, HTTPError
from llms.llms_accessing import llm_response
from chroma_store.chroma_client import add_file_to_collection, query_collection
from text_extraction.text_extractor import extract_text
from user_auth.files_handling import load_json, save_json, get_user_files
from user_auth.tokens_handling import token_required, generate_token
load_dotenv()

app = Flask(__name__)

# Allow all origins for simplicity - restrict in production!
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['JWT_EXPIRATION'] = int(os.getenv('JWT_EXPIRATION', '3600'))

USERS_FILE, FILES_FILE = get_user_files()
users_db = load_json(USERS_FILE)
uploaded_files = load_json(FILES_FILE)

@app.route('/api/register', methods=['POST'])
def register():
    """
    Register a new user with a username and password.

    Expects a JSON payload with:
        - "username": str, the desired username
        - "password": str, the desired password

    Validates input, checks if the username already exists, hashes the password
    securely using bcrypt, and stores the user credentials persistently.

    Also initializes an empty file list for the new user.

    Returns:
        - 201 Created: JSON with a JWT token and the registered username on success.
        - 400 Bad Request: JSON error message if input is missing or username exists.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    if username in users_db:
        return jsonify({'error': 'User already exists'}), 400

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_pw_str = hashed_pw.decode('utf-8')  # Convert bytes to str for JSON storage

    # Store user
    users_db[username] = hashed_pw_str
    save_json(users_db, USERS_FILE)

    # Initialize empty file list for this user
    if username not in uploaded_files:
        uploaded_files[username] = []
        save_json(uploaded_files, FILES_FILE)

    token = generate_token(username)

    return jsonify({'token': token, 'username': username}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """
    Authenticate a user and generate a JWT token upon successful login.

    Expects a JSON payload with:
        - "username": str, the username
        - "password": str, the user's password

    Validates input, verifies the username exists, and checks the password
    against the stored bcrypt hash.

    On successful authentication, generates a JWT token and ensures the user's
    uploaded files list is initialized.

    Returns:
        - 200 OK: JSON with JWT token and username on successful login.
        - 400 Bad Request: JSON error if username or password is missing.
        - 401 Unauthorized: JSON error if user not found or password is incorrect.
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    hashed_pw_str = users_db.get(username)

    if not hashed_pw_str:
        return jsonify({'error': 'User not found'}), 401

    hashed_pw = hashed_pw_str.encode('utf-8')  # Convert str back to bytes

    if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
        return jsonify({'error': 'Incorrect password'}), 401

    token = generate_token(username)

    # Ensure user has file list initialized
    if username not in uploaded_files:
        uploaded_files[username] = []
        save_json(uploaded_files, FILES_FILE)

    return jsonify({'token': token, 'username': username}), 200

@app.route('/api/files', methods=['GET'])
@token_required
def get_files(current_user):
    """
    Retrieve the list of files uploaded by the authenticated user.

    This endpoint is protected and requires a valid JWT token.

    Args:
        current_user (str): The username extracted from the JWT token by the decorator.

    Returns:
        - 200 OK: JSON containing a list of the user's uploaded files.
        - 500 Internal Server Error: JSON error message if an unexpected error occurs.
    """
    try:
        user_files = uploaded_files.get(current_user, [])
        return jsonify({"files": user_files})
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"Data serialization error: {str(e)}"}), 500

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """
    Handle uploading and processing a document file for the authenticated user.

    This endpoint expects a multipart form-data POST request with a file under
    the 'document' key. Supported file types are .txt, .pdf, and .docx.

    The file is read, text is extracted, and stored in a vector database (ChromaDB)
    under the current user's namespace. Metadata about the upload is recorded
    and persisted.

    Args:
        current_user (str): The username extracted from the JWT token by the decorator.

    Returns:
        - 200 OK: JSON confirming successful processing with the filename.
        - 400 Bad Request: JSON error if no file part, no selected file,
          or invalid file type.
        - 500 Internal Server Error: JSON error for file processing or unexpected errors.
    """
    if 'document' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['document']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        valid_extensions = {'.txt', '.pdf', '.docx'}
        if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
            return jsonify({"error": "Invalid file type"}), 400

        file_bytes = file.read()
        lines = extract_text(file_bytes, file.filename)

        # Store file contents in chroma DB, per your original logic
        add_file_to_collection(lines, file.filename, user=current_user)

        file_info = {
            "id": len(uploaded_files.get(current_user, [])) + 1,
            "filename": file.filename,
            "uploaded_at": datetime.utcnow().isoformat()
        }

        # Append to current user's uploaded files list
        uploaded_files.setdefault(current_user, []).append(file_info)
        save_json(uploaded_files, FILES_FILE)

        return jsonify({
            "status": "success",
            "message": "File processed successfully",
            "filename": file.filename
        })

    except ValueError as e:
        return jsonify({"error": f"Unsupported file type: {str(e)}"}), 400
    except (OSError, IOError) as e:
        return jsonify({"error": f"File processing error: {str(e)}"}), 500


@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
    """
    Process a chat query by retrieving relevant documents and generating a response.

    Expects a JSON payload with:
        - "query": str, the user's question or message.

    The function performs the following steps:
        - Validates the presence of the query parameter.
        - Retrieves the top relevant documents from the user's stored data.
        - Constructs an augmented prompt combining context and the user query.
        - Sends the prompt to an LLM for a generated reply.
        - Returns the matched documents and the LLM's reply.

    Args:
        current_user (str): The username extracted from the JWT token by the decorator.

    Returns:
        - 200 OK: JSON containing matched documents and the generated reply.
        - 400 Bad Request: JSON error if the query parameter is missing.
        - 503-504: JSON error on connection or timeout issues.
        - 500 Internal Server Error: JSON error for other request or server failures.
    """
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query parameter"}), 400

    user_message = data['query']
    try:
        retrieved_docs = query_collection(user_message, n_results=3, user=current_user)
        matches = []
        if retrieved_docs and retrieved_docs[0]:
            for doc in retrieved_docs[0]:
                matches.append({"text": doc})

        context_text = "\n".join([m["text"] for m in matches])
        augmented_prompt = f"""
        **Role**: You are an analytical assistant that strategically combines Context knowledge with external tools.

        **Primary Source**: Context below is your FIRST resource.

        **Tool Usage Mandate**:  
        - If Context CANNOT answer the question FULLY → Use ONE appropriate tool  
        - If question requires real-time/factual data (weather, news, etc.) → Use tools  
        - If Context partially answers → STILL call tools for missing information  
        - If context is empty or irrelevant → Use tools ONLY if necessary  

        **Available Tools** (Call EXACT names/parameters):  
        1. `get_weather(location: str)` – Current weather conditions  
        2. `get_news_headlines(category: str, country: str, limit: int)` – News headlines  
        3. `convert_currency(amount: float, from_currency: str, to_currency: str)` – Currency conversion  
        4. `search_wikipedia(query: str, sentences: int, language: str)` – Wikipedia summaries  
        5. `search_web(query: str)` – Latest/realtime info  

        **Critical Rules**:  
        ⚠️ NEVER use tools for questions the Context can fully answer  
        ⚠️ STRICTLY validate parameters (ISO codes, formats)  
        ⚠️ Use the MOST SPECIFIC tool possible  

        **Output Requirement**:  
        - ALWAYS respond in clear, natural language — even when using tools  
        - Explain tool results naturally, do not output raw JSON  

        **Context**:  
        {context_text}  

        **Question**:  
        {user_message}  

        **Reasoning Steps**:  
        1. Can Context answer COMPLETELY? → If yes, respond naturally.  
        2. If NO:  
           a. Identify required data type (weather/news/currency/facts/web)  
           b. Select precise tool and fetch info  
           c. Validate all parameters before use  
           d. Return results in fluent, natural language.
        3. Respond concisely, and to the point, using the tool results if applicable.
        """

        reply = llm_response(augmented_prompt)
        return jsonify({'matches': matches, 'reply': reply})

    except Timeout:
        return jsonify({'error': "Request timed out"}), 504
    except ConnectionError:
        return jsonify({'error': "Connection error"}), 503
    except HTTPError as e:
        return jsonify({'error': f"HTTP error: {e.response.status_code}"}), e.response.status_code
    except RequestException as e:
        return jsonify({'error': f"Request error: {str(e)}"}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
