from pathlib import Path

import chromadb

BASE_DIR = Path(__file__).resolve().parents[2]
POLICY_DIR = BASE_DIR / "policies"
CHROMA_DIR = BASE_DIR / "chroma_db"

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(name="baggage_policies")

def index_policies():
    policy_files = list(POLICY_DIR.glob("*.md"))
    documents = []
    ids = []
    metadatas = []

    for policy_file in policy_files:
        document = policy_file.read_text()
        documents.append(document)

        ids.append(policy_file.stem)

        metadatas.append({"source": policy_file.name})

    collection.upsert(
        ids = ids,
        documents = documents,
        metadatas = metadatas
    )

def search_policies(query: str):
    results = collection.query(query_texts = [query], n_results = 1)

    if not results["documents"] or not results["documents"][0]:
        return None

    return {
        "text": results["documents"][0][0],
        "source": results["metadatas"][0][0]["source"]
    }