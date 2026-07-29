import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Load environment variables
load_dotenv()

def create_collection():
    api_key = os.getenv("QDRANT_API_KEY")
    endpoint = os.getenv("QDRANT_CLUSTER_ENDPOINT")
    collection_name = "department_knowledge"

    if not api_key or not endpoint:
        print("Error: QDRANT_API_KEY or QDRANT_CLUSTER_ENDPOINT not configured in .env file.")
        return

    print(f"Connecting to Qdrant cluster at endpoint: {endpoint}...")
    client = QdrantClient(url=endpoint, api_key=api_key)

    try:
        # Check if collection already exists
        collections = client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)

        if exists:
            print(f"Collection '{collection_name}' already exists. Recreating...")
            client.delete_collection(collection_name=collection_name)

        print(f"Creating collection '{collection_name}'...")
        # We configure 768 dimensions for gemini's text-embedding-004 with Cosine distance
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        print(f"Collection '{collection_name}' created successfully in Qdrant!")

    except Exception as e:
        print(f"Error interacting with Qdrant: {e}")

if __name__ == "__main__":
    create_collection()
