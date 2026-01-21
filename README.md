# hashi-agent-RAG

This project is a CLI-based knowledge agent designed to assist with HashiCorp Vault and Terraform configuration, architecture, and best practices. It leverages Retrieval-Augmented Generation (RAG) and an agentic loop to provide accurate, context-aware answers based on official documentation.

## Overview

The tool operates by ingesting technical documentation into a local vector database and using a Large Language Model (LLM) to reason about user queries. It can function as a direct RAG tool or as an autonomous agent capable of deciding when to consult its knowledge base.

### Architecture

The project is built on the following stack:

*   **LangChain:** For document loading, splitting, and chain orchestration.
*   **LangGraph:** For defining the agent's state machine (cyclic graph).
*   **ChromaDB:** As the local vector store for embeddings.
*   **Google Generative AI:** For embeddings (`text-embedding-004`) and chat completion (`gemini-flash-latest`).

### Repository Structure

```
├── data/                  # Data assets
│   ├── chroma_db/         # Local Vector Store (generated)
│   ├── enterprise_scenario.txt  # Sample customer requirements
│   └── account_plan.md    # Generated output
├── src/                   # Source Code
│   ├── knowledge_agent.py # MAIN: Advanced LangGraph Agent
│   ├── account_planner.py # SECONDARY: Simple RAG Chain
│   ├── ingest.py          # Script to build knowledge base
│   └── search.py          # Utility to debug vector search
├── requirements.txt       # Dependencies
└── README.md              # Documentation
```

## Setup

### Prerequisites
*   Python 3.9+
*   A Google Cloud API Key with access to Gemini models.

### Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set your API key:
    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```

## Usage

### 1. Build the Knowledge Base
First, ingest the documentation to populate the vector database. This script scrapes specific HashiCorp documentation pages, chunks them, and stores the embeddings locally in `data/chroma_db`.

```bash
python src/ingest.py
```

### 2. Run the Intelligent Agent (Recommended)
The **Knowledge Agent** (`src/knowledge_agent.py`) uses **LangGraph** to create a cyclical workflow. It can "think" about whether it needs to search the documentation toolkit before answering, allowing for complex reasoning.

```bash
python src/knowledge_agent.py --query "How do I configure Vault for high availability on Kubernetes?"
```

**How it Works (The Agentic Loop):**

I built this using **LangGraph** because simple linear chains usually aren't enough for complex technical questions. Instead of just taking a question and hoping the first search result is right, the agent actually follows a "reasoning loop":

1.  **The Brain (chatbot node):** The LLM looks at your query and decides if it can answer right away or if it needs to look something up in the documentation.
2.  **The Router:** If the LLM decides it needs documentation, it triggers a tool call. If not, it just gives you the final answer and stops.
3.  **The Worker (tools node):** This is where the actual RAG happens. It searches the local ChromaDB for the most relevant docs and hands that context back to the brain.
4.  **The Loop:** The agent looks at the documentation it just found and realizes, "Oh, okay, now I have the facts." It then goes back to Step 1 to formulate the final response.

It's essentially a state machine that keeps looping until it's confident it has a complete answer for you. It's way more reliable than a standard search because the agent can "self-correct" if the first search doesn't give it exactly what it needs.

### 3. Generate Account Plans (Secondary)
The **Account Planner** (`src/account_planner.py`) is a simpler, linear RAG chain designed specifically for generating customer account strategies from raw notes. It does not use the agentic loop.

```bash
# Process a file
python src/account_planner.py --file data/enterprise_scenario.txt

# Process raw text
python src/account_planner.py --text "Customer wants to deploy Vault in EKS with auto-unseal."
```
