import requests, bs4, html, sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Let's test the 22 languages and find the exact working Google Translate language codes
test_langs = [
    ("Assamese (অসমীয়া)", ["as"]),
    ("Bengali (বাংলা)", ["bn"]),
    ("Bodo (बड़ो)", ["brx", "bho", "as"]),
    ("Dogri (डोगरी)", ["doi"]),
    ("Gujarati (ગુજરાતી)", ["gu"]),
    ("Hindi (हिन्दी)", ["hi"]),
    ("Kannada (ಕನ್ನಡ)", ["kn"]),
    ("Kashmiri (कॉशुर / کٲشُر)", ["ks", "ur"]),
    ("Konkani (कोंकणी)", ["gom", "kok"]),
    ("Maithili (मैथिली)", ["mai"]),
    ("Malayalam (മലയാളം)", ["ml"]),
    ("Manipuri / Meitei (মৈতৈলোন্)", ["mni-Mtei", "mni"]),
    ("Marathi (मराठी)", ["mr"]),
    ("Nepali (नेपाली)", ["ne"]),
    ("Odia (ଓଡ଼ିଆ)", ["or"]),
    ("Punjabi (ਪੰਜਾਬੀ)", ["pa"]),
    ("Sanskrit (संस्कृतम्)", ["sa"]),
    ("Santali (ᱥᱟᱱᱛᱟᱲᱤ)", ["sat"]),
    ("Sindhi (सिन्धी)", ["sd"]),
    ("Tamil (தமிழ்)", ["ta"]),
    ("Telugu (తెలుగు)", ["te"]),
    ("Urdu (اردو)", ["ur"])
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
})

print("Testing translations for all 22 official Indian languages:")
print("=" * 60)

for name, codes in test_langs:
    success = False
    for code in codes:
        try:
            r = session.get("https://translate.google.com/m", params={"sl": "en", "tl": code, "q": "Welcome my friend"}, timeout=5)
            if r.status_code == 200:
                soup = bs4.BeautifulSoup(r.text, "html.parser")
                res = soup.find("div", {"class": "result-container"})
                if res and res.get_text(strip=True):
                    txt = html.unescape(res.get_text(strip=True))
                    print(f"✓ {name:30} [{code:8}]: {txt}")
                    success = True
                    break
        except Exception as e:
            pass
    if not success:
        print(f"✗ {name:30} FAILED for codes: {codes}")
