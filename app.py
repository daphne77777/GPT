import os
import openai
from flask import Flask, request, Response, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_NAME = 'index.html'

app = Flask(__name__)
CORS(app, origins=["*"])
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "")
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    def streamer():
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_msg}],
            stream=True
        )
        for chunk in resp:
            text = chunk.choices[0].delta.get("content")
            if text:
                yield text

    return Response(streamer(), content_type="text/plain")

@app.route('/usage', methods=['GET'])
def usage():
    return jsonify({"messages": 0, "tokens_used": 0})

@app.route('/', methods=['GET', 'HEAD'])
def index():
    return send_from_directory(BASE_DIR, HTML_NAME)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
