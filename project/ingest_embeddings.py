import json
import uuid
from sentence_transformers import SentenceTransformer
from endee import Endee

# Configuration
INDEX_NAME = "crop_diseases"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DATA_FILE = "data.json"

print("🔄 Loading embedding model (384-dim)...")
model = SentenceTransformer(MODEL_NAME)

print("🔄 Connecting to Endee...")
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")   # as per docs

index = client.get_index(name=INDEX_NAME)

print("🔄 Loading data...")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

vectors = []

print("🔄 Creating embeddings...")
for crop, diseases in data.items():
    for d in diseases:
        text = (
            f"Crop: {crop}. "
            f"Disease: {d['disease']}. "
            f"Symptoms: {d['symptoms']}. "
            f"Temporary solution: {d['temporary_solution']}. "
            f"Permanent solution: {d['permanent_solution']}. "
            f"Prevention advice: {d['prevention_advice']}."
        )

        embedding = model.encode(text).tolist()

        vectors.append({
            "id": str(uuid.uuid4()),
            "vector": embedding,
            "meta": {
                "crop": crop,
                "disease": d["disease"],
                "text": text
            },
            "filter": {
                "crop": crop
            }
        })

print(f"🚀 Upserting {len(vectors)} vectors to Endee...")

index.upsert(vectors)

print("✅ Upload completed successfully!")
