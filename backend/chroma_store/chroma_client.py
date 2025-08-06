import chromadb
from chromadb.config import Settings
import uuid

COLLECTION_NAME = "RAG_files"
chroma_client = chromadb.PersistentClient(path="chroma_db")  # persists locally

def get_or_create_collection():
    return chroma_client.get_or_create_collection(name=COLLECTION_NAME)

def add_file_to_collection(lines, file_name):
    """Add already-extracted text lines to ChromaDB."""
    collection = get_or_create_collection()
    collection.upsert(
        ids=[str(uuid.uuid4()) for _ in lines],
        documents=lines,
        metadatas=[{"line": i, "source_file": file_name} for i in range(len(lines))]
    )

def query_collection(user_query, n_results=5):
    collection = get_or_create_collection()
    results = collection.query(
        query_texts=[user_query],
        n_results=n_results
    )
    return results["documents"]