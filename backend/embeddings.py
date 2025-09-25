from sentence_transformers import SentenceTransformer

# Load once globally
embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def embed_text(text: str):
    """Return dense vector for given text"""
    return embedding_model.encode(text, convert_to_numpy=True).tolist()
