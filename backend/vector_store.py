# backend/vector_store.py
import math
import heapq
import pathway as pw
from pathway.stdlib.indexing import default_brute_force_knn_document_index
from .embeddings import embed_text  
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import os, json, time
from .embeddings import embed_text

DOCS_DIR = "stored_docs"
os.makedirs(DOCS_DIR, exist_ok=True)
# ------------------ MongoDB Setup ------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB", "insideX")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "news")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
news_collection = db[COLLECTION_NAME]

# ------------------ Pathway Setup ------------------
class DocSchema(pw.Schema):
    id: str
    content: str
    embedding: list[float]

class MemorySubject(pw.io.python.ConnectorSubject):
    def __init__(self):
        super().__init__()
        self.buffer = []

    def send(self, rows):
        self.buffer.extend(rows)

    def run(self):
        while self.buffer:
            yield self.buffer.pop(0)

subject = MemorySubject()

docs = pw.io.python.read(
    subject=subject,
    schema=DocSchema,
    primary_key="id",
)

index = default_brute_force_knn_document_index(
    data_column=docs.embedding,
    data_table=docs,
    dimensions=384,
    metadata_column=docs.content,
)

# Local fallback memory
_local_docs = []  

# ------------------ Helpers ------------------
def _cosine(a, b):
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))

def _local_search_vector(vector, k):
    heap = []
    for doc in _local_docs:
        score = _cosine(vector, doc["embedding"])
        heap.append((score, doc["id"], doc["content"]))
    top = heapq.nlargest(k, heap, key=lambda x: x[0])
    return [(doc_id, content, float(score)) for (score, doc_id, content) in top]

# ------------------ Public API ------------------
def add_document(stock: str, text: str, source: str = "perplexity"):
    """
    Add a document to MongoDB, Pathway, and local fallback memory.
    """
    vector = embed_text(text)

    # Save to MongoDB
    news_collection.insert_one({
        "stock": stock,
        "analysis": text,
        "embedding": vector,
        "source": source,
        "timestamp": datetime.utcnow()
    })

    # Save to Pathway
    subject.send([{"id": stock, "content": text, "embedding": vector}])

    # Save to local fallback
    _local_docs.append({"id": stock, "content": text, "embedding": vector})

    pw.run()


def search(query: str, k: int = 3):
    """
    Search Pathway index first, fallback to local cosine search if needed.
    """
    vector = embed_text(query)

    query_table = pw.debug.table_from_rows(
        schema=DocSchema,
        rows=[("q1", query, vector)],
    )

    try:
        neighbors = index.query(query_table.embedding)
        pw.run()
        results = []
        for row in neighbors.as_rows():
            try:
                doc_meta = row[1]
                distance = float(row[2])
                doc_id = None
                for d in _local_docs:
                    if d["content"] == doc_meta:
                        doc_id = d["id"]
                        break
                results.append((doc_id if doc_id else doc_meta, doc_meta, distance))
            except Exception:
                continue
        if results:
            return results[:k]
        raise RuntimeError("Pathway returned no results, falling back.")
    except NotImplementedError:
        return _local_search_vector(vector, k)
    except Exception:
        return _local_search_vector(vector, k)


def get_news(stock: str, limit: int = 20):
    """
    Fetch last N docs for a stock from MongoDB.
    """
    return list(
        news_collection.find({"stock": stock})
        .sort("_id", -1)  # latest first
        .limit(limit)
    )


def preload_from_mongo(stock: str, limit: int = 20):
    """
    Preload last N news docs from Mongo into Pathway memory.
    """
    docs = get_news(stock, limit=limit)
    for doc in docs:
        vector = embed_text(doc["analysis"])
        subject.send([{
            "id": str(doc["_id"]),
            "content": doc["analysis"],
            "embedding": vector
        }])
    pw.run()

DOCS_DIR = "stored_docs"
os.makedirs(DOCS_DIR, exist_ok=True)

def store_full_doc(stock: str, doc: dict):
    """
    Save the entire news document locally as JSON.
    Filename format: stored_docs/{stock}_{timestamp}.json
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{DOCS_DIR}/{stock}_{timestamp}.json"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print(f"📄 Saved full document: {filename}")
    except Exception as e:
        print(f"❌ Failed to save full document: {e}")

def store_full_doc(stock: str, raw_response: dict):
    """Save full Perplexity response as JSON locally."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{stock}_{timestamp}.json"
    filepath = os.path.join(DOCS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(raw_response, f, indent=2)

    print(f"📁 Saved full doc: {filepath}")
    return filepath


def preload_from_local(stock: str, limit: int = 5):
    """
    Reload last N locally saved JSON docs into Pathway memory.
    Only extracts 'analysis' text from stored JSON.
    """
    files = sorted(
        [f for f in os.listdir(DOCS_DIR) if f.startswith(stock)],
        reverse=True
    )[:limit]

    for f in files:
        path = os.path.join(DOCS_DIR, f)
        try:
            with open(path, "r", encoding="utf-8") as infile:
                raw = json.load(infile)
                analysis = raw["choices"][0]["message"]["content"]

                # embed + push into Pathway
                vector = embed_text(analysis)
                subject.send([{
                    "id": f,  # filename as ID
                    "content": analysis,
                    "embedding": vector
                }])
        except Exception as e:
            print(f"⚠️ Failed to preload {f}: {e}")

    pw.run()
    print(f"✅ Preloaded {len(files)} local docs into Pathway for {stock}")