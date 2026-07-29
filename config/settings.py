# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── AI Provider Control ───────────────────────────
    # Change AI_PROVIDER in .env to switch providers
    # No code changes needed anywhere else
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")

    # ── All API Keys ──────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # ── Broker ────────────────────────────────────────
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_BASE_URL: str = os.getenv(
        "ALPACA_BASE_URL",
        "https://paper-api.alpaca.markets"
    )

    # ── Market Data ───────────────────────────────────
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")

    # ── Database ──────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///alphatrader.db"
    )

    # ── Telegram ──────────────────────────────────────
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # ── Trading Rules ─────────────────────────────────
    MAX_POSITION_SIZE: float = 0.05
    MAX_DAILY_LOSS: float = 0.02
    MAX_OPEN_POSITIONS: int = 5
    PAPER_TRADING: bool = True
    MIN_CONFIDENCE: float = 0.65


settings = Settings()


def validate_settings():
    """Check which keys are present on startup"""
    print("\n── API Key Status ───────────────────────")
    print(f"  AI Provider : {settings.AI_PROVIDER}")
    print(f"  AI Model    : {settings.AI_MODEL}")
    print(f"  OpenAI Key  : {'✅ Found' if settings.OPENAI_API_KEY else '❌ Missing'}")
    print(f"  Claude Key  : {'✅ Found' if settings.ANTHROPIC_API_KEY else '❌ Missing'}")
    print(f"  Google Key  : {'✅ Found' if settings.GOOGLE_API_KEY else '❌ Missing'}")
    print(f"  Groq Key    : {'✅ Found' if settings.GROQ_API_KEY else '❌ Missing'}")
    print(f"  Alpaca Key  : {'✅ Found' if settings.ALPACA_API_KEY else '❌ Missing'}")
    print("─────────────────────────────────────────\n")

    # Check active provider has a key
    provider_keys = {
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "google": settings.GOOGLE_API_KEY,
        "groq": settings.GROQ_API_KEY,
    }

    active_key = provider_keys.get(settings.AI_PROVIDER, "")
    if not active_key:
        print(f"⚠️  WARNING: Active provider '{settings.AI_PROVIDER}' has no API key!")
        print(f"   Add {settings.AI_PROVIDER.upper()}_API_KEY to your .env file")
        return False

    print(f"✅ Active AI provider '{settings.AI_PROVIDER}' is ready")
    return True