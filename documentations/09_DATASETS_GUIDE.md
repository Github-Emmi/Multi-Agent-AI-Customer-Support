# 09 — Public Datasets Guide

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Purpose:** Train intent classifiers, seed knowledge base, and evaluate RAG retrieval

---

## Overview

| Dataset | Use Case | Size | Access |
|---------|---------|------|--------|
| CFPB Consumer Complaints | Real complaint data, fine-tune complaint + billing agents | ~4M records | Free download |
| Banking77 | Intent classification training (77 intents) | 13,083 samples | Hugging Face |
| DailyDialog | Multi-turn conversation modeling | 13,118 dialogues | GitHub |
| SQuAD 2.0 | RAG evaluation, QA pair generation | 150K QA pairs | GitHub |
| MS MARCO | Semantic retrieval training | 1M QA pairs | GitHub |

---

## A. CFPB Consumer Complaint Dataset

**Official page:** https://www.consumerfinance.gov/data-research/consumer-complaints/

### Download

```bash
mkdir -p datasets/cfpb
# Direct CSV download (~600MB)
curl -L "https://files.consumerfinance.gov/ccdb/complaints.csv.zip" \
  -o datasets/cfpb/complaints.zip
unzip datasets/cfpb/complaints.zip -d datasets/cfpb/
```

### Relevant Columns

| Column | Usage |
|--------|-------|
| `Product` | Maps to agent domain (billing, technical) |
| `Issue` | Sub-category — routing label |
| `Consumer complaint narrative` | Text input for training |
| `Company response to consumer` | Target response for training |
| `Consumer disputed?` | Escalation signal |

### Usage in Project

1. **Intent Detection training data** — map `Product` to intent labels
2. **Complaint Agent training examples** — narratives + responses
3. **Knowledge base augmentation** — extract common FAQ answers

---

## B. Banking77 Intent Classification Dataset

**Official page:** https://huggingface.co/datasets/PolyAI/banking77

### Download

```bash
pip install datasets
python -c "
from datasets import load_dataset
ds = load_dataset('PolyAI/banking77')
ds['train'].to_csv('datasets/banking77_train.csv', index=False)
ds['test'].to_csv('datasets/banking77_test.csv', index=False)
print('Banking77 downloaded.')
"
```

### Structure

| Column | Description |
|--------|-------------|
| `text` | Customer utterance |
| `label` | Intent ID (0-76) |
| `label_name` | Intent string (e.g., "card_payment_fee_charged") |

### Usage in Project

Map Banking77 intent labels to our 6 domains:

```python
BANKING77_TO_DOMAIN = {
    "card_payment_fee_charged": "billing",
    "card_payment_wrong_exchange_rate": "billing",
    "direct_debit_payment_not_recognised": "billing",
    "refund_not_showing_up": "billing",
    "lost_or_stolen_card": "technical",
    "cancel_transfer": "billing",
    # ... map all 77 intents
}
```

**Use:** Evaluate and fine-tune Intent Detection Agent accuracy.

---

## C. DailyDialog Dataset

**Official page:** https://github.com/liuzeming01/XDailyDialog

### Download

```bash
mkdir -p datasets/dailydialog
git clone https://github.com/liuzeming01/XDailyDialog datasets/dailydialog
```

### Structure

Multi-turn conversations in `.txt` format, one dialogue per line, turns separated by `__eou__`.

### Usage in Project

- **Conversation Memory testing** — validate that history is correctly maintained
- **Typing pattern modeling** — understand natural conversation flow
- Use as negative examples in intent detection (non-support queries)

---

## D. SQuAD 2.0 Dataset

**Official page:** https://github.com/rajpurkar/SQuAD-explorer

### Download

```bash
mkdir -p datasets/squad
curl -L "https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v2.0.json" \
  -o datasets/squad/train-v2.0.json
curl -L "https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json" \
  -o datasets/squad/dev-v2.0.json
```

### Usage in Project

**RAG Evaluation:** Generate synthetic QA pairs from knowledge base, then measure:

- **Retrieval precision** — does the top-k result contain the answer?
- **Answer faithfulness** — does the LLM answer match the ground truth?

```python
# Example: evaluate retrieval
from backend.rag.retriever import retriever

question = "What is TechMart's refund policy?"
results = retriever.search(question, top_k=4)
# Manually verify: does at least 1 result come from refund_policy.pdf?
```

---

## E. MS MARCO Dataset

**Official page:** https://github.com/microsoft/MSMARCO-Question-Answering

### Download (small subset)

```bash
mkdir -p datasets/msmarco
# Dev set (~30MB)
curl -L "https://msmarco.blob.core.windows.net/msmarcoranking/queries.dev.small.tsv" \
  -o datasets/msmarco/queries.dev.small.tsv
```

### Usage in Project

**Semantic retrieval benchmarking** — test that FAISS returns relevant chunks at scale. Use MS MARCO queries to stress-test retrieval quality before production deployment.

---

## Datasets Folder Structure After Download

```
datasets/
├── cfpb/
│   └── complaints.csv
├── banking77_train.csv
├── banking77_test.csv
├── dailydialog/
│   └── (cloned repo)
├── squad/
│   ├── train-v2.0.json
│   └── dev-v2.0.json
└── msmarco/
    └── queries.dev.small.tsv
```

---

## Dataset Usage Matrix

| Phase | Dataset | How Used |
|-------|---------|---------|
| Phase 3 (Agents) | Banking77 | Evaluate intent detection accuracy |
| Phase 3 (Agents) | CFPB | Sample training examples per domain |
| Phase 4 (RAG) | SQuAD | Measure retrieval precision |
| Phase 4 (RAG) | MS MARCO | Stress test FAISS at scale |
| Phase 5 (LLM) | DailyDialog | Validate conversation history handling |
| Phase 9 (Testing) | All | Regression test suite |
