import re

URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
SPECIAL_RE = re.compile(r"[^a-z0-9àâäçéèêëîïôöùûüÿ'!? ]+")
SPACES_RE = re.compile(r"\s+")


def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = HASHTAG_RE.sub(r"\1", text)
    text = SPECIAL_RE.sub(" ", text)
    return SPACES_RE.sub(" ", text).strip()