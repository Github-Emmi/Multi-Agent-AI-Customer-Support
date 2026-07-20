"""
TechMart backend package.

Runtime guards set here run before ANY backend submodule (and therefore before
torch / faiss are imported), which is the only point at which they take effect.

On macOS, FAISS and PyTorch each ship their own OpenMP runtime (libomp). When
both load, and torch inference runs inside a worker thread (LangGraph executes
sync agent nodes in a thread pool), the duplicate runtimes cause a hard
segfault (SIGSEGV / exit 139) mid-request. Pinning to a single OpenMP thread and
allowing the duplicate runtime to coexist is the standard, safe mitigation.
These are set via setdefault so an explicit environment value always wins.
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
