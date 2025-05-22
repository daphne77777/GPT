import os
from flask import Flask, request, Response, jsonify, send_from_directory
from flask_cors import CORS
from threading import Lock
import openai

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_NAME = 'index.html'
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("Missing OPENAI_API_KEY. Please set it in environment variables.")

# App Setup
app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "https://daphne.co.za",
    "https://mp3.daphne.co.za",
    "https://fireproof.daphne.co.za"
])

# Usage Metrics
usage_data = {"messages": 0, "tokens_used": 0}
lock = Lock()

# Streaming Chat Function
def streamer(user_msg):
    global usage_data
    try:
        resp = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": user_msg}],
            stream=True
        )
        collected_text = ''
        for chunk in resp:
            text = chunk.choices[0].delta.get("content")
            if text:
                collected_text += text
                yield text

        with lock:
            usage_data["messages"] += 1
            usage_data["tokens_used"] += len(collected_text)

    except openai.error.OpenAIError as e:
        yield f"⚠️ OpenAI API Error: {str(e)}"

# Routes
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "")
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400
    return Response(streamer(user_msg), content_type="text/plain")

@app.route('/usage', methods=['GET'])
def usage():
    with lock:
        return jsonify(usage_data)

@app.route('/', methods=['GET', 'HEAD'])
def index():
    html_path = os.path.join(BASE_DIR, HTML_NAME)
    if not os.path.exists(html_path):
        return jsonify({"error": "index.html not found"}), 404
    return send_from_directory(BASE_DIR, HTML_NAME)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

