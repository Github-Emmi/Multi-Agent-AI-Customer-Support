# 14 — The "Kaggle Factory" Pattern: Step-by-Step Build Process

> **Scope:** This document is the *implementation roadmap* (the process, not the
> code) for building the AI artifacts that power the TechMart Multi-Agent
> Assistant. It expands on the pattern overview in
> [13_KAGGLE_FACTORY_PATTERN.md](13_KAGGLE_FACTORY_PATTERN.md).
>
> The Kaggle notebook you create should follow the **same structural
> conventions** as the reference notebook `shopper_spectrum.ipynb` in the repo
> root: numbered sections with banner comments, an imports/config cell, adaptive
> `/kaggle/input/` path handling, narrated markdown between code cells, and a
> final **Save Artifacts + verification** section.

---

## 0. The Pattern in One Picture

```
   ┌─────────────────────────────┐        ┌──────────────────────────────┐
   │   KAGGLE FACTORY (offline)  │        │   PRODUCTION APP (online)    │
   │   GPU · Internet · batch    │  ===>  │   CPU · stateless · fast     │
   │                             │ build  │                              │
   │  A1 · RAG index artifact    │ ─────► │  loads at startup:           │
   │  A2 · Intent router artifact│        │   • vectorstore/faiss_index/ │
   └─────────────────────────────┘        │   • backend/models/          │
                                          │       intent_classifier/     │
                                          │  LLM used ONLY for the final │
                                          │  response generation         │
                                          └──────────────────────────────┘
```

Two workloads are decoupled:

| Workload | Where | Produces |
|----------|-------|----------|
| **Heavy-lifting** (train classifier, embed the whole KB) | Kaggle (GPU) | 2 artifacts |
| **Lightweight inference** (embed 1 query, classify 1 intent) | Production (CPU) | fast responses |

---

## Prerequisites (before touching Kaggle)

1. A Kaggle account with **phone verification** (required to enable GPU + Internet).
2. The repo assets that become Kaggle Datasets:
   - `knowledge_base/` — 8 PDFs (`faq, refund_policy, shipping_policy, warranty, pricing, products, installation_guide, user_manual`)| powers the RAG index |
| `techmart-intent-data` | `banking77/train.csv`, `banking77/test.csv`, `msmarco/queries.dev.small.tsv`, `squad/dev-v2.0.json` and `squad/train-v2.0.json` (intent labels).
   - `datasets/cfpb/complaints.csv` — **⚠ 8.9 GB.** Do **not** upload as-is. Create a sampled subset first (see Step 1.3).
3. An `OPENROUTER_API_KEY` (only if you want the notebook to smoke-test final response generation; not required to build the two artifacts).

---

# PART A — Build the Artifacts in the Kaggle Factory

*Everything in Part A happens inside a single Kaggle Notebook.*

## Step 1 — Environment Setup

### 1.1 Create the notebook
- Kaggle → **Create → New Notebook** → choose **Python**.
- Rename it, e.g. `techmart-kaggle-factory`.
- (Author it locally first if you prefer — a `.ipynb` structured like
  `shopper_spectrum.ipynb` — then **File → Import Notebook** into Kaggle.)

### 1.2 Configure the session (right-hand "Settings" panel)
Notify the software developer the notbook has been successfully pushed to Kaggle.
- **Accelerator:** `GPU T4 x2` (or `P100`). Needed for fast embedding + fine-tuning. guide the software developer to do this and notify once done
- **Internet:** **On** — needed to `pip install` and to pull the base models
  (`all-MiniLM-L6-v2`, `distilbert-base-uncased`) from Hugging Face.
- **Persistence:** Variables/files off is fine; artifacts are written to
  `/kaggle/working/` which is captured on "Save Version".

### 1.3 Prepare & upload the data as Kaggle Datasets
Create **two** Kaggle Datasets (Add Data → New Dataset):

| Dataset name | Contents | Notes |
|--------------|----------|-------|
| `techmart-knowledge-base` | the 8 PDFs from `knowledge_base/` (zipped) | powers the RAG index |
| `techmart-intent-data` | `banking77/train.csv`, `banking77/test.csv`, `msmarco/queries.dev.small.tsv`, `squad/dev-v2.0.json` and `squad/train-v2.0.json` | powers the intent router |

