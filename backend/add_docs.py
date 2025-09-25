from backend.vector_store import add_document

# Add some docs about Tata Motors
add_document("tata1", "Tata Motors shares rose 5% after announcing new EV models.")
add_document("tata2", "Tata Motors signed a joint venture with a foreign automaker to expand production.")
add_document("tata3", "Analysts warn Tata Motors may face margin pressure due to rising input costs.")

print("✅ Docs about Tata Motors added to Pathway.")
