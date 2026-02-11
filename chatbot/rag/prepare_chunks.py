"""
prepare_chunks.py

Prepare knowledge base chunks from source documents.
This script reads source files and creates text chunks with overlap.

Usage:
    python manage.py shell < prepare_chunks.py

Output:
    Saves chunks to chatbot/rag/chunks.txt (one chunk per line)
"""

import os
import json

# Configure these paths
SOURCE_FILES = {
    'project_docs': 'chatbot/rag/source_docs.txt',  # Your project documentation
    # Add more sources as needed
}

CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 100  # Overlap between chunks


def load_documents():
    """Load all source documents."""
    documents = {}
    for name, path in SOURCE_FILES.items():
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                documents[name] = f.read()
                print(f"✓ Loaded {name}: {len(documents[name])} characters")
        else:
            print(f"⚠ Warning: {name} not found at {path}")
    return documents


def create_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split text into overlapping chunks.
    Returns: list of chunk strings
    """
    chunks = []
    step = chunk_size - overlap
    
    for i in range(0, len(text), step):
        chunk = text[i:i + chunk_size]
        if len(chunk) > 50:  # Only keep chunks with meaningful content
            chunks.append(chunk.strip())
    
    return chunks


def process_documents(documents):
    """Process documents into chunks."""
    all_chunks = []
    
    for doc_name, content in documents.items():
        print(f"\nProcessing {doc_name}...")
        chunks = create_chunks(content)
        all_chunks.extend(chunks)
        print(f"  Created {len(chunks)} chunks")
    
    return all_chunks


def save_chunks(chunks):
    """Save chunks to file (one per line, JSON encoded)."""
    output_path = 'chatbot/rag/chunks.txt'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            # Store as JSON for safe encoding/decoding
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    print(f"\n✓ Saved {len(chunks)} chunks to {output_path}")
    return output_path


def main():
    """Main pipeline: load → chunk → save."""
    print("=== Smart Farm Knowledge Base Preparation ===\n")
    
    # Step 1: Load documents
    documents = load_documents()
    if not documents:
        print("✗ No documents loaded. Please add source files.")
        return False
    
    # Step 2: Create chunks
    chunks = process_documents(documents)
    print(f"\nTotal chunks created: {len(chunks)}")
    
    # Step 3: Save chunks
    save_chunks(chunks)
    
    print("\n✓ Knowledge base preparation complete!")
    print("Next step: Run generate_embeddings.py to create embeddings")
    return True


if __name__ == '__main__':
    main()
