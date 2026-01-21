import os
import argparse
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# API Key Check
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("set GOOGLE_API_KEY environment variable")

def search_knowledge_base(query):
    print(f"\nSearching for: '{query}'...")

    # Open the existing database
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "data", "chroma_db")

    db = Chroma(
        persist_directory=db_path, 
        embedding_function=embeddings
    )


    # Similarity search
    results = db.similarity_search(query, k=3)

    # Print the results
    if not results:
        print("No matches found.")
        return

    print(f"Found {len(results)} relevant docs:\n")
    for i, doc in enumerate(results):
        print(f"Content Preview: {doc.page_content[:300]}...\n")

if __name__ == "__main__":
    # This allows you to run specific queries from the command line later
    # For now, we default to a hardcoded test question.
    test_query = "What are the recommended settings for swap memory in Vault?"
    search_knowledge_base(test_query)