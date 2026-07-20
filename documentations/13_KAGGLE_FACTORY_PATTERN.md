# 13 — The "Kaggle Factory" Pattern for Hybrid AI Systems

This document records the architectural pattern used to build, deploy, and
maintain the AI models at the core of the TechMart Multi-Agent Assistant, and
the concrete code changes that implement it.

## 1. The Problem

The application has two very different workloads:

| Workload | Where | Examples | Requirement |
|----------|-------|----------|-------------|
| **Heavy-lifting** | Offline | Training the intent classifier; embedding the whole knowledge base | GPU, batchy, slow, one-off |
| **Lightweight inference** | Online | Classifying one query; retrieving a few chunks | Fast, cheap, low-latency |

Using a general-purpose LLM for *every* task (including intent detection) is
slow and expensive, and on the free OpenRouter tier it triggers `429 Too Many
Requests`. Running the embedding/training on the live server blocks the event
loop and, on Apple Silicon, segfaults during MPS cleanup on shutdown.

## 2. The Pattern

Decouple the two workloads:

```
   ┌─────────────────────────────┐        ┌──────────────────────────────┐
   │   KAGGLE FACTORY (offline)  │        │   PRODUCTION APP (online)    │
   │   GPU, internet, batch      │  ==>   │   CPU, stateless, fast       │
   │                             │ build  │                              │
   │  • fine-tune intent router  │ ─────► │  loads artifacts at startup: │
   │  • embed KB → FAISS index   │        │   • intent classifier        │
   └─────────────────────────────┘        │   • FAISS index              │
                                          │  LLM used ONLY for final     │
                                          │  response generation         │
                                          └──────────────────────────────┘
```

The Factory produces two **artifacts**; production loads them and only calls the
LLM for the final, high-value response.

## 3. Part A — Build the Artifacts in Kaggle

Performed in a single Kaggle Notebook (GPU + Internet enabled).

1. **Setup** — upload `knowledge_base/` and `datasets/` as Kaggle Datasets;
   `!pip install langchain langgraph sentence-transformers faiss-gpu
   transformers`; add `OPENROUTER_API_KEY` to Kaggle Secrets.
2. **RAG index artifact** — load KB PDFs → `RecursiveCharacterTextSplitter`
   (chunk 500 / overlap 50, matching `backend/rag/pipeline.py`) →
   `sentence-transformers/all-MiniLM-L6-v2` embeddings on GPU → build FAISS
   index → save `index.faiss` + `metadata.pkl`.
3. **Intent router artifact** — load Banking77 + CFPB, map their labels to the
   five domains (`billing, technical, product, complaint, faq`), fine-tune
   `distilbert-base-uncased`, `trainer.save_model(".../intent-classifier-model")`.
   Set `id2label` to `{0:billing,1:technical,2:product,3:complaint,4:faq}`.
4. **Export** — Save Version, download both output directories.

## 4. Part B — Integrate into Production (implemented in this repo)

### Place the artifacts
- Intent router → `backend/models/intent_classifier/` (see its `README.md`).
- FAISS index → replace `vectorstore/faiss_index/` (`index.faiss`, `metadata.pkl`).

### Code changes
| File | Change |
|------|--------|
| `backend/config.py` | Added `ROUTING_MODE`, `INTENT_MODEL_PATH`, `INTENT_CONFIDENCE_THRESHOLD`, `EMBEDDING_DEVICE`, `ENABLE_INGESTION`. |
| `backend/agents/intent_classifier.py` | **New.** Loads the DistilBERT artifact, normalizes labels, classifies with a confidence threshold, plus a keyword frustration heuristic. Falls back to `None` (→ LLM) if the artifact is missing. |
| `backend/agents/router.py` | `detect_intent` now uses the local classifier when `ROUTING_MODE=local` and the artifact is loaded; otherwise falls back to the original LLM path. Local mode makes **zero** LLM calls for routing. |
| `backend/embeddings/encoder.py` | `show_progress_bar` off by default (was the "Batches: 0%" hang); device pinned to CPU; added async `aencode_query` that offloads to a thread-pool executor. |
| `backend/rag/pipeline.py` | Refuses to run in production unless `ENABLE_INGESTION=true`; always persists the index; explicit `gc`/`del` teardown to avoid the MPS segfault. |

### Fallback mechanism
`ROUTING_MODE=local` is safe to ship even before the artifact exists: if
`backend/models/intent_classifier/` is empty or the model fails to load, the app
logs a warning and uses the LLM-based `detect_intent` automatically.

## 5. Benefits

- **Decoupling** — DS training/data-processing (Kaggle) is separated from SWE
  API serving.
- **Performance** — local classification is a forward pass, not a network
  round-trip.
- **Cost** — thousands of routing LLM calls → free local inference; the LLM is
  reserved for final response generation.
- **Scalability** — the production server stays lightweight and stateless; heavy
  stateful artifacts are pre-built and simply loaded into memory.
