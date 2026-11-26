import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://lexicon:lexicon@localhost:17802/lexicon")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    token_key: str = os.getenv("JWT_SECRET", "local-floatbridge-lexicon-key-change-before-exposure")
    demo_password: str = os.getenv("DEMO_PASSWORD", "StageDesk2026!")
    seed_demo: bool = os.getenv("SEED_DEMO", "true").lower() == "true"


settings = Settings()
