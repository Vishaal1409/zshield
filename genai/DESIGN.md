# GenAI alerts: design

## Purpose
For STEP_UP and HOLD payments only, turn the decision facts into (1) a customer alert and (2) an analyst summary.
The GenAI never makes or changes a decision; it only rephrases supplied facts.

## Inputs (`facts` dict, all optional, never trusted)
`txn_id` (logging only, never in a prompt), `amount`, `type` (PaySim type), `decision`, `risk_score` (0 to 1),
`reasons` (list, max 3 used). Every other key (e.g. `nameOrig`, `nameDest`) is dropped by `sanitize.clean_facts`.

## Outputs
- `generate_alert(facts) -> str`: at most 40 words. `""` for APPROVE or an unknown decision (the API only calls it
  for non-APPROVE; its own fallback `template_alert` also returns `""` there, so nothing odd is stored).
- `analyst_summary(facts) -> str`: exactly 3 lines: what happened / why flagged / action
  (HOLD: review and Approve, Block or Escalate; STEP_UP: confirm the customer verification result). Built from a
  template and validated; the model is used for the customer alert only. `""` for APPROVE.
- `template_alert(facts)`: the deterministic alert. All functions never raise.

## Rules
- Reasons are sanitized before any use: coerced to str, control chars and `<>{}[]` removed, ids `[CM]\d{5,}` removed,
  capped at 80 chars, max 3, empties and duplicates dropped. A reason containing injection text ("ignore...",
  "system:", "you are now", URLs, emails), decision/promise words (approved, blocked, refund, guarantee, safe) or any
  digit is replaced by "Unusual activity". So reasons can never add numbers or ids.
- Canonical amount: currency symbol + western grouping, decimals only when needed (`₹9,000`, `₹9,000.50`).
  The validator accepts any grouping of the SAME value (`9000`, `9,000.00`, `1,00,000`) and rejects other values.
  PaySim amounts are synthetic units shown with ₹ for the demo only; set `GENAI_CURRENCY` to change the symbol.
- Validator (`validate.py`): at most 40 words; amount present and equal; no number except the amount and the risk
  score (`0.97` or `97%`); no account ids; decision wording matches (STEP_UP must ask to confirm/verify and not say
  paused/held/blocked; HOLD must say paused/on hold/under review and not say approved/completed); no promises
  (money is safe, refund, guarantee, no risk); no names (honorific + capitalised word, "Dear <Name>", small denylist;
  deliberately simple, not real name recognition); no URLs or emails.

## Providers (`GENAI_PROVIDER`, read at call time)
- `template` (default): no keys, no network.
- `watsonx`: `ibm-watsonx-ai` SDK imported lazily; env `WATSONX_URL`, `WATSONX_APIKEY`, `WATSONX_PROJECT_ID`,
  `WATSONX_MODEL_ID` (default `ibm/granite-3-8b-instruct`; check the exact id against the models available in the
  project). Chat API, `temperature=0`, `max_tokens=100`. Not exercised live in tests.
- `openai_compat`: any OpenAI-style `/chat/completions` endpoint via stdlib `urllib` (e.g. Ollama with a local Granite
  model at `http://localhost:11434/v1`). Env `GENAI_BASE_URL`, `GENAI_MODEL`, optional `GENAI_API_KEY`. Temperature 0.
- Prompts live in `prompts/system.md` and `prompts/fewshot.json`, loaded per call with built-in defaults if missing.
  Reasons go in a `<reasons>` block labelled as data, not instructions.

## Failure behaviour
```
facts -> sanitize/minimise -> provider (timeout GENAI_TIMEOUT_S, default 2.0 s, thread guard)
      -> validate -> ok: model text
                  -> else: template text + warning log (reason only)
template text fails validation (should not happen) -> fixed safe message per decision
```
Missing env/key/SDK, timeout, any exception or failed validation all fall back to the template. Logger
`zshield.genai` logs provider, txn_id and the reason code (exception class or validator problems); never keys, amounts
or reasons.
