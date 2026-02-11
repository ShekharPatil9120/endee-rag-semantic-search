from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
from endee import Endee
import ollama

# ==============================
# Configuration
# ==============================
INDEX_NAME = "crop_diseases"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "tinyllama"   # or "phi"
SIM_THRESHOLD = 0.45

# ==============================
# Flask Setup
# ==============================
app = Flask(__name__)
CORS(app)

# ==============================
# Load Models (load once)
# ==============================
print("Loading embedding model...")
embed_model = SentenceTransformer(MODEL_NAME)

print("Connecting to Endee...")
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

try:
    index = client.get_index(name=INDEX_NAME)
except:
    print("Index not found! Create index and run ingestion first.")
    exit()

print("System Ready")

# ==============================
# Health Route
# ==============================
@app.route("/")
def home():
    return "AI Crop Assistant API is running"

# ==============================
# Chat Route
# ==============================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_query = data.get("message", "").strip()

    if not user_query:
        return jsonify({"reply": "Please enter symptoms."})

    if len(user_query.split()) < 3:
        return jsonify({
            "reply": "Please describe symptoms clearly (example: 'tomato leaves yellow with brown spots')."
        })

    # Embed query
    query_vector = embed_model.encode(user_query).tolist()

    # Retrieve best match
    results = index.query(vector=query_vector, top_k=1)

    if not results:
        return jsonify({"reply": "No disease information found."})

    best = results[0]
    score = best["similarity"]

    if score < 0.45:
        return jsonify({
            "reply": "I’m not confident. Please provide more detailed symptoms.",
            "confidence": round(score, 2)
        })

    # ===== Use stored metadata directly =====
    text = best["meta"]["text"]
    crop = best["meta"].get("crop", "Unknown")
    disease = best["meta"].get("disease", "Unknown")

    reply = f"""
Crop: {crop}
Disease: {disease}

Details:
{text}
"""

    return jsonify({
        "reply": reply,
        "confidence": round(score, 2)
    })


# ==============================
# Run Server
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
