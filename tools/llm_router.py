# tools/llm_router.py
# ══════════════════════════════════════════════════════════
# THIS IS THE CORE OF THE PROVIDER-AGNOSTIC ARCHITECTURE
# Every agent uses this file to talk to AI
# To switch AI provider: change .env file only
# No other file needs to change
# ══════════════════════════════════════════════════════════
from config.settings import settings
from monitoring.logger import get_logger

logger = get_logger(__name__)


def get_llm(
    provider: str = None,
    model: str = None,
    temperature: float = 0.1
):
    """
    Returns the correct LLM client based on provider setting.

    Usage in any agent:
        from tools.llm_router import get_llm
        llm = get_llm()
        response = llm.invoke("Your prompt here")

    To use a specific provider temporarily:
        llm = get_llm(provider="anthropic", model="claude-3-5-sonnet-20241022")
    """
    # Use env settings if not specified
    active_provider = provider or settings.AI_PROVIDER
    active_model = model or settings.AI_MODEL

    logger.info(f"Loading LLM: {active_provider} / {active_model}")

    # ── OpenAI ────────────────────────────────────────────
    if active_provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=active_model,
                api_key=settings.OPENAI_API_KEY,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"OpenAI load failed: {e}")
            raise

    # ── Anthropic Claude ──────────────────────────────────
    elif active_provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=active_model,
                api_key=settings.ANTHROPIC_API_KEY,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Anthropic load failed: {e}")
            raise

    # ── Google Gemini ─────────────────────────────────────
    elif active_provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=active_model,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Google Gemini load failed: {e}")
            raise

    # ── Groq (Free + Fast) ────────────────────────────────
    elif active_provider == "groq":
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=active_model,
                api_key=settings.GROQ_API_KEY,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Groq load failed: {e}")
            raise

    else:
        raise ValueError(
            f"Unknown provider: '{active_provider}'. "
            f"Choose from: openai, anthropic, google, groq"
        )


def get_llm_with_fallback(temperature: float = 0.1):
    """
    Tries your primary provider first.
    If it fails, automatically falls back to the next available one.
    This prevents the bot from crashing if one API is down.

    Fallback order: Primary → OpenAI → Google → Groq
    """
    providers_to_try = [
        (settings.AI_PROVIDER, settings.AI_MODEL),
        ("openai", "gpt-4o-mini"),
        ("google", "gemini-1.5-flash"),
        ("groq", "llama3-70b-8192"),
    ]

    # Remove duplicates while keeping order
    seen = set()
    unique_providers = []
    for p, m in providers_to_try:
        if p not in seen:
            seen.add(p)
            unique_providers.append((p, m))

    for provider, model in unique_providers:
        try:
            llm = get_llm(provider=provider, model=model, temperature=temperature)
            logger.info(f"LLM loaded successfully: {provider}/{model}")
            return llm
        except Exception as e:
            logger.warning(f"Provider {provider} failed: {e}. Trying next...")
            continue

    raise RuntimeError("All AI providers failed. Check your API keys.")


def test_llm_connection() -> dict:
    """
    Quick test to verify your active AI provider works.
    Run this before starting the trading session.
    """
    results = {}
    providers = {
        "openai": ("gpt-4o-mini", settings.OPENAI_API_KEY),
        "anthropic": ("claude-3-5-sonnet-20241022", settings.ANTHROPIC_API_KEY),
        "google": ("gemini-1.5-flash", settings.GOOGLE_API_KEY),
        "groq": ("llama3-70b-8192", settings.GROQ_API_KEY),
    }

    for provider, (model, key) in providers.items():
        if not key:
            results[provider] = "❌ No API key"
            continue
        try:
            llm = get_llm(provider=provider, model=model)
            response = llm.invoke("Say OK")
            results[provider] = "✅ Connected"
        except Exception as e:
            results[provider] = f"❌ Failed: {str(e)[:50]}"

    return results