from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from LLMS.llms_accessing import llm_response  # your custom LLM response function

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    
    try:
        reply = llm_response(user_message)
    except Exception as e:
        reply = f"Error: {str(e)}"

    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
