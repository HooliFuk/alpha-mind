# tests/test_llm_router.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.llm_router import get_llm, get_llm_with_fallback, test_llm_connection
from config.settings import settings


def test_router():
    print("=" * 60)
    print("     LLM ROUTER TEST")
    print("=" * 60)

    print(f"\nActive Provider : {settings.AI_PROVIDER}")
    print(f"Active Model    : {settings.AI_MODEL}\n")

    # Test 1: Connection test for all providers
    print("Testing all provider connections...")
    results = test_llm_connection()
    for provider, status in results.items():
        print(f"   {provider:12} → {status}")

    # Test 2: Load active provider
    print(f"\nLoading active provider ({settings.AI_PROVIDER})...")
    try:
        llm = get_llm()
        response = llm.invoke("You are a trading assistant. Say READY in one word.")
        print(f"   ✅ Response: {response.content}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 3: Fallback test
    print(f"\nTesting fallback system...")
    try:
        llm = get_llm_with_fallback()
        response = llm.invoke("Say FALLBACK_OK in one word.")
        print(f"   ✅ Fallback works: {response.content}")
    except Exception as e:
        print(f"   ❌ Fallback failed: {e}")

    print("\n" + "=" * 60)
    print("LLM ROUTER TEST COMPLETE")
    print("=" * 60)
    print("\nTo switch AI provider:")
    print("   1. Open .env file")
    print("   2. Change AI_PROVIDER=openai to AI_PROVIDER=anthropic")
    print("   3. Change AI_MODEL to the model you want")
    print("   4. Save file and restart bot")
    print("   5. Zero code changes needed anywhere else")


if __name__ == "__main__":
    test_router()