> **CFPB sampling (do this locally before upload).** `complaints.csv` is ~8.9 GB
> — far above Kaggle's practical dataset size and unnecessary for training.
> Take a stratified sample of the columns you need only (e.g. `Product`, `Issue`,
> `Consumer complaint narrative`, and related to the porject requirements), keeping rows with a non-empty narrative, down
> to ~50k–100k rows. Save as `cfpb_sample.csv` and upload that.

After attaching both datasets, they appear under `/kaggle/input/techmart-knowledge-base/`
and `/kaggle/input/techmart-intent-data/`.

### 1.4 First cell — Imports & Configuration (mirror `shopper_spectrum.ipynb` cell 11)
Following the reference's banner-comment style, the first code cell should:
- `!pip install -q langchain langchain-community sentence-transformers faiss-gpu
  transformers datasets pypdf accelerate` (Kaggle base image already has torch).
- Import everything up front, `warnings.filterwarnings('ignore')`, set display
  options, and create the output dirs:
  `os.makedirs('/kaggle/working/faiss_index', exist_ok=True)` and
  `os.makedirs('/kaggle/working/intent_classifier', exist_ok=True)`.
- Print a "✅ environment ready" banner with library versions and `torch.cuda.is_available()`.

### 1.5 (Optional) Secrets
If smoke-testing the LLM: Add-ons → **Secrets** → add `OPENROUTER_API_KEY`, then
read it with `UserSecretsClient`. Never hard-code keys in a cell. Guide software the developer to set `OPENROUTER_API_KEY`

---

## Step 2 — Notebook Structure (the section map)

Lay the notebook out like the reference, so it reads as a narrated pipeline.
Proposed sections (each = a markdown header + one or more code cells):

```
1.  Imports & Configuration                     (Step 1.4)
2.  Load the Knowledge Base (PDFs)              (Step 3.1)
3.  Chunk the Documents                         (Step 3.2)
4.  Build Embeddings (GPU)                      (Step 3.3)
5.  Build & Save the FAISS Index  ── ARTIFACT 1 (Step 3.4–3.5)
6.  Load & Explore the Intent Data             (Step 4.1)
7.  Map Labels → 5 Agent Domains               (Step 4.2)
8.  Tokenize & Split                            (Step 4.3)
9.  Fine-Tune DistilBERT (GPU)                  (Step 4.4)
10. Evaluate the Classifier                     (Step 4.5)
11. Save the Classifier          ── ARTIFACT 2  (Step 4.6)
12. Verify & Package Both Artifacts             (Step 5)
```

Between every code cell, add a short markdown note explaining **why** the step
exists — the same discipline as the reference's "Why this chart?" annotations.

---

## Step 3 — Build ARTIFACT 1: the RAG Index

Goal: a complete FAISS vector store built from the knowledge-base PDFs, in the
**exact format the production `RAGRetriever` expects**: an `index.faiss` file and
a `metadata.pkl` list of chunk dicts.

> **Format contract (must match `backend/rag/retriever.py`).** Production reads
> `index.faiss` via `faiss.read_index` and `metadata.pkl` as a `list[dict]`
> where the *i-th* dict aligns with the *i-th* vector. Each dict must contain at
> least: `source`, `page`, `chunk_id`, `text`. It embeds queries with
> `sentence-transformers/all-MiniLM-L6-v2` and searches with `IndexFlatL2`. Your
> notebook must reproduce all of these choices exactly, or retrieval will break.

