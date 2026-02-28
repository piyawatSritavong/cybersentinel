import chromadb
import hashlib
import os
from pathlib import Path
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from .config import settings

client = None
collection = None


class LightweightEmbedding(EmbeddingFunction):
    """Hash-based embedding that avoids loading sentence-transformers models."""

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for doc in input:
            h = hashlib.sha256(doc.encode()).digest()
            vec = [float(b) / 255.0 for b in h[:64]]
            norm = sum(v * v for v in vec) ** 0.5
            if norm > 0:
                vec = [v / norm for v in vec]
            embeddings.append(vec)
        return embeddings


_embedding_fn = LightweightEmbedding()


def init_chromadb():
    global client, collection

    persist_path = Path(
        __file__).parent.parent.parent / settings.vector_db_path
    os.makedirs(persist_path, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_path))

    try:
        collection = client.get_or_create_collection(
            name="playbooks",
            metadata={"hnsw:space": "cosine"},
            embedding_function=_embedding_fn
        )
    except Exception as e:
        print(f"Error initializing collection: {e}")
        return None

    if collection.count() == 0:
        playbooks_path = Path(
            __file__).parent.parent.parent / "data" / "playbooks"

        if playbooks_path.exists():
            print(f"Indexing playbooks from {playbooks_path}...")
            for md_file in playbooks_path.glob("*.md"):
                with open(md_file, "r") as f:
                    content = f.read()
                    try:
                        collection.add(documents=[content],
                                       metadatas=[{
                                           "filename": md_file.name,
                                           "type": "official_playbook"
                                       }],
                                       ids=[md_file.stem])
                    except Exception as e:
                        print(f"Skip {md_file.name}: {e}")

    return collection


def query_playbooks(query_text: str, n_results: int = 3):
    global collection
    if collection is None:
        init_chromadb()

    try:
        results = collection.query(query_texts=[query_text],
                                   n_results=n_results)
        return results
    except Exception as e:
        print(f"Error querying playbooks: {e}")
        return {"documents": [[]]}
