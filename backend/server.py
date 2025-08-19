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
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout, HTTPError

from llms.llms_accessing import llm_response
from chroma_store.chroma_client import add_file_to_collection, query_collection
from text_extraction.text_extractor import extract_text
from user_auth.files_handling import load_json, save_json, get_user_files
from user_auth.tokens_handling import token_required, generate_token

load_dotenv()

# === React build directory ===
BUILD_DIR = os.path.join(os.path.dirname(__file__), "frontend/build")

# === Flask app (with static assets) ===
app = Flask(
    __name__,
    static_folder=os.path.join(BUILD_DIR, "static"),
    static_url_path="/static"
)

# === CORS ===
ENABLE_CORS = os.getenv("ENABLE_CORS", "false").lower() == "true"
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")
if ENABLE_CORS and FRONTEND_ORIGIN:
    CORS(app, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}})
else:
    CORS(app, resources={r"/api/*": {"origins": "*"}})

# === Config ===
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['JWT_EXPIRATION'] = int(os.getenv('JWT_EXPIRATION', '3600'))
if os.getenv("MAX_CONTENT_LENGTH"):
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv("MAX_CONTENT_LENGTH"))

# === Data files ===
USERS_FILE, FILES_FILE = get_user_files()
users_db = load_json(USERS_FILE)
uploaded_files = load_json(FILES_FILE)

# ---------- Health ----------
@app.get("/api/health")
def api_health():
    return {"ok": True}, 200

# ---------- Auth ----------
@app.post('/api/register')
def register():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    if username in users_db:
        return jsonify({'error': 'User already exists'}), 400
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users_db[username] = hashed_pw
    save_json(users_db, USERS_FILE)
    uploaded_files.setdefault(username, [])
    save_json(uploaded_files, FILES_FILE)
    token = generate_token(username)
    return jsonify({'token': token, 'username': username}), 201

@app.post('/api/login')
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    hashed_pw_str = users_db.get(username)
    if not hashed_pw_str:
        return jsonify({'error': 'User not found'}), 401
    if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw_str.encode('utf-8')):
        return jsonify({'error': 'Incorrect password'}), 401
    token = generate_token(username)
    uploaded_files.setdefault(username, [])
    save_json(uploaded_files, FILES_FILE)
    return jsonify({'token': token, 'username': username}), 200

# ---------- Files ----------
@app.get('/api/files')
@token_required
def get_files(current_user):
    try:
        return jsonify({"files": uploaded_files.get(current_user, [])})
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"Data serialization error: {str(e)}"}), 500

@app.post('/api/upload')
@token_required
def upload_file(current_user):
    if 'document' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['document']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    try:
        valid_exts = {'.txt', '.pdf', '.docx'}
        if not any(file.filename.lower().endswith(ext) for ext in valid_exts):
            return jsonify({"error": "Invalid file type"}), 400
        file_bytes = file.read()
        lines = extract_text(file_bytes, file.filename)
        add_file_to_collection(lines, file.filename, user=current_user)
        file_info = {
            "id": len(uploaded_files.get(current_user, [])) + 1,
            "filename": file.filename,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        uploaded_files.setdefault(current_user, []).append(file_info)
        save_json(uploaded_files, FILES_FILE)
        return jsonify({"status": "success", "message": "File processed successfully", "filename": file.filename})
    except ValueError as e:
        return jsonify({"error": f"Unsupported file type: {str(e)}"}), 400
    except (OSError, IOError) as e:
        return jsonify({"error": f"File processing error: {str(e)}"}), 500

# ---------- Chat ----------
@app.post('/api/chat')
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

# ---------- Serve React (catch-all) ----------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(BUILD_DIR, path)):
        return send_from_directory(BUILD_DIR, path)
    return send_from_directory(BUILD_DIR, "index.html")

# ---------- Error handlers ----------
@app.errorhandler(413)
def too_large(_e):
    return jsonify({"error": "File too large"}), 413

# ---------- Entrypoint ----------
if __name__ == '__main__':
    port = int(os.getenv('PORT', '8080'))  # Railway sets PORT
    app.run(host='0.0.0.0', port=port, debug=False)
