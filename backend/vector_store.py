# backend/vector_store.py
import math
import heapq
import pathway as pw
from pathway.stdlib.indexing import default_brute_force_knn_document_index
from .embeddings import embed_text

# Simple schema
class DocSchema(pw.Schema):
    id: str
    content: str
    embedding: list[float]

# Minimal ConnectorSubject implementation (already working in your env)
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

# Pathway input table
docs = pw.io.python.read(
    subject=subject,
    schema=DocSchema,
    primary_key="id",
)

# Build brute-force index (signature matches your environment)
index = default_brute_force_knn_document_index(
    data_column=docs.embedding,
    data_table=docs,
    dimensions=384,
    metadata_column=docs.content,
)

# --- Local fallback index (keeps (id, content, embedding) in memory) ---
_local_docs = []  # list of dicts: {"id":..., "content":..., "embedding":[...]} 

def _cosine(a, b):
    # a and b are lists of floats
    # handle zero vectors gracefully
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
    """Return list of (id, content, score) sorted by descending score (top k)"""
    heap = []
    for doc in _local_docs:
        score = _cosine(vector, doc["embedding"])
        # use min-heap; push negative score to get max behavior or use (score,...) and heapq.nlargest
        heap.append((score, doc["id"], doc["content"]))
    # get top k by score
    top = heapq.nlargest(k, heap, key=lambda x: x[0])
    # convert to (id, content, score)
    return [(doc_id, content, float(score)) for (score, doc_id, content) in top]

# Public API
def add_document(doc_id: str, text: str):
    """
    Add a document to Pathway AND the local fallback index.
    Calls pw.run() to materialize Pathway pipeline immediately.
    """
    vector = embed_text(text)
    # send to Pathway subject
    subject.send([{"id": doc_id, "content": text, "embedding": vector}])
    # also keep a local copy for fallback search
    _local_docs.append({"id": doc_id, "content": text, "embedding": vector})
    # run Pathway pipeline
    pw.run()


def search(query: str, k: int = 3):
    """
    Try a Pathway query first. If Pathway raises the NotImplementedError
    you saw (brute force index not supported in this variant), fall back
    to local cosine search (guaranteed).
    Returns list of tuples: (doc_id, content, score)
    """
    vector = embed_text(query)

    # Build a single-row query table
    query_table = pw.debug.table_from_rows(
        schema=DocSchema,
        rows=[("q1", query, vector)],
    )

    try:
        # Try to query the Pathway index. API differences across Pathway
        # versions mean this can raise NotImplementedError (as you observed).
        # We call index.query(query_column) — your environment expects that.
        neighbors = index.query(query_table.embedding)
        pw.run()
        results = []
        for row in neighbors.as_rows():
            # In your environment row format for DataIndex query was (query_id, doc_content, distance)
            # but sometimes doc id is returned. We attempt to parse both shapes.
            # If row[1] is id (likely str) and row[2] numeric, we'll attempt to look up content in _local_docs.
            try:
                # If the metadata column we passed was content, row[1] is content.
                doc_meta = row[1]
                distance = float(row[2])
                # Try to find id from local store if needed:
                doc_id = None
                # If doc_meta matches some content in local docs, fetch id
                for d in _local_docs:
                    if d["content"] == doc_meta:
                        doc_id = d["id"]
                        break
                results.append((doc_id if doc_id is not None else doc_meta, doc_meta, distance))
            except Exception:
                # on unexpected shape, skip gracefully
                continue
        # If we got results, return top-k
        if results:
            return results[:k]
        # else fallthrough to local fallback
        raise RuntimeError("Pathway returned no results, falling back.")
    except NotImplementedError:
        # This is the exact error you saw with brute-force "as-of-now" support.
        # Fall back to local search.
        return _local_search_vector(vector, k)
    except Exception:
        # any other exception -> fallback as well (safer for hackathon/demo)
        return _local_search_vector(vector, k)
