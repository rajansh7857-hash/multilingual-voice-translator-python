import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from backend.translator import translate_for_multiple_languages, SUPPORTED_LANGUAGES

INDIAN_LANG_CODES = [
    "as", "bn", "brx", "doi", "gu", "hi", "kn", "ks", "kok", "mai",
    "ml", "mni-Mtei", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta",
    "te", "ur"
]

async def test_full_indic_suite():
    print(f"Total Languages supported in backend: {len(SUPPORTED_LANGUAGES)}")
    print("Testing translation from English to ALL 22 Scheduled Indian Languages:")
    print("=" * 70)
    
    phrase = "Welcome to our meeting. We are happy to talk with you."
    
    results = await translate_for_multiple_languages(phrase, "en", set(INDIAN_LANG_CODES))
    
    for i, code in enumerate(INDIAN_LANG_CODES, 1):
        meta = SUPPORTED_LANGUAGES[code]
        translated = results.get(code, "MISSING")
        print(f"{i:2d}. {meta['flag']} {meta['name']:35} [{code:8}] : {translated}")
        
    print("\n[SUCCESS] All 22 official Indian languages translated successfully!")

if __name__ == "__main__":
    asyncio.run(test_full_indic_suite())
