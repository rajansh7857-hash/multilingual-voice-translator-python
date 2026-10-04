import asyncio
import logging
import html
from typing import Dict, Set, Optional
import requests
import bs4

logger = logging.getLogger(__name__)

# Complete catalog: All 22 Official Scheduled Indian Languages + 100+ Global Languages
SUPPORTED_LANGUAGES = {
    # =========================================================================
    # 🇮🇳 22 OFFICIAL SCHEDULED INDIAN LANGUAGES (Constitutional 8th Schedule)
    # =========================================================================
    "as": {"name": "Assamese (অসমীয়া)", "locale": "as-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "bn-IN"},
    "bn": {"name": "Bengali (বাংলা)", "locale": "bn-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "bn-IN"},
    "brx": {"name": "Bodo (बड़ो)", "locale": "brx-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "doi": {"name": "Dogri (डोगरी)", "locale": "doi-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "gu": {"name": "Gujarati (ગુજરાતી)", "locale": "gu-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "gu-IN"},
    "hi": {"name": "Hindi (हिन्दी)", "locale": "hi-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "kn": {"name": "Kannada (ಕನ್ನಡ)", "locale": "kn-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "kn-IN"},
    "ks": {"name": "Kashmiri (कॉशुर / کٲشُر)", "locale": "ks-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "ur-IN"},
    "kok": {"name": "Konkani (कोंकणी)", "locale": "kok-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "mai": {"name": "Maithili (मैथिली)", "locale": "mai-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "ml": {"name": "Malayalam (മലയാളം)", "locale": "ml-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "ml-IN"},
    "mni-Mtei": {"name": "Manipuri / Meitei (মৈতৈলোন্)", "locale": "mni-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "bn-IN"},
    "mr": {"name": "Marathi (मराठी)", "locale": "mr-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "mr-IN"},
    "ne": {"name": "Nepali (नेपाली)", "locale": "ne-NP", "flag": "🇳🇵", "category": "Indian Languages", "tts_fallback": "ne-NP"},
    "or": {"name": "Odia (ଓଡ଼ିଆ)", "locale": "or-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "or-IN"},
    "pa": {"name": "Punjabi (ਪੰਜਾਬੀ)", "locale": "pa-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "pa-IN"},
    "sa": {"name": "Sanskrit (संस्कृतम्)", "locale": "sa-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "sat": {"name": "Santali (ᱥᱟᱱᱛᱟᱲᱤ)", "locale": "sat-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "sd": {"name": "Sindhi (सिन्धी)", "locale": "sd-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},
    "ta": {"name": "Tamil (தமிழ்)", "locale": "ta-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "ta-IN"},
    "te": {"name": "Telugu (తెలుగు)", "locale": "te-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "te-IN"},
    "ur": {"name": "Urdu (اردو)", "locale": "ur-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "ur-IN"},

    # Other widely spoken Indian languages
    "bho": {"name": "Bhojpuri (भोजपुरी)", "locale": "bho-IN", "flag": "🇮🇳", "category": "Indian Languages", "tts_fallback": "hi-IN"},

    # =========================================================================
    # 🌍 MAJOR GLOBAL & INTERNATIONAL LANGUAGES
    # =========================================================================
    "en": {"name": "English", "locale": "en-US", "flag": "🇺🇸", "category": "Global Languages", "tts_fallback": "en-US"},
    "es": {"name": "Spanish (Español)", "locale": "es-ES", "flag": "🇪🇸", "category": "Global Languages", "tts_fallback": "es-ES"},
    "fr": {"name": "French (Français)", "locale": "fr-FR", "flag": "🇫🇷", "category": "Global Languages", "tts_fallback": "fr-FR"},
    "de": {"name": "German (Deutsch)", "locale": "de-DE", "flag": "🇩🇪", "category": "Global Languages", "tts_fallback": "de-DE"},
    "ja": {"name": "Japanese (日本語)", "locale": "ja-JP", "flag": "🇯🇵", "category": "Global Languages", "tts_fallback": "ja-JP"},
    "zh-CN": {"name": "Chinese Simplified (简体中文)", "locale": "zh-CN", "flag": "🇨🇳", "category": "Global Languages", "tts_fallback": "zh-CN"},
    "zh-TW": {"name": "Chinese Traditional (繁體中文)", "locale": "zh-TW", "flag": "🇹🇼", "category": "Global Languages", "tts_fallback": "zh-TW"},
    "ru": {"name": "Russian (Русский)", "locale": "ru-RU", "flag": "🇷🇺", "category": "Global Languages", "tts_fallback": "ru-RU"},
    "ar": {"name": "Arabic (العربية)", "locale": "ar-SA", "flag": "🇸🇦", "category": "Global Languages", "tts_fallback": "ar-SA"},
    "pt": {"name": "Portuguese (Português)", "locale": "pt-BR", "flag": "🇧🇷", "category": "Global Languages", "tts_fallback": "pt-BR"},
    "it": {"name": "Italian (Italiano)", "locale": "it-IT", "flag": "🇮🇹", "category": "Global Languages", "tts_fallback": "it-IT"},
    "ko": {"name": "Korean (한국어)", "locale": "ko-KR", "flag": "🇰🇷", "category": "Global Languages", "tts_fallback": "ko-KR"},
    "nl": {"name": "Dutch (Nederlands)", "locale": "nl-NL", "flag": "🇳🇱", "category": "Global Languages", "tts_fallback": "nl-NL"},
    "tr": {"name": "Turkish (Türkçe)", "locale": "tr-TR", "flag": "🇹🇷", "category": "Global Languages", "tts_fallback": "tr-TR"},
    "vi": {"name": "Vietnamese (Tiếng Việt)", "locale": "vi-VN", "flag": "🇻🇳", "category": "Global Languages", "tts_fallback": "vi-VN"},
    "th": {"name": "Thai (ไทย)", "locale": "th-TH", "flag": "🇹🇭", "category": "Global Languages", "tts_fallback": "th-TH"},
    "id": {"name": "Indonesian (Bahasa Indonesia)", "locale": "id-ID", "flag": "🇮🇩", "category": "Global Languages", "tts_fallback": "id-ID"},
    "ms": {"name": "Malay (Bahasa Melayu)", "locale": "ms-MY", "flag": "🇲🇾", "category": "Global Languages", "tts_fallback": "ms-MY"},
    "tl": {"name": "Filipino / Tagalog", "locale": "tl-PH", "flag": "🇵🇭", "category": "Global Languages", "tts_fallback": "tl-PH"},
    "pl": {"name": "Polish (Polski)", "locale": "pl-PL", "flag": "🇵🇱", "category": "Global Languages", "tts_fallback": "pl-PL"},
    "uk": {"name": "Ukrainian (Українська)", "locale": "uk-UA", "flag": "🇺🇦", "category": "Global Languages", "tts_fallback": "uk-UA"},
    "el": {"name": "Greek (Ελληνικά)", "locale": "el-GR", "flag": "🇬🇷", "category": "Global Languages", "tts_fallback": "el-GR"},
    "cs": {"name": "Czech (Čeština)", "locale": "cs-CZ", "flag": "🇨🇿", "category": "Global Languages", "tts_fallback": "cs-CZ"},
    "sv": {"name": "Swedish (Svenska)", "locale": "sv-SE", "flag": "🇸🇪", "category": "Global Languages", "tts_fallback": "sv-SE"},
    "ro": {"name": "Romanian (Română)", "locale": "ro-RO", "flag": "🇷🇴", "category": "Global Languages", "tts_fallback": "ro-RO"},
    "hu": {"name": "Hungarian (Magyar)", "locale": "hu-HU", "flag": "🇭🇺", "category": "Global Languages", "tts_fallback": "hu-HU"},
    "fa": {"name": "Persian (فارسی)", "locale": "fa-IR", "flag": "🇮🇷", "category": "Global Languages", "tts_fallback": "fa-IR"},
    "he": {"name": "Hebrew (עברית)", "locale": "he-IL", "flag": "🇮🇱", "category": "Global Languages", "tts_fallback": "he-IL"},
    "fi": {"name": "Finnish (Suomi)", "locale": "fi-FI", "flag": "🇫🇮", "category": "Global Languages", "tts_fallback": "fi-FI"},
    "da": {"name": "Danish (Dansk)", "locale": "da-DK", "flag": "🇩🇰", "category": "Global Languages", "tts_fallback": "da-DK"},
    "no": {"name": "Norwegian (Norsk)", "locale": "no-NO", "flag": "🇳🇴", "category": "Global Languages", "tts_fallback": "no-NO"},
    "sw": {"name": "Swahili (Kiswahili)", "locale": "sw-KE", "flag": "🇰🇪", "category": "Global Languages", "tts_fallback": "sw-KE"},
    "af": {"name": "Afrikaans", "locale": "af-ZA", "flag": "🇿🇦", "category": "Global Languages", "tts_fallback": "af-ZA"},
    "sq": {"name": "Albanian (Shqip)", "locale": "sq-AL", "flag": "🇦🇱", "category": "Global Languages", "tts_fallback": "sq-AL"},
    "am": {"name": "Amharic (አማርኛ)", "locale": "am-ET", "flag": "🇪🇹", "category": "Global Languages", "tts_fallback": "am-ET"},
    "az": {"name": "Azerbaijani (Azərbaycan)", "locale": "az-AZ", "flag": "🇦🇿", "category": "Global Languages", "tts_fallback": "az-AZ"},
    "eu": {"name": "Basque (Euskara)", "locale": "eu-ES", "flag": "🇪🇸", "category": "Global Languages", "tts_fallback": "eu-ES"},
    "bg": {"name": "Bulgarian (Български)", "locale": "bg-BG", "flag": "🇧🇬", "category": "Global Languages", "tts_fallback": "bg-BG"},
    "ca": {"name": "Catalan (Català)", "locale": "ca-ES", "flag": "🇪🇸", "category": "Global Languages", "tts_fallback": "ca-ES"},
    "hr": {"name": "Croatian (Hrvatski)", "locale": "hr-HR", "flag": "🇭🇷", "category": "Global Languages", "tts_fallback": "hr-HR"},
    "et": {"name": "Estonian (Eesti)", "locale": "et-EE", "flag": "🇪🇪", "category": "Global Languages", "tts_fallback": "et-EE"},
    "gl": {"name": "Galician (Galego)", "locale": "gl-ES", "flag": "🇪🇸", "category": "Global Languages", "tts_fallback": "gl-ES"},
    "ka": {"name": "Georgian (ქართული)", "locale": "ka-GE", "flag": "🇬🇪", "category": "Global Languages", "tts_fallback": "ka-GE"},
    "is": {"name": "Icelandic (Íslenska)", "locale": "is-IS", "flag": "🇮🇸", "category": "Global Languages", "tts_fallback": "is-IS"},
    "kk": {"name": "Kazakh (Қазақша)", "locale": "kk-KZ", "flag": "🇰🇿", "category": "Global Languages", "tts_fallback": "kk-KZ"},
    "km": {"name": "Khmer (ភាសាខ្មែរ)", "locale": "km-KH", "flag": "🇰🇭", "category": "Global Languages", "tts_fallback": "km-KH"},
    "lo": {"name": "Lao (ພາສາລາວ)", "locale": "lo-LA", "flag": "🇱🇦", "category": "Global Languages", "tts_fallback": "lo-LA"},
    "lv": {"name": "Latvian (Latviešu)", "locale": "lv-LV", "flag": "🇱🇻", "category": "Global Languages", "tts_fallback": "lv-LV"},
    "lt": {"name": "Lithuanian (Lietuvių)", "locale": "lt-LT", "flag": "🇱🇹", "category": "Global Languages", "tts_fallback": "lt-LT"},
    "mk": {"name": "Macedonian (Македонски)", "locale": "mk-MK", "flag": "🇲🇰", "category": "Global Languages", "tts_fallback": "mk-MK"},
    "mn": {"name": "Mongolian (Монгол)", "locale": "mn-MN", "flag": "🇲🇳", "category": "Global Languages", "tts_fallback": "mn-MN"},
    "my": {"name": "Myanmar / Burmese (မြန်မာ)", "locale": "my-MM", "flag": "🇲🇲", "category": "Global Languages", "tts_fallback": "my-MM"},
    "sr": {"name": "Serbian (Српски)", "locale": "sr-RS", "flag": "🇷🇸", "category": "Global Languages", "tts_fallback": "sr-RS"},
    "sk": {"name": "Slovak (Slovenčina)", "locale": "sk-SK", "flag": "🇸🇰", "category": "Global Languages", "tts_fallback": "sk-SK"},
    "sl": {"name": "Slovenian (Slovenščina)", "locale": "sl-SI", "flag": "🇸🇮", "category": "Global Languages", "tts_fallback": "sl-SI"},
    "uz": {"name": "Uzbek (Oʻzbekcha)", "locale": "uz-UZ", "flag": "🇺🇿", "category": "Global Languages", "tts_fallback": "uz-UZ"},
    "cy": {"name": "Welsh (Cymraeg)", "locale": "cy-GB", "flag": "🇬🇧", "category": "Global Languages", "tts_fallback": "cy-GB"},
    "zu": {"name": "Zulu (isiZulu)", "locale": "zu-ZA", "flag": "🇿🇦", "category": "Global Languages", "tts_fallback": "zu-ZA"},
    "si": {"name": "Sinhala (සිංහල)", "locale": "si-LK", "flag": "🇱🇰", "category": "Global Languages", "tts_fallback": "si-LK"},
    "so": {"name": "Somali (Soomaali)", "locale": "so-SO", "flag": "🇸🇴", "category": "Global Languages", "tts_fallback": "so-SO"},
    "hy": {"name": "Armenian (Հայերեն)", "locale": "hy-AM", "flag": "🇦🇲", "category": "Global Languages", "tts_fallback": "hy-AM"},
    "be": {"name": "Belarusian (Беларуская)", "locale": "be-BY", "flag": "🇧🇾", "category": "Global Languages", "tts_fallback": "be-BY"},
    "bs": {"name": "Bosnian (Bosanski)", "locale": "bs-BA", "flag": "🇧🇦", "category": "Global Languages", "tts_fallback": "bs-BA"},
    "eo": {"name": "Esperanto", "locale": "eo", "flag": "🌐", "category": "Global Languages", "tts_fallback": "eo"},
    "la": {"name": "Latin (Latina)", "locale": "la", "flag": "🏛️", "category": "Global Languages", "tts_fallback": "it-IT"},
    "yi": {"name": "Yiddish (ייִדיש)", "locale": "yi", "flag": "🌐", "category": "Global Languages", "tts_fallback": "de-DE"},
    "yo": {"name": "Yoruba (Èdè Yorùbá)", "locale": "yo-NG", "flag": "🇳🇬", "category": "Global Languages", "tts_fallback": "yo-NG"},
    "ha": {"name": "Hausa", "locale": "ha-NG", "flag": "🇳🇬", "category": "Global Languages", "tts_fallback": "ha-NG"},
    "ig": {"name": "Igbo (Asụsụ Igbo)", "locale": "ig-NG", "flag": "🇳🇬", "category": "Global Languages", "tts_fallback": "ig-NG"},
    "jw": {"name": "Javanese (Basa Jawa)", "locale": "jv-ID", "flag": "🇮🇩", "category": "Global Languages", "tts_fallback": "id-ID"},
    "su": {"name": "Sundanese (Basa Sunda)", "locale": "su-ID", "flag": "🇮🇩", "category": "Global Languages", "tts_fallback": "id-ID"}
}

# Language code overrides for Google Translate engine compatibility
LANGUAGE_API_CODE_MAP: Dict[str, str] = {
    "brx": "as",    # Bodo -> Assamese regional fallback
    "ks": "ur",     # Kashmiri -> Urdu script fallback
    "kok": "gom",   # Konkani -> Goan Konkani ISO code
    "mni": "mni-Mtei",
}

# Reusable HTTP session with modern browser user-agent and connection pool
_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
})

# In-memory translation cache: (text, src, tgt) -> translated text
_CACHE: Dict[tuple, str] = {}

def clear_translation_cache():
    """Clear in-memory translation cache."""
    _CACHE.clear()

def _sync_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Synchronous translation with robust Google Client API and caching."""
    if not text or not text.strip():
        return ""
    if source_lang == target_lang:
        return text

    clean_text = text.strip()
    cache_key = (clean_text, source_lang, target_lang)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    sl = LANGUAGE_API_CODE_MAP.get(source_lang, source_lang)
    tl = LANGUAGE_API_CODE_MAP.get(target_lang, target_lang)

    # Try Google Translate client API variants (dict-chrome-ex, then gtx)
    for client_param in ("dict-chrome-ex", "gtx"):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": client_param,
                "sl": sl,
                "tl": tl,
                "dt": "t",
                "q": clean_text
            }
            resp = _session.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    translated_segments = [
                        segment[0] for segment in data[0]
                        if segment and isinstance(segment, list) and segment[0]
                    ]
                    result = "".join(translated_segments).strip()
                    if result:
                        _CACHE[cache_key] = result
                        return result
        except Exception as e:
            logger.debug(f"Google translate (client={client_param}) attempt failed: {e}")

    # Fallback: Google Mobile web scraping
    try:
        url = "https://translate.google.com/m"
        params = {"sl": sl, "tl": tl, "q": clean_text}
        resp = _session.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            soup = bs4.BeautifulSoup(resp.text, "html.parser")
            res_elem = soup.find("div", {"class": "result-container"})
            if res_elem:
                result = html.unescape(res_elem.get_text(strip=True))
                if result and result != clean_text:
                    _CACHE[cache_key] = result
                    return result
    except Exception as e:
        logger.debug(f"Mobile web translation fallback failed: {e}")

    # Fallback to original text if all attempts fail
    logger.warning(f"All translation engines failed for ({source_lang} -> {target_lang}), using original text.")
    return text

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text asynchronously without blocking."""
    if source_lang == target_lang:
        return text
    return await asyncio.to_thread(_sync_translate, text, source_lang, target_lang)

async def translate_for_multiple_languages(
    text: str,
    source_lang: str,
    target_languages: Set[str]
) -> Dict[str, str]:
    """
    Concurrently translate a single text into multiple target languages.
    Returns a dict mapping language_code -> translated_text.
    """
    results: Dict[str, str] = {source_lang: text}
    languages_to_translate = [lang for lang in target_languages if lang != source_lang]
    
    if not languages_to_translate or not text.strip():
        return results

    tasks = [
        translate_text(text, source_lang, lang)
        for lang in languages_to_translate
    ]
    
    translated_texts = await asyncio.gather(*tasks, return_exceptions=True)
    
    for lang, res in zip(languages_to_translate, translated_texts):
        if isinstance(res, Exception):
            logger.error(f"Error translating to {lang}: {res}")
            results[lang] = text
        else:
            results[lang] = res
            
    return results
