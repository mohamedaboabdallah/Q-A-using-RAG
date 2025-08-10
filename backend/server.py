import os
import jwt
import bcrypt
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout, HTTPError
from llms.llms_accessing import llm_response
from chroma_store.chroma_client import add_file_to_collection, query_collection
from text_extraction.text_extractor import extract_text

load_dotenv()

app = Flask(__name__)

# Allow all origins for simplicity - restrict in production!
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['JWT_EXPIRATION'] = int(os.getenv('JWT_EXPIRATION', 3600))

USERS_FILE = 'users_db.json'
FILES_FILE = 'uploaded_files.json'


def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}


def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


# Load persisted data on startup
users_db = load_json(USERS_FILE)
uploaded_files = load_json(FILES_FILE)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', None)
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        if not token:
            return jsonify({'error': 'Authorization token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': f'Token verification failed: {str(e)}'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


def generate_token(username):
    token = jwt.encode({
        'sub': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=app.config['JWT_EXPIRATION'])
    }, app.config['SECRET_KEY'], algorithm='HS256')
    return token


@app.route('/api/register', methods=['POST'])
def register():
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
    try:
        # Return only files for current user
        user_files = uploaded_files.get(current_user, [])
        return jsonify({"files": user_files})
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file(current_user):
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
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route('/api/chat', methods=['POST'])
@token_required
def chat(current_user):
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

        if matches:
            context_text = "\n".join([m["text"] for m in matches])
            augmented_prompt = f"""
            Use the following context to answer the question.
            Context:
            {context_text}

            Question:
            {user_message}
            """
            reply = llm_response(augmented_prompt)
            return jsonify({'matches': matches, 'reply': reply})
        else:
            return jsonify({'matches': [], 'reply': "No relevant context found for your query."})

    except Timeout:
        return jsonify({'error': "Request timed out"}), 504
    except ConnectionError:
        return jsonify({'error': "Connection error"}), 503
    except HTTPError as e:
        return jsonify({'error': f"HTTP error: {e.response.status_code}"}), e.response.status_code
    except RequestException as e:
        return jsonify({'error': f"Request error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': f"Server error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
