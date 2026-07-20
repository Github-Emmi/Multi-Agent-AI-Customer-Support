from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENAI_MODEL: str = "openrouter/free"
    OPENAI_MAX_TOKENS: int = 1024
    OPENAI_TEMPERATURE: float = 0.3

    # ── Intent Routing (Kaggle Factory) ───────────────────────────────────────
    # "local" → fast, free, fine-tuned classifier (no LLM call for routing).
    # "llm"   → fall back to the original LLM-based intent detection.
    # In "local" mode the app still falls back to the LLM automatically if the
    # local classifier artifact is missing or fails to load.
    ROUTING_MODE: str = "local"  # "local" | "llm"
    INTENT_MODEL_PATH: str = "backend/models/intent_classifier"
    INTENT_CONFIDENCE_THRESHOLD: float = 0.4

    # ── Embeddings ─────────────────────────────────────────────────────────────
    # Pin to CPU: avoids the Apple-Silicon MPS shutdown segfault and keeps
    # single-query embedding fast and deterministic in production.
    EMBEDDING_DEVICE: str = "cpu"

    # ── Ingestion pipeline ─────────────────────────────────────────────────────
    # Heavy offline work belongs in the Kaggle Factory; production loads the
    # pre-built artifact instead. Set true only to force a local rebuild in prod.
    ENABLE_INGESTION: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    MONGODB_URI: str = "mongodb://localhost:27017/customer_support"

    # ── Auth ──────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-to-a-secure-random-string-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24

    # ── Vector Store ──────────────────────────────────────────────────────────
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    PINECONE_INDEX_NAME: str = "techmart-kb"
    PINECONE_HOST: str = ""

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # ── App ───────────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    ENVIRONMENT: str = "development"

    # ── File Upload ───────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "uploads/"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Webhooks ──────────────────────────────────────────────────────────────
    WHATSAPP_VERIFY_TOKEN: str = "techmart_verify_token_2026"

    # ── Vector Store selector ─────────────────────────────────────────────────
    # Set VECTOR_STORE=pinecone in .env.production for cloud deployment
    VECTOR_STORE: str = "faiss"  # "faiss" | "pinecone"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
