from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


from sentence_transformers import SentenceTransformer
from endee import Endee

# ==============================
# Configuration
# ==============================
INDEX_NAME = "crop_diseases"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIM_THRESHOLD = 0.45

# ==============================
# Load Models (Load once)
# ==============================
print("Loading Endee embedding model...")
embed_model = SentenceTransformer(MODEL_NAME)

print("Connecting to Endee...")
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

try:
    index = client.get_index(name=INDEX_NAME)
except:
    print("❌ Index not found! Create index and run ingestion first.")
    index = None

print("Endee Chatbot Ready")


# ==============================
# Endee RAG Logic
# ==============================
def get_endee_response(question):
    if not question:
        return {"reply": "Please ask a question."}

    if len(question.split()) < 3:
        return {
            "reply": "Please describe symptoms clearly (example: rice leaves have brown spots)."
        }

    if index is None:
        return {"reply": "Vector database not available."}

    # Convert to embedding
    query_vector = embed_model.encode(question).tolist()

    # Search Endee
    results = index.query(vector=query_vector, top_k=1)

    if not results:
        return {"reply": "No disease information found."}

    best = results[0]
    score = best["similarity"]

    # Confidence check
    if score < SIM_THRESHOLD:
        return {
            "reply": "I’m not confident. Please provide more detailed symptoms.",
            "confidence": round(score, 2)
        }

    meta = best["meta"]

    reply = f"""
Crop: {meta.get('crop', 'Unknown')}
Disease: {meta.get('disease', 'Unknown')}

Details:
{meta.get('text', '')}
"""

    return {
        "reply": reply,
        "confidence": round(score, 2)
    }


# ==============================
# Chat API (Called by frontend)
# ==============================
@csrf_exempt
@require_http_methods(["GET"])
def rag_chatbot(request):
    question = request.GET.get("q", "").strip()
    result = get_endee_response(question)
    return JsonResponse(result)


# ==============================
# Chat Page
# ==============================
@require_http_methods(["GET"])
def chat_page(request):
    return render(request, "chatbot/chat.html")
