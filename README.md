# hashi-agent-rag

A CLI knowledge agent for HashiCorp Vault and Terraform questions. It ingests
official docs into a local vector store, then answers questions by retrieving
the relevant chunks and reasoning over them with an LLM. I built it to learn
how a retrieval loop actually behaves when you wire it up with LangGraph
instead of a single linear chain.

## What's in here

Two entry points, one shared knowledge base:

- **`src/knowledge_agent.py`** — the main one. A LangGraph agent that decides
  for itself whether to search the docs before answering, then loops back with
  what it found. Ask it a Vault/Terraform question, get an answer grounded in
  the ingested docs.
- **`src/account_planner.py`** — a simpler linear RAG chain. Feed it raw
  meeting notes and it drafts an account-strategy markdown doc, validating the
  customer's goals against the docs and flagging risks. No agent loop, just
  retrieve → prompt → generate.

Supporting scripts: `src/ingest.py` builds the vector store, `src/search.py`
dumps raw retrieval results for a query (handy for debugging what the agent
actually sees), and `src/check_models.py` lists the Gemini models your key can
reach.

## Stack

- **LangGraph** for the agent state machine, **LangChain** for loading,
  splitting, and the RAG chain.
- **ChromaDB** as a local, on-disk vector store — no external service.
- **Google Gemini**: `text-embedding-004` for embeddings, `gemini-flash-latest`
  for chat.

## Running it

You need Python 3.9+ and a Google API key with access to Gemini.

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY="your_key_here"
```

Build the knowledge base first — this scrapes a fixed list of Vault and
Terraform doc pages (see the `urls` list in `src/ingest.py`), chunks them, and
writes embeddings to `data/chroma_db/`:

```bash
python src/ingest.py
```

Then ask the agent something:

```bash
python src/knowledge_agent.py --query "How do I configure Vault for high availability on Kubernetes?"
```

It prints each node as it fires, so you can watch it decide to search, run the
retrieval, and come back with an answer.

Or draft an account plan from notes:

```bash
python src/account_planner.py --file data/enterprise_scenario.txt
# or pass text directly
python src/account_planner.py --text "Customer wants Vault on EKS with auto-unseal."
```

The plan prints to the console and also writes to `account_plan.md` in the
current directory.

## What I learned building the LangGraph loop

The agent is three pieces: a reasoning node (the LLM, with the doc-search tool
bound to it), a tool node that runs the actual ChromaDB retrieval, and a
conditional edge that checks whether the last message asked for a tool call. If
it did, go to the tool node and loop back; if not, we're done. That's the whole
graph.

The thing I actually wanted to see was the loop iterating — search, realize it's
not enough, search again. In practice, for the single-tool Vault/Terraform
questions I throw at it, the model almost always does one search and then
answers. The cyclic graph is doing real work (it's what lets the model choose
whether to retrieve at all), but calling it "self-correcting" would oversell it.
What I got was mostly about structure: separating "decide" from "retrieve" makes
the control flow explicit, versus a linear chain where retrieval is always
forced whether the question needs it or not.

One gotcha worth noting: Gemini sometimes returns message content as a list of
blocks instead of a plain string, so `run_agent` has to flatten it before
printing. That took a minute to track down.

## Rough edges

- `requirements.txt` isn't version-pinned and is missing a couple of transitive
  deps the scripts actually import (`langchain-community` for the web loader,
  `google-generativeai` for `check_models.py`). A fresh clone may need those
  installed by hand until I fix the pinning. This is next on the roadmap.
- The ingest URL list is hardcoded. If HashiCorp moves a page, ingestion just
  skips it silently.
- No citations yet — the agent answers from retrieved chunks but doesn't tell
  you which pages they came from. For a knowledge agent that's a real gap, and
  it's high on the roadmap.
- No tests or eval harness yet. I can't currently *measure* whether an answer
  is grounded or whether retrieval hit the right pages. That's the direction I
  most want to take this.

See [ROADMAP.md](ROADMAP.md) for what's planned.
