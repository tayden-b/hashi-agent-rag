import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import sys
import argparse
from dotenv import load_dotenv

# Environment Check
load_dotenv()
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("Please set your GOOGLE_API_KEY environment variable!")

def generate_account_plan(raw_notes):
    print("Architect Agent Initialized...")
    
    # Initialize Gemini Model
    # temperature=0 means "be precise, don't hallucinate."
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

    # Initialize Vector DB
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "data", "chroma_db")
    
    db = Chroma(persist_directory=db_path, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 5}) # Get top 5 facts

    # Define Prompt Template
    # We use {context} for the Docs and {input} for your Notes.
    template = """
    You are a Senior Solutions Engineer at HashiCorp. 
    Your goal is to take raw meeting notes and write a professional "Account Strategy" document for Obsidian.
    
    Use the following Technical Documentation to validate the customer's goals and identify risks.
    If the customer tries to do something against the docs (like enabling swap), warn them in a "Risks" section.

    TECHNICAL DOCUMENTATION:
    {context}

    CUSTOMER MEETING NOTES:
    {question}

    OUTPUT FORMAT (Markdown):
    # Account Strategy: [Company Name]
    **Date:** [Today's Date]
    **Status:** [[Discovery]]
    
    ## 1. Executive Summary
    (Brief summary of what they want to achieve)

    ## 2. Technical Architecture
    (Propose the solution based on the docs. Mention specific Auth methods or Storage backends.)

    ## 3. Risks & Validation
    (Crucial: Cite specific HashiCorp rules found in the context that might block them. e.g. "Docs recommend disabling swap...")

    ## 4. Next Steps
    (Bulleted list)
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    # Define RAG Chain
    # Combine retriever, prompt, and LLM
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("Analyzing notes against HashiCorp Knowledge Base...")
    result = rag_chain.invoke(raw_notes)
    
    print("\n" + "="*40)
    print("GENERATED OBSIDIAN NOTE")
    print("="*40 + "\n")
    print(result)
    
    # Optional: Save to a real file
    # Save to data/outputs if possible, or just current dir
    output_path = "account_plan.md" 
    with open(output_path, "w") as f:
        f.write(result)
    print(f"\nSaved to '{output_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a HashiCorp Account Plan from notes.")
    
    # Allow user to pass a file path OR raw text
    parser.add_argument("--file", type=str, help="Path to a text file containing notes")
    parser.add_argument("--text", type=str, help="Raw text string of notes")
    
    args = parser.parse_args()

    if args.file:
        print(f"Reading notes from {args.file}...")
        try:
            with open(args.file, "r") as f:
                notes = f.read()
            generate_account_plan(notes)
        except FileNotFoundError:
            print("Error: File not found!")
    
    elif args.text:
        generate_account_plan(args.text)
        
    else:
        # Fallback if no arguments provided
        print("Please provide input! Usage examples:")
        print('   python src/account_planner.py --text "Client wants to use Vault..."')
        print('   python src/account_planner.py --file data/enterprise_scenario.txt')