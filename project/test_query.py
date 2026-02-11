from sentence_transformers import SentenceTransformer
from endee import Endee

# Configuration
INDEX_NAME = "crop_diseases"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("🔄 Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("🔄 Connecting to Endee...")
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

index = client.get_index(name=INDEX_NAME)

# Test query (change this text to test)
query_text = "diamond shaped gray spots on rice leaves"

print("🔍 Query:", query_text)

# Create embedding
query_vector = model.encode(query_text).tolist()

# Search
results = index.query(
    vector=query_vector,
    top_k=5,
    include_vectors=False
)

print("\n✅ Results:\n")

for i, item in enumerate(results, 1):
    print(f"Result {i}")
    print("ID:", item["id"])
    print("Similarity:", item["similarity"])
    print("Crop:", item["meta"].get("crop"))
    print("Disease:", item["meta"].get("disease"))
    print("-" * 40)
