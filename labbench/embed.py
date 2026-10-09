"""Retrieval quality of an embedding model against a plain lexical baseline, on the synthetic documents."""
import math
import re
import time
from collections import Counter

from . import ollama
from .workloads import load_docs, load_questions


def _tok(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25_rank(query, docs, k1=1.5, b=0.75):
    toks = {n: _tok(t) for n, t in docs.items()}
    avg = sum(map(len, toks.values())) / len(toks)
    df = Counter(w for t in toks.values() for w in set(t))
    scores = {}
    for name, t in toks.items():
        tf = Counter(t)
        scores[name] = sum(
            math.log(1 + (len(docs) - df[w] + 0.5) / (df[w] + 0.5)) * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(t) / avg))
            for w in set(_tok(query)) if w in tf)
    return sorted(scores, key=lambda n: (-scores[n], n))


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def metrics(rankings, relevant):
    """recall@1 and mean reciprocal rank over queries that have at least one relevant document."""
    hits, rr, n = 0, 0.0, 0
    for ranking, rel in zip(rankings, relevant):
        if not rel:
            continue
        n += 1
        hits += ranking[0] in rel
        rr += next((1 / (i + 1) for i, d in enumerate(ranking) if d in rel), 0.0)
    return {"queries": n, "recall_at_1": round(hits / n, 3), "mrr": round(rr / n, 3)} if n else {"queries": 0}


def evaluate(model):
    docs, questions = load_docs(), load_questions()
    names = list(docs)
    ollama.unload_all()
    start = time.perf_counter()
    doc_vecs, doc_s = ollama.embed(model, [docs[n] for n in names])
    q_vecs, q_s = ollama.embed(model, [q["question"] for q in questions])
    resident = next((m for m in ollama.loaded() if m["name"].startswith(model.split(":")[0])), {})
    emb_rank = [[n for _, n in sorted(((-cosine(qv, dv), n) for n, dv in zip(names, doc_vecs)))] for qv in q_vecs]
    bm_rank = [bm25_rank(q["question"], docs) for q in questions]
    relevant = [set(q["topic"]) for q in questions]
    return {"model": model, "dimensions": len(doc_vecs[0]), "documents": len(names), "queries": len(questions),
            "embedding": metrics(emb_rank, relevant), "bm25_baseline": metrics(bm_rank, relevant),
            "latency_s": {"documents_batch": round(doc_s, 2), "queries_batch": round(q_s, 2), "total": round(time.perf_counter() - start, 2)},
            "server_reported_gb": round(resident.get("size", 0) / 1e9, 2)}
