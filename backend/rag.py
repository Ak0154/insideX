# backend/rag.py
from .vector_store import search
from .llm import analyze_with_claude

def get_context(query: str, k: int = 3):
    """Retrieve relevant context for a query using Pathway."""
    results = search(query, k=k)
    context = "\n".join([f"- {doc} (score: {score:.2f})" for _, doc, score in results])
    return context

def answer_query(query: str):
    """RAG pipeline: retrieve with Pathway, answer with Claude."""
    context = get_context(query)
    if not context:
        return "No relevant documents found in InsiderX knowledge base."

    # Prompt Claude with context + query
    prompt = f"""
You are InsiderX, a stock anomaly detection assistant.

Context documents:
{context}

User query: {query}

Task:
- ONLY highlight if there are anomalies, suspicious behavior, or risks.
- Be concise, 3-4 bullet points max.
- Always attach sources/links from the context if present.
- If nothing unusual, say "No anomalies detected."
"""
    return analyze_with_claude(prompt)
