from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout, HTTPError
from llms.llms_accessing import llm_response
from chroma_store.chroma_client import add_file_to_collection, query_collection
from text_extraction.text_extractor import extract_text  # now works with file_bytes
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

@app.route('/')
def upload_page():
    """Render the upload page."""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and store extracted text in ChromaDB."""
    if 'document' not in request.files:
        return "No file part", 400

    file = request.files['document']
    if file.filename == '':
        return "No selected file", 400

    try:
        # Read file directly into memory
        file_bytes = file.read()

        # Extract text from bytes (text_extractor must support this)
        lines = extract_text(file_bytes, file.filename)

        # Store extracted lines in ChromaDB
        add_file_to_collection(lines, file.filename)

    except Exception as e:
        return f"Error processing file: {e}", 400

    # Redirect to chatbot page after successful processing
    return redirect(url_for('chatbot'))

@app.route('/chatbot')
def chatbot():
    """Render the chatbot page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat requests and return an LLM response
    augmented with retrieved context from ChromaDB.
    """
    user_message = request.json['message']
    try:
        # Retrieve relevant docs from ChromaDB
        retrieved_docs = query_collection(user_message, n_results=3)
        context_text = "\n".join(sum(retrieved_docs, []))  # flatten list of lists

        # Augment user query with retrieved context
        augmented_prompt = f"""
        Use the following context to answer the question.
        Context:
        {context_text}

        Question:
        {user_message}
        """

        reply = llm_response(augmented_prompt)

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
