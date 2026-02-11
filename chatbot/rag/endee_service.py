from sentence_transformers import SentenceTransformer
from endee import Endee

INDEX_NAME = "crop_diseases"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIM_THRESHOLD = 0.45

print("Loading Endee model...")
embed_model = SentenceTransformer(MODEL_NAME)

print("Connecting to Endee...")
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

index = client.get_index(name=INDEX_NAME)

print("Endee Ready")


def get_endee_response(question):
    if not question or len(question.split()) < 3:
        return {
            "reply": "Please describe symptoms clearly (example: rice leaves brown spots)."
        }

    query_vector = embed_model.encode(question).tolist()
    results = index.query(vector=query_vector, top_k=1)

    if not results:
        return {"reply": "No disease information found."}

    best = results[0]
    score = best["similarity"]

    if score < SIM_THRESHOLD:
        return {
            "reply": "I’m not confident. Please provide more detailed symptoms.",
            "confidence": round(score, 2)
        }

    meta = best["meta"]

    reply = f"""
Crop: {meta.get('crop')}
Disease: {meta.get('disease')}

Details:
{meta.get('text')}
"""

    return {
        "reply": reply,
        "confidence": round(score, 2)
    }
