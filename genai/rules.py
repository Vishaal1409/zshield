"""Shared text rules. The reason sanitizer and the output validator use the same lists, so a reason that
passes the sanitizer can never make a template fail validation."""
import os
import re
import unicodedata

ID_RE = re.compile(r"[CM]\d{5,}")
URL_RE = re.compile(r"https?:|www\.|@|\b[a-z0-9-]+\.[a-z]{2,}(?:/|\b)", re.I)
PROMISE_RE = re.compile(
    r"refund|guarantee|money back|nothing to worry|we promise|no risk|risk[- ]free|100\s*%\s*safe|reimburs|"
    r"\b(?:is|are|stays?|remains?|will\s+(?:be|stay|remain))\s+(?:totally\s+|fully\s+|completely\s+)?"
    r"(?:safe|secure|protected|fine)\b|fully protected", re.I)
# Names: honorific or greeting + Capitalised word, or a small denylist (demo persona names, common names).
# A safety net, not real name recognition.
NAME_RE = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Dr|Shri|Smt|Sri)\b\.?\s+[A-Z][a-z]+|"
                     r"\b(?:Dear|Hi|Hello|Hey|Namaste|Namaskar)\s+(?!Customer\b|Sir\b|Madam\b|there\b)[A-Z][a-z]+")
NAME_DENY = re.compile(r"\b(?:meera|kamla|rahul|priya|amit|john|sharma|kumar|singh)\b", re.I)
# Asking for secrets is only allowed inside the fixed safety line.
SAFE_SECRET_LINE = re.compile(r"(?:never|do not|don't) share your otp or pin", re.I)
SECRET_RE = re.compile(r"\b(?:otp|pin|cvv|password|passcode|upi pin)\b", re.I)
# "one" is left out on purpose: "Account emptied in one transfer" is a normal reason.
NUMBER_WORDS = re.compile(r"\b(?:zero|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|"
                          r"thirty|forty|fifty|hundred|thousand|lakh|crore|million|billion)\b", re.I)
# Words that would change or contradict a decision. Banned for every decision.
DECISION_CHANGE = re.compile(
    r"\bapprov|\bblocked\b|cancel|declin|revers|reject|\bsent\b|went (?:ahead|through)|no need|"
    r"\bnot\s+(?:been\s+)?(?:paused|held|on hold)|\breleased?\b|\bcompleted?\b|\bprocessed\b|successful", re.I)
# Words that mean HOLD. A STEP_UP text must not use them.
HOLD_WORDS = re.compile(r"paused|\bheld\b|on hold|under review", re.I)
INVISIBLE = {"Cf", "Cc", "Co", "Cs", "Cn"}


def currency() -> str:
    return os.environ.get("GENAI_CURRENCY", "₹")


def bad_chars(text: str) -> bool:
    """True if the text has invisible/format characters or any non-ASCII character other than the currency
    symbol and typographic quotes/dashes. This blocks look-alike letters and non-ASCII digits."""
    allowed = set(currency()) | set("₹‘’“”–—")
    for ch in text:
        if ch in "\n\t":
            continue
        if unicodedata.category(ch) in INVISIBLE or (ord(ch) > 127 and ch not in allowed):
            return True
    return False


def forbidden(text: str) -> list:
    """Problems that apply to any customer-facing text, whatever the decision."""
    probs = []
    if bad_chars(text):
        probs.append("non-ascii or invisible characters")
    if ID_RE.search(text):
        probs.append("account id")
    if PROMISE_RE.search(text):
        probs.append("promise")
    if NAME_RE.search(text) or NAME_DENY.search(text):
        probs.append("name")
    if URL_RE.search(text):
        probs.append("url or email")
    if SECRET_RE.search(SAFE_SECRET_LINE.sub("", text)):
        probs.append("mentions otp/pin outside the safety line")
    if NUMBER_WORDS.search(text):
        probs.append("number written in words")
    if DECISION_CHANGE.search(text):
        probs.append("wrong decision wording")
    return probs
