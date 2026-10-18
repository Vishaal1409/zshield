"""Guardrails: check generated text against the input facts before it reaches a customer or analyst.
Pattern-based, so it is a strong filter, not a proof. Anything that fails goes back to the template."""
import re

from .rules import HOLD_WORDS, currency, forbidden
from .sanitize import clean_facts
from .templates import HOLD_T, LAST_RESORT, STEP_UP_T, fmt_amount

WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")
# Allowlist for model-written customer alerts: template words + this payment's reason words + a few calm words.
# A blocklist alone kept leaking new phrasings in review; any word outside this list sends us back to the template.
CALM = set("""of the an it is has been was be to with on hold held under verify check quick now because extra security
before do not only after new recipient unusual activity until pending temporarily flagged signs due please review
reviewing shortly soon risk score""".split())
TEMPLATE_WORDS = set(WORD_RE.findall(" ".join([STEP_UP_T, HOLD_T, *LAST_RESORT.values()]).lower())) - {"amt", "why"}

MAX_WORDS, MAX_CHARS = 40, 300
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
CONFIRM_RE = re.compile(r"confirm|verif", re.I)


def _indian(amount) -> str:
    """Amount with Indian digit grouping (1,00,000), same decimals rule as fmt_amount."""
    whole, _, dec = f"{amount:.2f}".partition(".")
    head, tail = whole[:-3], whole[-3:]
    while len(head) > 2:
        tail, head = head[-2:] + "," + tail, head[:-2]
    s = (head + "," + tail) if head else tail
    return currency() + (s if dec == "00" else s + "." + dec)


def _number_problems(text: str, f: dict) -> list:
    """The amount must appear exactly as displayed (₹9,000 or ₹9,000 in Indian grouping). The only other number
    allowed is the risk score, written as 0.97 or 97%."""
    probs = []
    amt, rs = f["amount"], f["risk_score"]
    rest = text
    if amt is not None:
        forms = sorted({fmt_amount(amt), _indian(amt)}, key=len, reverse=True)
        if not any(x in text for x in forms):
            probs.append("amount missing or does not match")
        for x in forms:
            rest = rest.replace(x, " ")
    allowed = set() if rs is None else {f"{rs:.2f}", f"{round(rs * 100)}%"}
    for m in NUM_RE.findall(rest):
        if m.rstrip(",.") not in allowed:
            probs.append("unexpected number")
            break
    return probs


def _without_reasons(text: str, f: dict) -> str:
    """Remove the (already sanitized) reason strings, so 'one' in 'emptied in one transfer' is not a number."""
    low = text.lower()
    for r in f["reasons"]:
        low = low.replace(r.lower(), " ")
    return low


def validate_alert(text, facts) -> tuple:
    """Check a customer alert. Returns (ok, problems). Never raises."""
    try:
        f = clean_facts(facts)
        if not isinstance(text, str) or not text.strip():
            return False, ["empty"]
        probs = []
        if len(text.split()) > MAX_WORDS or len(text) > MAX_CHARS:
            probs.append("too long")
        if "\n" in text.strip():
            probs.append("multiple lines")
        probs += _number_problems(text, f)
        probs += forbidden(text)
        if re.search(r"\bone\b", _without_reasons(text, f)):
            probs.append("number written in words")
        allowed = TEMPLATE_WORDS | CALM | set(WORD_RE.findall(" ".join(f["reasons"]).lower()))
        plain = text
        if f["amount"] is not None:
            for x in (fmt_amount(f["amount"]), _indian(f["amount"])):
                plain = plain.replace(x, " ")
        extra = sorted(set(WORD_RE.findall(plain.lower())) - allowed)
        if extra:
            probs.append("words outside the allowlist: " + ", ".join(extra[:5]))
        d = f["decision"]
        if d == "STEP_UP":
            if not CONFIRM_RE.search(text) or HOLD_WORDS.search(text):
                probs.append("decision wording mismatch")
        elif d == "HOLD":
            if not HOLD_WORDS.search(text):
                probs.append("decision wording mismatch")
        else:
            probs.append("no alert for this decision")
        return not probs, sorted(set(probs))
    except Exception:
        return False, ["validator error"]


def validate_summary(text, facts) -> tuple:
    """Check an analyst summary: exactly 3 lines, same safety checks, action line matches the decision.
    Decision words are allowed here because the action line names the analyst's options."""
    try:
        f = clean_facts(facts)
        if not isinstance(text, str):
            return False, ["empty"]
        lines = [x for x in text.split("\n") if x.strip()]
        probs = [] if len(lines) == 3 and len(text.strip().split("\n")) == 3 else ["not exactly 3 lines"]
        probs += _number_problems(text, f)
        probs += [p for p in forbidden(text) if p not in ("wrong decision wording",)]
        if len(lines) == 3:
            act = lines[2].lower()
            ok = ("approve" in act and "block" in act and "escalate" in act) if f["decision"] == "HOLD" \
                else ("confirm" in act and "verif" in act) if f["decision"] == "STEP_UP" else False
            if not ok:
                probs.append("action line mismatch")
        return not probs, probs
    except Exception:
        return False, ["validator error"]
