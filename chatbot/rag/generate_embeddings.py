"""
generate_embeddings.py

Generate embeddings for knowledge base chunks using OpenAI's API.
Creates FAISS index and pickled knowledge base.

Prerequisites:
    - OPENAI_API_KEY environment variable set
    - chunks.txt file created by prepare_chunks.py
    - faiss-cpu installed

Usage (from Django shell):
    python manage.py shell
    exec(open('chatbot/rag/generate_embeddings.py').read())

Or standalone:
    python generate_embeddings.py

Output:
    - chatbot/rag/kb.index (FAISS index)
    - chatbot/rag/kb.pkl (pickled knowledge base chunks)
"""

import os
import json
import pickle
import numpy as np
from openai import OpenAI
import faiss

# Configuration
CHUNKS_FILE = 'chatbot/rag/chunks.txt'
OUTPUT_DIR = 'chatbot/rag'
KB_INDEX_PATH = os.path.join(OUTPUT_DIR, 'kb.index')
KB_PKL_PATH = os.path.join(OUTPUT_DIR, 'kb.pkl')

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536  # Dimension of text-embedding-3-small


def load_chunks():
    """Load chunks from file."""
    if not os.path.exists(CHUNKS_FILE):
        raise FileNotFoundError(f"{CHUNKS_FILE} not found. Run prepare_chunks.py first.")
    
    chunks = []
    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunk = json.loads(line.strip())
                chunks.append(chunk)
    
    print(f"✓ Loaded {len(chunks)} chunks")
    return chunks


def generate_embeddings(chunks):
    """
    Generate embeddings for all chunks using OpenAI API.
    Handles batch processing for efficiency.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    print(f"\nGenerating embeddings for {len(chunks)} chunks...")
    embeddings = []
    batch_size = 100  # Process 100 chunks per API call
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        print(f"  Batch {batch_num}/{total_batches}...", end='', flush=True)
        
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch
            )
            
            # Extract embeddings in order
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            print(" ✓")
        except Exception as e:
            print(f" ✗ Error: {e}")
            raise
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings, dtype=np.float32)
    print(f"\n✓ Generated {len(embeddings)} embeddings")
    print(f"  Embedding shape: {embeddings_array.shape}")
    
    return embeddings_array


def create_faiss_index(embeddings):
    """Create and train FAISS index."""
    print(f"\nCreating FAISS index...")
    
    # Create L2 index (Euclidean distance)
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    
    # Add embeddings to index
    index.add(embeddings)
    
    print(f"✓ FAISS index created with {index.ntotal} vectors")
    return index


def save_index_and_kb(index, chunks):
    """Save FAISS index and knowledge base to disk."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save FAISS index
    faiss.write_index(index, KB_INDEX_PATH)
    print(f"✓ Saved FAISS index to {KB_INDEX_PATH}")
    
    # Save knowledge base (chunks) as pickle
    with open(KB_PKL_PATH, 'wb') as f:
        pickle.dump(chunks, f)
    print(f"✓ Saved knowledge base to {KB_PKL_PATH}")


def main():
    """Main pipeline: load chunks → generate embeddings → create index → save."""
    print("=== Smart Farm Embedding Generation ===\n")
    
    try:
        # Step 1: Load chunks
        chunks = load_chunks()
        
        # Step 2: Generate embeddings
        embeddings = generate_embeddings(chunks)
        
        # Step 3: Create FAISS index
        index = create_faiss_index(embeddings)
        
        # Step 4: Save files
        save_index_and_kb(index, chunks)
        
        print("\n✓ Embedding generation complete!")
        print(f"  Index: {KB_INDEX_PATH}")
        print(f"  Knowledge Base: {KB_PKL_PATH}")
        print("\nYou can now use the chatbot!")
        return True
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    main()
