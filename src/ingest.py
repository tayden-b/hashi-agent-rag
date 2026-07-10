import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("Please set your GOOGLE_API_KEY environment variable!")

def ingest_docs():
    print("Starting Ingestion...")


    # Source URLs
    urls = [
        # --- VAULT: Core Architecture ---
        "https://developer.hashicorp.com/vault/docs/internals/architecture",
        "https://developer.hashicorp.com/vault/docs/internals/security",
        "https://developer.hashicorp.com/vault/docs/concepts/auth",
        "https://developer.hashicorp.com/vault/docs/concepts/lease",
        "https://developer.hashicorp.com/vault/docs/concepts/tokens",

        # --- VAULT: Production Hardening ---
        "https://developer.hashicorp.com/vault/docs/concepts/production-hardening",
        "https://developer.hashicorp.com/vault/tutorials/operations/production-hardening",
        "https://developer.hashicorp.com/vault/docs/configuration/telemetry",
        "https://developer.hashicorp.com/vault/docs/enterprise/replication",
        "https://developer.hashicorp.com/vault/docs/concepts/pki-global-scale",

        # --- VAULT: Common Integrations ---
        "https://developer.hashicorp.com/vault/docs/auth/kubernetes",
        "https://developer.hashicorp.com/vault/docs/auth/jwt",
        "https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2",
        "https://developer.hashicorp.com/vault/docs/secrets/database",
        "https://developer.hashicorp.com/vault/docs/secrets/aws",
        "https://developer.hashicorp.com/vault/docs/secrets/ssh",

        # --- TERRAFORM: Best Practices & Architecture ---
        "https://developer.hashicorp.com/terraform/intro/core-workflow",
        "https://developer.hashicorp.com/terraform/language/modules/develop/structure",
        "https://developer.hashicorp.com/terraform/language/state/remote",
        "https://developer.hashicorp.com/terraform/language/state/locking",
        "https://developer.hashicorp.com/terraform/language/values/variables",
        
        # --- TERRAFORM: Governance ---
        "https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement/sentinel",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings/run-tasks",
    ]
    
    # Load raw text from websites
    print(f"Loading {len(urls)} pages...")
    loader = WebBaseLoader(urls)
    raw_documents = loader.load()
    
    # Break text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(raw_documents)
    print(f"Split into {len(chunks)} text chunks.")

    # Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    # Save to ChromaDB
    print("Saving to local Vector Database...")
    # Use robust path relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "data", "chroma_db")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_path
    )
    
    print("Successfully built knowledge base.")

if __name__ == "__main__":
    ingest_docs()