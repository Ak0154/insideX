import pathway as pw
from . import vector_store

def run_query(query: str, k: int = 3):
    """Run Pathway pipeline end-to-end and return search results."""
    # Define the query computation
    results = vector_store.search(query, k)

    # Execute pipeline
    pw.run()

    # Collect results into Python list
    return [(r[0], r[1]) for r in results]  # (id, content)
