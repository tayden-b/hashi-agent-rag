"""Score the agent against a golden question set.

Two numbers per question:
  - retrieval hit: did top-k retrieval surface an expected source page?
  - answer quality: an LLM judge's 1-5 grade of the agent's answer.

Needs GOOGLE_API_KEY and a built vector DB (run `python src/ingest.py` first).
The scoring math lives in eval/scoring.py and is unit tested without any key.

    python eval/run_eval.py            # full golden set
    python eval/run_eval.py --limit 3  # quick smoke over the first 3
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from knowledge_agent import run_agent  # noqa: E402
from scoring import (  # noqa: E402
    format_table,
    hit_rate,
    mean,
    parse_judge_score,
    retrieval_hit,
)

load_dotenv()

JUDGE_PROMPT = (
    "You are grading a HashiCorp documentation assistant. Given the user's "
    "question and the assistant's answer, rate the answer's quality from 1 "
    "(wrong or unhelpful) to 5 (accurate, grounded, and complete). Reply with "
    "just the number.\n\nQuestion: {question}\n\nAnswer: {answer}\n\nScore:"
)


def retrieved_sources(db, question, k):
    """Source URLs of the top-k retrieved chunks for one question."""
    docs = db.similarity_search(question, k=k)
    return [(d.metadata or {}).get("source", "") for d in docs]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--k", type=int, default=3, help="retrieval depth to score")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_API_KEY"):
        raise SystemExit("Set GOOGLE_API_KEY (and run src/ingest.py) before evaluating.")

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "golden_set.json")) as f:
        golden = json.load(f)
    if args.limit:
        golden = golden[: args.limit]

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    db_path = os.path.join(here, "..", "data", "chroma_db")
    db = Chroma(persist_directory=db_path, embedding_function=embeddings)
    judge = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

    rows, hits, scores = [], [], []
    for i, item in enumerate(golden, 1):
        q = item["question"]
        hit = retrieval_hit(retrieved_sources(db, q, args.k), item["sources"])
        answer, _ = run_agent(q)
        graded = judge.invoke(JUDGE_PROMPT.format(question=q, answer=answer or ""))
        score = parse_judge_score(getattr(graded, "content", str(graded)))
        hits.append(hit)
        scores.append(score)
        rows.append((i, q[:48], "yes" if hit else "no", "-" if score is None else score))

    print("\n" + format_table(rows, ["#", "question", "retr", "quality"]))
    avg = mean(scores)
    print(f"\nretrieval hit-rate @ k={args.k}: {hit_rate(hits):.0%}  ({sum(hits)}/{len(hits)})")
    print(f"mean answer quality: {'n/a' if avg is None else f'{avg:.2f} / 5'}")


if __name__ == "__main__":
    main()
