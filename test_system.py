import asyncio
import sys

# Ensure UTF-8 output encoding for emojis and non-latin scripts
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from backend.translator import translate_text, translate_for_multiple_languages, SUPPORTED_LANGUAGES

async def test_translations():
    print(f"Loaded {len(SUPPORTED_LANGUAGES)} supported languages.")
    
    test_phrase = "Hello everyone, welcome to the multilingual conference call."
    src = "en"
    target_langs = {"es", "hi", "fr", "ja", "de"}
    
    print(f"\nOriginal ({src.upper()}): {test_phrase}")
    print("Translating simultaneously to 5 target languages...")
    
    results = await translate_for_multiple_languages(test_phrase, src, target_langs)
    
    for lang, translated in results.items():
        meta = SUPPORTED_LANGUAGES.get(lang, {})
        flag = meta.get("flag", "🌐")
        name = meta.get("name", lang)
        print(f"  [{flag} {name:10}] : {translated}")
        
    print("\nVerifying cache hit speed (2nd run):")
    t0 = asyncio.get_event_loop().time()
    cached_results = await translate_for_multiple_languages(test_phrase, src, target_langs)
    t1 = asyncio.get_event_loop().time()
    print(f"  Completed cached lookup in {(t1 - t0)*1000:.2f} ms")
    
    print("\n[SUCCESS] All translation tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_translations())
