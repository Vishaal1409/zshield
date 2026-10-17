"""Clean untrusted input facts. Reasons are DATA: never trusted, never allowed to add numbers or IDs."""
import math
import re

from .rules import HOLD_WORDS, ID_RE, forbidden

DECISIONS = ("APPROVE", "STEP_UP", "HOLD")
TYPES = ("PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT")   # PaySim transaction types
FALLBACK_REASON = "Unusual activity"
CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]+")
STRIP_RE = re.compile(r"[<>{}\[\]`]")
# Injection text inside a reason: the whole reason is replaced. Promise, name, URL, decision and other
# customer-text rules come from rules.forbidden, the same check the validator runs on the output.
INJECTION_RE = re.compile(
    r"\b(?:ignore|disregard|forget|override|pretend)\b|\b(?:previous|new|above) instructions\b|"
    r"\b(?:system|assistant)\s*:|you are now|\bact as\b|\b(?:system )?prompt\b|\b(?:earlier|previous) messages\b", re.I)


def _unsafe(s: str) -> bool:
    return bool(INJECTION_RE.search(s) or forbidden(s) or HOLD_WORDS.search(s) or re.search(r"\d", s))


def clean_reasons(reasons, limit: int = 80) -> list:
    """Return up to 3 safe, short, digit-free reason strings. Never raises."""
    try:
        if isinstance(reasons, str):
            reasons = [reasons]
        if not isinstance(reasons, (list, tuple)):
            return []
        out = []
        for r in reasons:
            if r is None:
                continue
            s = " ".join(STRIP_RE.sub(" ", CTRL_RE.sub(" ", str(r)[:500])).split())
            if not s:
                continue
            bad = _unsafe(s)
            s = ID_RE.sub("", s).strip()
            if bad or not s:
                s = FALLBACK_REASON
            s = s[:limit].rstrip(" ,.;:-")
            if s and s not in out:
                out.append(s)
            if len(out) == 3:
                break
        return out
    except Exception:
        return []


def _num(v):
    if isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError, OverflowError):
        return None
    return f if math.isfinite(f) else None


def clean_facts(facts) -> dict:
    """Minimal facts: only decision, amount, type, risk_score, reasons (+ txn_id for logging). Never raises."""
    f = facts if isinstance(facts, dict) else {}
    d = str(f.get("decision", "")).strip().upper()
    amt = _num(f.get("amount"))
    rs = _num(f.get("risk_score"))
    t = str(f.get("type", "")).strip().upper()
    return {
        "decision": d if d in DECISIONS else "",
        "amount": round(amt, 2) if amt is not None and amt >= 0 else None,   # cents, as displayed
        "type": t if t in TYPES else None,
        "risk_score": min(max(rs, 0.0), 1.0) if rs is not None else None,
        "reasons": clean_reasons(f.get("reasons")),
        "txn_id": " ".join(str(f.get("txn_id", ""))[:40].split()),
    }
