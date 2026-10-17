"""GenAI alert layer (Arun owns). The model only rephrases supplied facts.
It never changes the decision. If the LLM call fails, use the template fallback."""


def template_alert(facts: dict) -> str:
    reasons = ", ".join(facts.get("reasons", [])[:3]) or "unusual activity"
    decision = facts.get("decision", "STEP_UP")
    amount = facts.get("amount", 0)
    if decision == "HOLD":
        return f"We paused a payment of {amount:,.0f} because of: {reasons}. A specialist is reviewing it."
    if decision == "STEP_UP":
        return f"Please confirm this payment of {amount:,.0f}. We noticed: {reasons}."
    return "Payment approved."


def generate_alert(facts: dict) -> str:
    """TODO: call the LLM (watsonx.ai or another API) with a strict prompt, max 40 words.
    Fall back to template_alert on any error."""
    try:
        raise NotImplementedError  # replace with the real LLM call
    except Exception:
        return template_alert(facts)
