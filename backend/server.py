import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout, HTTPError
from llms.llms_accessing import llm_response
from chroma_store.chroma_client import add_file_to_collection, query_collection
from text_extraction.text_extractor import extract_text

# Load environment variables
load_dotenv()
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
# JWT Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['JWT_EXPIRATION'] = int(os.getenv('JWT_EXPIRATION', 3600))  # 1 hour

def token_required(f):
    """JWT Authentication Decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
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

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'error': 'Missing credentials'}), 400
    
    try:
        # Accept any non-empty credentials
        username = auth['username']
        
        # Create JWT token
        token = jwt.encode({
            'sub': username,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=app.config['JWT_EXPIRATION'])
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'username': username,
            'expires_in': app.config['JWT_EXPIRATION']
        })
        
    except Exception as e:
        return jsonify({'error': f'Login processing error: {str(e)}'}), 500

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """Handle file upload and store in ChromaDB"""
    if 'document' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['document']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Check file extension
        valid_extensions = {'.txt', '.pdf', '.docx'}
        if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
            return jsonify({"error": "Invalid file type"}), 400

        # Read file into memory
        file_bytes = file.read()

        # Extract text
        lines = extract_text(file_bytes, file.filename)

        # Store in ChromaDB
        add_file_to_collection(lines, file.filename)

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
    """Handle chat requests with RAG"""
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Missing message parameter"}), 400

    user_message = data['message']
    
    try:
        # Retrieve relevant context
        retrieved_docs = query_collection(user_message, n_results=3)
        context_text = "\n".join(sum(retrieved_docs, []))  # flatten

        # Augment prompt with context
        augmented_prompt = f"""
        Use the following context to answer the question.
        Context:
        {context_text}

        Question:
        {user_message}
        """

        reply = llm_response(augmented_prompt)

        return jsonify({'reply': reply})

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