"""Deterministic wording. Also the fallback whenever a model is missing, slow or fails validation."""
import os

from .sanitize import FALLBACK_REASON, clean_facts

MAX_WORDS = 40
# PaySim amounts are synthetic units; they are shown with a currency symbol (default rupee) for the demo only.
STEP_UP_T = "Please confirm this payment{amt} in your app. We noticed: {why}. If someone asked you to send this, stop and call your bank."
HOLD_T = "We paused a payment{amt} for a safety review. Reason: {why}. Our team will contact you. Never share your OTP or PIN."
LAST_RESORT = {
    "STEP_UP": "Please confirm this payment in your app. If someone asked you to send this, stop and call your bank.",
    "HOLD": "We paused a payment for a safety review. Our team will contact you. Never share your OTP or PIN.",
}
ACTION = {
    "HOLD": "Action: review the case and choose Approve, Block or Escalate.",
    "STEP_UP": "Action: confirm the customer verification result, then release or stop the payment.",
}


def currency() -> str:
    return os.environ.get("GENAI_CURRENCY", "₹")


def fmt_amount(amount) -> str:
    """Canonical format: symbol + western grouping, decimals only when needed (9,000 / 9,000.50). '' if unknown."""
    if amount is None:
        return ""
    s = f"{amount:,.2f}"
    return currency() + (s[:-3] if s.endswith(".00") else s)


def _lower(r: str) -> str:
    return r[:1].lower() + r[1:] if r[1:2].islower() else r


def alert_for(f: dict) -> str:
    """Customer alert from CLEAN facts, at most 40 words (reasons are dropped or truncated to fit)."""
    d = f["decision"]
    if d not in LAST_RESORT:
        return ""
    tpl = STEP_UP_T if d == "STEP_UP" else HOLD_T
    amt = fmt_amount(f["amount"])
    amt = f" of {amt}" if amt else ""
    reasons = [_lower(r) for r in f["reasons"]] or [_lower(FALLBACK_REASON)]
    while True:
        text = tpl.format(amt=amt, why=", ".join(reasons))
        over = len(text.split()) - MAX_WORDS
        if over <= 0:
            return text
        if len(reasons) > 1:
            reasons.pop()
        else:
            words = reasons[0].split()
            reasons = [" ".join(words[:max(1, len(words) - over)])]
            if len(words) == 1:
                reasons = [_lower(FALLBACK_REASON)]


def summary_for(f: dict) -> str:
    """Exactly 3 lines: what happened, why flagged, what the analyst should do."""
    d = f["decision"]
    if d not in ACTION:
        return ""
    head = "Payment held for review" if d == "HOLD" else "Extra check requested"
    bits = [b for b in (f["type"], f"of {fmt_amount(f['amount'])}" if f["amount"] is not None else "") if b]
    l1 = f"{head}: {' '.join(bits) or 'payment'}"
    if f["risk_score"] is not None:
        l1 += f", risk score {f['risk_score']:.2f}"
    l2 = "Flagged because: " + "; ".join(f["reasons"] or [FALLBACK_REASON]) + "."
    return f"{l1}.\n{l2}\n{ACTION[d]}"


def template_for(facts) -> str:
    return alert_for(clean_facts(facts))
