from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from requests.exceptions import RequestException, Timeout, HTTPError
from llms.llms_accessing import llm_response
from chroma_store.chroma_client import add_file_to_collection, query_collection
from text_extraction.text_extractor import extract_text
import os

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'document' not in request.files:
        return "No file part", 400

    file = request.files['document']
    if file.filename == '':
        return "No selected file", 400

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        try:
            lines = extract_text(file_path)
            add_file_to_collection(lines, file.filename)
        except Exception as e:
            return f"Error processing file: {e}", 400

        return redirect(url_for('chatbot'))

    return "Upload failed", 400


@app.route('/chatbot')
def chatbot():
    """Render the chatbot page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat requests and return an LLM response
    augmented with retrieved context from remote ChromaDB.
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