### 3.1 Load the PDFs
- Discover files adaptively: `glob('/kaggle/input/**/**/*.pdf', recursive=True)`
  (mirrors the reference's adaptive `DATA_PATH` discovery).
- Read each page's text with `pypdf.PdfReader`, skipping empty pages.

### 3.2 Chunk the documents
- Use `RecursiveCharacterTextSplitter` with **`chunk_size=500`, `chunk_overlap=50`**
  — identical to `backend/rag/pipeline.py` so dev and Factory chunks match.
- For each chunk, build the metadata dict: `{source, page, chunk_id, text}`
  where `chunk_id = f"{pdf_stem}_{page}_{i}"`.

### 3.3 Build embeddings (GPU)
- Instantiate `SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2',
  device='cuda')`.
- `model.encode(all_chunks, batch_size=64, show_progress_bar=True,
  normalize_embeddings=False)` — this is the heavy step that justifies the GPU.
- Cast to `float32` numpy.

### 3.4 Build the FAISS index
- `dim = embeddings.shape[1]` (384 for MiniLM); `index = faiss.IndexFlatL2(dim)`;
  `index.add(embeddings)`.
- Sanity-check `index.ntotal == len(all_chunks)`.

### 3.5 Save the artifact
- `faiss.write_index(index, '/kaggle/working/faiss_index/index.faiss')`.
- `pickle.dump(all_metadata, open('/kaggle/working/faiss_index/metadata.pkl','wb'))`.
- Print each file's size (reference-style ✅ report).

---

## Step 4 — Build ARTIFACT 2: the Intent Router

Goal: a fine-tuned DistilBERT text classifier that maps a customer message to one
of the **five agent domains**, saved in Hugging Face format so production loads it
with `transformers.pipeline("text-classification", ...)`.

> **Format contract (must match `backend/agents/intent_classifier.py`).**
> Production loads a directory containing `config.json`, the weights
> (`model.safetensors`), and the tokenizer files, and calls it as a
> `text-classification` pipeline. Train with an explicit label mapping so the
> model emits domain names directly:
> `id2label = {0:"billing", 1:"technical", 2:"product", 3:"complaint", 4:"faq"}`
> (and the inverse `label2id`). The loader also tolerates `LABEL_0…LABEL_4` by
> position, but naming them is cleaner.

### 4.1 Load & explore the intent data

- Load `techmart-intent-data` | `banking77/train.csv`, `banking77/test.csv`, `msmarco/queries.dev.small.tsv`, `squad/dev-v2.0.json` and `squad/train-v2.0.json` (intent labels). (columns: `text`, `label`).
- Load `cfpb_sample.csv` (columns include `Product`, `Issue`,
  `Consumer complaint narrative`).
- Inspect class balance, text length, nulls — the reference's "Know Your Data"
  discipline (shape, head, info, missing-value counts).

### 4.2 Map labels → the 5 domains (the key design step)
`techmart-intent-data` | `banking77/train.csv`, `banking77/test.csv`, `msmarco/queries.dev.small.tsv`, `squad/dev-v2.0.json` and `squad/train-v2.0.json` intent, and issue categories must be collapsed
onto `billing, technical, product, complaint, faq`. Build an explicit mapping
dictionary. A recommended starting strategy:

| Domain | Pull from the datasets like 
|--------|-----------------------------------|-----------------|
| `billing` | `*_fee_charged`, `refund_not_showing_up`, `transfer_*`, `card_payment_*`, `cash_withdrawal_charge`, `direct_debit_*` | rows where Issue ~ "Fees", "Charged", "Payment" |
| `technical` | `pin_blocked`, `card_not_working`, `declined_*`, `passcode_forgotten`, `top_up_failed`, `verify_my_identity` | Issue ~ "Trouble accessing", "Login" |
| `product` | `exchange_rate`, `card_delivery_estimate`, `apple_pay_or_google_pay`, `contactless_not_working`, `card_acceptance` | Product-descriptive rows |
| `complaint` | (Banking77 has few; rely on CFPB) | the bulk of CFPB **narratives** = real complaints |
| `faq` | `getting_started`, `country_support`, `verify_source_of_funds`, general "what/how" intents | generic informational rows |

- Apply the mapping, drop unmapped rows, and **balance** the classes
  (down/upsample) so no single domain dominates — note any caps you apply
  (don't silently truncate).
- Concatenate Banking77 + CFPB into one labeled DataFrame: `text`, `domain`.

### 4.3 Tokenize & split
- `AutoTokenizer.from_pretrained('distilbert-base-uncased')`, truncate/pad to
  `max_length=128`.
- Stratified train/validation split (e.g. 90/10) using the `datasets` library.

### 4.4 Fine-tune DistilBERT (GPU)
- `AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased',
  num_labels=5, id2label=..., label2id=...)`.
- Train with `TrainingArguments` (e.g. `epochs=3`, `batch_size=32`, `fp16=True`,
  `evaluation_strategy="epoch"`, `load_best_model_at_end=True`) and `Trainer`.
- This is the second GPU-justifying step.

### 4.5 Evaluate
- Report accuracy + macro-F1 and a per-domain confusion matrix on the validation
  set. Confirm the confidence distribution is sane for the production threshold
  (`INTENT_CONFIDENCE_THRESHOLD=0.4`). Spot-check a few example queries.

### 4.6 Save the artifact
- `trainer.save_model('/kaggle/working/intent_classifier')` and
  `tokenizer.save_pretrained('/kaggle/working/intent_classifier')`.
- Confirm the dir contains `config.json`, `model.safetensors`,
  `tokenizer.json`, `tokenizer_config.json`, `vocab.txt`, `special_tokens_map.json`.

---

## Step 5 — Verify & Export Both Artifacts

### 5.1 In-notebook sanity check (mirror `shopper_spectrum.ipynb` cell 125)
Before saving the version, prove the artifacts load and work **inside the notebook**:
- Reload the FAISS index + metadata; run 2–3 sample queries
  ("what is the refund policy?", "I can't log in") and print the top chunks'
  `source`/`text` to confirm relevance.
- Reload the classifier with `pipeline("text-classification",
  model='/kaggle/working/intent_classifier', top_k=None)`; classify the same
  sample queries and confirm the predicted domain + score.
- Print a "✅ all artifacts verified" banner.

### 5.2 Commit the notebook
- **Save Version → Save & Run All (Commit).** This executes the notebook top to
  bottom on Kaggle's servers and snapshots everything in `/kaggle/working/`.

### 5.3 Download the outputs
- Open the completed version → **Output** tab → download:
  - `faiss_index/` (`index.faiss`, `metadata.pkl`)
  - `intent_classifier/` (the full HF model directory)

---

# PART B — Integrate Artifacts into Production (already wired in this repo)

The application code already supports these artifacts; you only drop the files in
and flip a flag. (Full detail in
[13_KAGGLE_FACTORY_PATTERN.md](13_KAGGLE_FACTORY_PATTERN.md).)

1. **Place the RAG index:** replace the contents of `vectorstore/faiss_index/`
   with the downloaded `index.faiss` + `metadata.pkl`.
2. **Place the intent router:** unzip the downloaded model into
   `backend/models/intent_classifier/` (see its `README.md`).
3. **Enable local routing:** set `ROUTING_MODE=local` in `.env`
   (default is already `local`). If the artifact is absent or fails to load, the
   app logs a warning and **falls back to the LLM** automatically — so it is safe
   to deploy before the artifact exists.
4. **Confirm:** on startup you should *not* see
   `Intent classifier artifact not found …`; a chat request should route locally
   with **zero** LLM calls for intent detection.
5.  Since the `vectorstore/faiss_index/`, and `backend/models/intent_classifier/`  will be gitignore because our current code base file is large, in production it reads the `vectorstore/faiss_index/` and `backend/models/intent_classifier/` from where it is pushed on kaggle using KAGGLE_API_TOKEN on railway environment


---

## Artifact Contract Summary (the "interface" between Factory and App)

| Artifact | Built in notebook at | Deployed to | Loaded by | Must match |
|----------|----------------------|-------------|-----------|-----------|
| RAG index | `/kaggle/working/faiss_index/` | `vectorstore/faiss_index/` | `backend/rag/retriever.py` | `all-MiniLM-L6-v2`, `IndexFlatL2`, metadata keys `source/page/chunk_id/text`, chunk 500/50 |
| Intent router | `/kaggle/working/intent_classifier/` | `backend/models/intent_classifier/` | `backend/agents/intent_classifier.py` | HF `text-classification` format, `id2label` = the 5 domains |

---

## Why This Pattern (the payoff)

- **Decoupling** — DS training/data-processing (Kaggle) is separated from SWE API serving.
- **Performance** — local intent classification is a forward pass, not a network round-trip.
- **Cost** — thousands of routing LLM calls → free local inference; the LLM is reserved for final response generation (removes the 429 rate-limit problem).
- **Scalability** — the production server stays lightweight, CPU-only, and stateless; the heavy stateful artifacts are pre-built and simply loaded into memory.
