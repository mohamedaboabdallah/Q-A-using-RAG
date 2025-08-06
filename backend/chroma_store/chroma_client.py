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

COLLECTION_NAME = "RAG_files"
chroma_client = chromadb.PersistentClient(path="chroma_db")  # persists locally

def get_or_create_collection():
    """
    Retrieve the existing ChromaDB collection or create it if it does not exist.

    Returns
    -------
    chromadb.api.models.Collection.Collection
        The ChromaDB collection object for storing and retrieving documents.
    """
    return chroma_client.get_or_create_collection(name=COLLECTION_NAME)

def add_file_to_collection(lines, file_name):
    """
    Add already-extracted text lines to the ChromaDB collection.

    Each line is stored as a separate document with a unique UUID and metadata
    including its line index and the source file name.

    Parameters
    ----------
    lines : list of str
        A list of text segments (e.g., lines or chunks) extracted from a file.
    file_name : str
        The name of the original file from which the text was extracted.

    Returns
    -------
    None
    """
    collection = get_or_create_collection()
    collection.upsert(
        ids=[str(uuid.uuid4()) for _ in lines],
        documents=lines,
        metadatas=[{"line": i, "source_file": file_name} for i in range(len(lines))]
    )

def query_collection(user_query, n_results=5):
    """
    Query the ChromaDB collection for the most relevant documents.

    Uses the provided user query to retrieve the top matching documents
    from the persistent ChromaDB collection based on vector similarity.

    Parameters
    ----------
    user_query : str
        The search query or question to match against stored documents.
    n_results : int, optional
        The maximum number of relevant documents to retrieve (default is 5).

    Returns
    -------
    list of list of str
        A list of lists, where each inner list contains the text of the
        retrieved documents for each query provided.
    """
    collection = get_or_create_collection()
    results = collection.query(
        query_texts=[user_query],
        n_results=n_results
    )
    return results["documents"]
