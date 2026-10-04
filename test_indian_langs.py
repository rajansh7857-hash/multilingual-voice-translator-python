import asyncio
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from backend.translator import translate_text, SUPPORTED_LANGUAGES

test_langs = [
    ("Assamese (অসমীয়া)", "as"),
    ("Bengali (বাংলা)", "bn"),
    ("Bodo (बड़ो)", "brx"),
    ("Dogri (डोगरी)", "doi"),
    ("Gujarati (ગુજરાતી)", "gu"),
    ("Hindi (हिन्दी)", "hi"),
    ("Kannada (ಕನ್ನಡ)", "kn"),
    ("Kashmiri (कॉशुर / کٲشُر)", "ks"),
    ("Konkani (कोंकणी)", "kok"),
    ("Maithili (मैथिली)", "mai"),
    ("Malayalam (മലയാളം)", "ml"),
    ("Manipuri / Meitei (মৈতৈলোন্)", "mni-Mtei"),
    ("Marathi (मराठी)", "mr"),
    ("Nepali (नेपाली)", "ne"),
    ("Odia (ଓଡ଼ିଆ)", "or"),
    ("Punjabi (ਪੰਜਾਬੀ)", "pa"),
    ("Sanskrit (संस्कृतम्)", "sa"),
    ("Santali (ᱥᱟᱱᱛᱟᱲᱤ)", "sat"),
    ("Sindhi (सिन्धी)", "sd"),
    ("Tamil (தமிழ்)", "ta"),
    ("Telugu (తెలుగు)", "te"),
    ("Urdu (اردو)", "ur")
]

async def run_test():
    print("Testing translations for all 22 official Indian languages:")
    print("=" * 60)
    for name, code in test_langs:
        try:
            txt = await translate_text("Welcome my friend", "en", code)
            print(f"✓ {name:30} [{code:8}]: {txt}")
        except Exception as e:
            print(f"✗ {name:30} [{code:8}]: ERROR {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
