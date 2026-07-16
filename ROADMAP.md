# Roadmap

Where this project is headed and what to pick up next. Work the top unchecked
item first. When something ships, check it off and move it to Done with the date.
Keep items small enough to land as one focused PR.

## Goal

Make this a docs-Q&A agent whose answers can be trusted and *measured*: every
answer cites the exact doc pages it drew from, and an eval harness scores
retrieval and answer quality against a golden question set. Scope stays
distinct from sales-agent-rag — this repo is the documentation knowledge
agent; that one is call-transcript intelligence.

## Next up

- [ ] Eval harness: a golden set of ~15 Vault/Terraform questions with
      expected source pages, a script that scores retrieval hit-rate and
      uses an LLM judge for answer quality, results printed as a table.
      This is the highest-leverage item in the repo.
- [ ] Tests for `ingest.py` chunking (sizes, overlap, metadata) on a fixture
      doc — no network, no API key.
- [ ] CI: lint + tests on push.

## Later

- [ ] Retrieval quality pass measured by the eval set: try a reranking step
      or hybrid (keyword + vector) search, keep it only if the numbers improve.
- [ ] Multi-turn memory so follow-up questions keep context.
- [ ] Make the doc source list configurable instead of hardcoded pages.

## Done

- [x] Citations: the search tool now tags each retrieved chunk with its source
      and returns the source list as the tool artifact. The agent cites inline,
      and `run_agent` prints a deduped "Sources" footer built from what was
      actually retrieved (so it's reliable even if the model forgets to cite).
      Source formatting lives in `src/citations.py` and is covered by
      `tests/test_citations.py` — no network or API key needed. (2026-07-13)
- [x] Add `.env.example` and pin versions in `requirements.txt` so a fresh
      clone actually installs and runs. Also load `.env` automatically and add
      the two deps the scripts imported but weren't listed. (2026-07-10)
- [x] Rewrite the README in first person: what it does, how to run it, what
      I learned building the LangGraph loop, honest rough edges. (2026-07-07)
