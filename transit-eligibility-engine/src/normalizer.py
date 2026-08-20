import re
import unicodedata

HEBREW_PUNCT_RE = re.compile(r"[\u0590-\u05FF]+")


def normalize_hebrew(text) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""
    if not text or text.strip().lower() in ("nan", "none"):
        return ""
    # Normalize unicode, remove diacritics, unify quotes and whitespace
    txt = unicodedata.normalize("NFKC", text)
    txt = re.sub(r"[\u0591-\u05C7]", "", txt)  # remove nikud and trop
    txt = txt.replace('״', '"').replace('׳', "'")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt
