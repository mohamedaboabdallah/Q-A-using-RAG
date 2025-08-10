"""
ChromaDB Persistence Module for User-Specific Document Storage and Retrieval.

This module provides functions to interact with a persistent ChromaDB instance,
enabling storage and retrieval of extracted text documents in a Retrieval-Augmented
Generation (RAG) system, with multi-user support.

Key Features:
-------------
- Initializes a persistent local ChromaDB client storing data under `chroma_db/`.
- Supports storing text lines extracted from files with associated metadata,
  including filename and user identity.
- Ensures user data isolation by filtering queries and deletions by user.
- Allows querying for the most relevant documents uploaded by a specific user.
- Automatically removes old entries when adding updated files for the same user.

Functions:
----------
- get_or_create_collection(user=None):
    Returns the shared ChromaDB collection instance. Supports potential user-based
    collection management (currently using a single shared collection).

- delete_file_from_collection(file_name, user):
    Deletes all entries associated with a specific file and user.

- add_file_to_collection(lines, file_name, user):
    Adds a list of text lines from a file to the collection for the given user,
    replacing any previous entries for that file.

- query_collection(user_query, user, n_results=5):
    Queries the collection for documents relevant to the query text,
    filtered by the specified user, returning up to n_results documents.

Usage:
------
Intended for integration into backend components (e.g., Flask routes) to manage
user-specific document ingestion and retrieval for augmenting language model prompts.
"""
import uuid
import chromadb

BASE_COLLECTION_NAME = "RAG_files"
chroma_client = chromadb.PersistentClient(path="chroma_db")  # persists locally


def get_or_create_collection():
    """
    Retrieve the ChromaDB collection instance.

    Args:
        user (str, optional): User identifier. Currently unused because
            the implementation uses a single shared collection.
            Can be extended to support per-user collections.

    Returns:
        chromadb.api.models.Collection: The ChromaDB collection object.
    """
    return chroma_client.get_or_create_collection(name=BASE_COLLECTION_NAME)


def delete_file_from_collection(file_name, user):
    """
    Delete all entries in the collection associated with a specific file and user.

    Args:
        file_name (str): The source filename whose entries should be deleted.
        user (str): The user identifier to scope the deletion to that user's data.
    """
    collection = get_or_create_collection()
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
    Add a list of extracted text lines to the ChromaDB collection for a user,
    replacing any previous entries for the same file and user.

    Args:
        lines (list of str): Extracted text lines from the file.
        file_name (str): The source filename of the extracted text.
        user (str): The user identifier for scoping the entries.
    """
    collection = get_or_create_collection()

    # Remove old entries for the file for this user only
    delete_file_from_collection(file_name, user)

    cleaned_lines = [line.strip() for line in lines if line.strip()]
    if not cleaned_lines:
        return

    collection.upsert(
        ids=[str(uuid.uuid4()) for _ in cleaned_lines],
        documents=cleaned_lines,
        metadatas=[{"line": i, "source_file": file_name, "user": user}
                for i in range(len(cleaned_lines))]
    )


def query_collection(user_query, user, n_results=5):
    """
    Query the collection to retrieve the most relevant documents uploaded by a user.

    Args:
        user_query (str): The text query string for relevance search.
        user (str): The user identifier to filter results to that user's documents.
        n_results (int, optional): Maximum number of documents to return. Defaults to 5.

    Returns:
        list of str: List of documents matching the query, filtered by user.
    """
    collection = get_or_create_collection()
    results = collection.query(
        query_texts=[user_query],
        n_results=n_results,
        where={"user": user}
    )
    return results["documents"]
