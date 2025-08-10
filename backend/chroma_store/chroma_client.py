"""
ChromaDB Persistence Module for RAG-based Applications.

This module provides helper functions to interact with a persistent
ChromaDB instance for storing and retrieving documents used in a
Retrieval-Augmented Generation (RAG) system.

Features:
---------
- Initializes a local ChromaDB persistent client (data stored in `chroma_db/`).
- Creates or retrieves a named collection ("RAG_files").
- Adds extracted text data to the collection with unique IDs and metadata.
- Queries the collection for the most relevant documents to a given user query.

Functions:
----------
- get_or_create_collection():
    Returns the ChromaDB collection object, creating it if it does not exist.

- add_file_to_collection(lines, file_name):
    Stores a list of extracted text lines into the collection with UUIDs
    and metadata (line index and source filename).

- query_collection(user_query, n_results=5):
    Retrieves the top `n_results` most relevant documents from the collection
    for a given query string.

Usage:
------
This module is intended to be used by other application components (e.g.,
Flask routes) to store documents extracted from uploaded files and to
retrieve relevant context for augmenting LLM prompts.
"""
import uuid
import chromadb

BASE_COLLECTION_NAME = "RAG_files"
chroma_client = chromadb.PersistentClient(path="chroma_db")  # persists locally


def get_or_create_collection(user: str = None):
    """
    Returns the collection for the given user.
    Option 1: Use separate collections per user (uncomment below)
    Option 2: Use single shared collection with user metadata filtering (recommended)
    """
    return chroma_client.get_or_create_collection(name=BASE_COLLECTION_NAME)


def delete_file_from_collection(file_name, user):
    """Remove all entries for a given file and user from the collection."""
    collection = get_or_create_collection(user)
    existing = collection.get(
        where={
            "$and": [
                {"source_file": {"$eq": file_name}},
                {"user": {"$eq": user}}
            ]
        }
    )
    if existing["ids"]:
        collection.delete(ids=existing["ids"])



def add_file_to_collection(lines, file_name, user):
    """
    Add extracted text lines to ChromaDB for the given user,
    replacing any old entries for that file by the user.
    """
    collection = get_or_create_collection(user)

    # Remove old entries for the file for this user only
    delete_file_from_collection(file_name, user)

    cleaned_lines = [line.strip() for line in lines if line.strip()]
    if not cleaned_lines:
        return

    collection.upsert(
        ids=[str(uuid.uuid4()) for _ in cleaned_lines],
        documents=cleaned_lines,
        metadatas=[{"line": i, "source_file": file_name, "user": user} for i in range(len(cleaned_lines))]
    )


def query_collection(user_query, user, n_results=5):
    """
    Query collection with a filter to only return documents
    uploaded by the specified user.
    """
    collection = get_or_create_collection(user)
    results = collection.query(
        query_texts=[user_query],
        n_results=n_results,
        where={"user": user}
    )
    return results["documents"]
