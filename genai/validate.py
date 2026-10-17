"""Guardrails: check generated text against the input facts before it reaches a customer or analyst."""
import re

from .sanitize import ID_RE, clean_facts

NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
PROMISE_RE = re.compile(
    r"(money|funds?|account|payment)\s+(is|are|will be)\s+(totally\s+|completely\s+)?(safe|secure|protected)|"
    r"refund|guarantee|no risk|risk[- ]free|100\s*%\s*safe|fully protected|will be reimbursed", re.I)
# Names heuristic: honorific + Capitalised word, "Dear <Capitalised>", or a tiny denylist. Fixed template
# words never match. This is a safety net, not name recognition.
NAME_RE = re.compile(r"\b(?:Mr|Mrs|Ms|Miss|Dr|Shri|Smt|Sri)\b\.?\s+[A-Z][a-z]+|\bDear\s+(?!Customer|Sir|Madam)[A-Z][a-z]+")
NAME_DENY = ("rahul", "priya", "amit", "arun", "abhinava", "john", "sharma", "kumar", "singh")
URL_RE = re.compile(r"https?:|www\.|\.com\b|@", re.I)
WORDS = {
    "STEP_UP": (re.compile(r"confirm|verif", re.I),
                re.compile(r"paused|\bheld\b|on hold|blocked|under review|approved|completed|processed", re.I)),
    "HOLD": (re.compile(r"paused|on hold|under review|\bheld\b", re.I),
             re.compile(r"approved|completed|processed|went through|successful|blocked permanently", re.I)),
}
ALWAYS_BAD = re.compile(r"approved|blocked permanently", re.I)


def _values(text: str) -> list:
    out = []
    for m in NUM_RE.findall(text):
        try:
            out.append(float(m.rstrip(",.").replace(",", "")))
        except ValueError:
            out.append(float("nan"))
    return out


def _close(a, b) -> bool:
    return abs(a - b) < 0.005


def _number_problems(text: str, f: dict) -> list:
    """Amount must appear (if known) and match; only the amount and risk score may appear as numbers."""
    probs, vals = [], _values(text)
    amt, rs = f["amount"], f["risk_score"]
    allowed_rs = [] if rs is None else [round(rs, 2), round(rs * 100)]
    if amt is not None and not any(_close(v, amt) for v in vals):
        probs.append("amount missing or does not match")
    for v in vals:
        if amt is not None and _close(v, amt):
            continue
        if any(_close(v, a) for a in allowed_rs):
            continue
        probs.append("unexpected number")
        break
    return probs


def _common_problems(text: str, f: dict) -> list:
    probs = _number_problems(text, f)
    if ID_RE.search(text):
        probs.append("account id")
    if PROMISE_RE.search(text):
        probs.append("promise")
    if NAME_RE.search(text) or any(re.search(rf"\b{n}\b", text, re.I) for n in NAME_DENY):
        probs.append("name")
    if URL_RE.search(text):
        probs.append("url or email")
    return probs


def validate_alert(text, facts) -> tuple:
    """Check a customer alert. Returns (ok, problems). Never raises."""
    try:
        f = clean_facts(facts)
        if not isinstance(text, str) or not text.strip():
            return False, ["empty"]
        probs = []
        if len(text.split()) > 40:
            probs.append("over 40 words")
        if "\n" in text.strip():
            probs.append("multiple lines")
        probs += _common_problems(text, f)
        if ALWAYS_BAD.search(text):
            probs.append("wrong decision wording")
        if f["decision"] in WORDS:
            need, ban = WORDS[f["decision"]]
            if not need.search(text) or ban.search(text):
                probs.append("decision wording mismatch")
        else:
            probs.append("no alert for this decision")
        return not probs, probs
    except Exception:
        return False, ["validator error"]


def validate_summary(text, facts) -> tuple:
    """Check an analyst summary: exactly 3 lines, same safety checks, action line matches decision."""
    try:
        f = clean_facts(facts)
        if not isinstance(text, str):
            return False, ["empty"]
        lines = [x for x in text.split("\n") if x.strip()]
        probs = [] if len(lines) == 3 and len(text.strip().split("\n")) == 3 else ["not exactly 3 lines"]
        probs += _common_problems(text, f)
        if len(lines) == 3:
            act = lines[2].lower()
            ok = ("approve" in act and "block" in act and "escalate" in act) if f["decision"] == "HOLD" \
                else ("confirm" in act and "verif" in act) if f["decision"] == "STEP_UP" else False
            if not ok:
                probs.append("action line mismatch")
        return not probs, probs
    except Exception:
        return False, ["validator error"]
