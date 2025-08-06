import chromadb
chroma_client = chromadb.PersistentClient()

# switch `create_collection` to `get_or_create_collection` to avoid creating a new collection every time
collection = chroma_client.get_or_create_collection(name="my_collection")

# switch `add` to `upsert` to avoid adding the same documents every time
collection.upsert(
    documents=[
        "This is a document about oranges",
        "This is a document about pineapple"
    ],
    ids=["id1", "id2"]
)

results = collection.query(
    query_texts=["what about pineapple"], # Chroma will embed this for you
    n_results=1 # how many results to return
)

print(results["documents"]) # prints the documents that match the query
