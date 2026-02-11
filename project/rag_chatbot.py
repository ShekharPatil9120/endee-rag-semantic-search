from sentence_transformers import SentenceTransformer
from endee import Endee
import ollama

# =========================
# Configuration
# =========================
INDEX_NAME = "crop_diseases"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "tinyllama"   # use "phi" if you prefer
SIMILARITY_THRESHOLD = 0.45

# =========================
# Load Embedding Model
# =========================
print("🔄 Loading embedding model...")
embed_model = SentenceTransformer(MODEL_NAME)

# =========================
# Connect to Endee
# =========================
print("🔄 Connecting to Endee...")
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

try:
    index = client.get_index(name=INDEX_NAME)
except:
    print("❌ Index not found. Create index and run ingest first.")
    exit()

print("\n🌾 Smart AI Crop Assistant Ready (type 'exit')\n")

# =========================
# Chat Loop
# =========================
while True:
    user_query = input("You: ")

    if user_query.lower() == "exit":
        break

    # Step 1: Convert query to embedding
    query_vector = embed_model.encode(user_query).tolist()

    # Step 2: Retrieve from Endee
    results = index.query(vector=query_vector, top_k=3)

    if not results:
        print("AI: No relevant information found.\n")
        continue

    best_score = results[0]["similarity"]

    # Step 3: If similarity too low → skip LLM
    if best_score < SIMILARITY_THRESHOLD:
        print("AI: I’m not confident about the disease. Please provide more details.\n")
        continue

    # Step 4: Build context for LLM
    context = "\n".join([r["meta"]["text"] for r in results])

    prompt = f"""
You are an agricultural expert helping farmers.

User Query:
{user_query}

Relevant Information:
{context}

Provide:
1. Most likely disease
2. Cause
3. Immediate solution
4. Permanent treatment
5. Prevention tips

Give a clear and farmer-friendly answer.
"""

    # Step 5: Call lightweight LLM
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        print("\nAI Response:\n")
        print(response["message"]["content"])
        print("\nConfidence:", round(best_score, 2))
        print("-" * 50, "\n")

    except Exception as e:
        print("❌ LLM Error:", e)
        print("Try running: ollama pull tinyllama\n")
