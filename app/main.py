import os
from flask import Flask, jsonify

app = Flask(__name__)
APP_ENV = os.getenv("APP_ENV", "local")

@app.get("/")
def home():
    return jsonify(message="Hello from zahid you have automated the Flask DevOps demo app sucessfully!", environment=APP_ENV)

@app.get("/health")
def health():
    return jsonify(status="healthy"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
