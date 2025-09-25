from backend.vector_store import add_document, search

# Add some documents
add_document("1", "Apple is acquiring a startup in AI.")
add_document("2", "Tesla stock surged after earnings.")
add_document("3", "Microsoft announced new cloud features.")

print("Query: AI acquisition")
print(search("AI acquisition", k=3))
