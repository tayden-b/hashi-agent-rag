import os
import argparse
from typing import Annotated, Literal, TypedDict

# LangChain / LangGraph Imports
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

from citations import format_docs_with_sources, render_sources

# Environment Validation
load_dotenv()
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("Set GOOGLE_API_KEY environment variable!")

# --- Tools ---
# Search tool for the knowledge base

@tool(response_format="content_and_artifact")
def search_hashicorp_docs(query: str):
    """
    Call this tool to look up technical details about Vault, Terraform, or HashiCorp architecture.
    Use this when you need to validate specific configurations, security risks, or best practices.
    """
    print(f"Agent is searching Knowledge Base for: '{query}'...")

    # Connect to your existing DB
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "data", "chroma_db")

    db = Chroma(persist_directory=db_path, embedding_function=embeddings)

    # Get top 3 results
    results = db.similarity_search(query, k=3)

    # Each chunk is tagged with its source so the model can cite inline; the
    # source list rides along as the tool artifact for a deterministic footer.
    context, sources = format_docs_with_sources(results)
    return context, sources

# --- Agent Definition ---

# Define Agent State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Tell the model to ground every claim in retrieved docs and cite the source
# tags it sees in the tool output.
SYSTEM_PROMPT = (
    "You are a HashiCorp docs assistant. Answer only from the documentation "
    "returned by the search tool. Each retrieved chunk is prefixed with a "
    "[Source: ...] tag; when you use a chunk, cite its source inline. If the "
    "docs don't cover the question, say so rather than guessing. A full list of "
    "sources is appended to your answer automatically."
)

# Initialize Model
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

# Bind tools to model
tools = [search_hashicorp_docs]
llm_with_tools = llm.bind_tools(tools)

# Define the "Reasoning Node"
def chatbot(state: AgentState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# --- Graph Construction ---

# Initialize the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", chatbot)
workflow.add_node("tools", ToolNode(tools))

# Add edges
workflow.add_edge(START, "agent")

# Conditional Edge
# Check if the agent requested a tool call
def should_continue(state: AgentState) -> Literal["tools", END]:
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM output contains a tool call, transition to tools
    if last_message.tool_calls:
        return "tools"
    return END

workflow.add_conditional_edges("agent", should_continue)

# Always go back to agent from tools
workflow.add_edge("tools", "agent")

# Compile the graph
app = workflow.compile()

# --- PART 4: EXECUTION ---

def run_agent(user_input):
    print("Agent (LangGraph) Initialized...")
    print(f"User Goal: {user_input[:50]}...")
    
    # Define the inputs
    inputs = {"messages": [("system", SYSTEM_PROMPT), ("user", user_input)]}

    final_response = None
    sources = []
    seen_sources = set()

    # Stream the events
    # The 'stream' yields dictionaries like {'agent': {...}} or {'tools': {...}}
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Node '{key}' finished.")

            # Capture the latest message from the 'agent' node
            if key == "agent":
                content = value['messages'][-1].content
                # Fix: If content is a list (JSON), extract just the text
                if isinstance(content, list):
                    final_response = " ".join([block['text'] for block in content if 'text' in block])
                else:
                    final_response = content

            # Collect the sources the search tool actually returned (its artifact),
            # deduped across every retrieval in this run.
            if key == "tools":
                for msg in value['messages']:
                    for label, url in getattr(msg, "artifact", None) or []:
                        if url not in seen_sources:
                            seen_sources.add(url)
                            sources.append((label, url))

    # Print the final result found in the loop
    print("\n" + "="*40)
    print("FINAL ANSWER:")
    print("="*40)
    print(final_response)

    footer = render_sources(sources)
    if footer:
        print("\n" + footer)

    # Return the answer and the sources actually retrieved so callers (the eval
    # harness) can score the real pipeline instead of re-implementing it.
    return final_response, sources

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="How do I configure Vault for EKS with high security?")
    args = parser.parse_args()
    
    run_agent(args.query)