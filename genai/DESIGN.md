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
Shared word lists live in `rules.py`. The reason sanitizer and the output validator use the same lists, so a
clean reason can never make a template fail.
- Reasons are sanitized before any use: coerced to str, control chars and `<>{}[]` removed, capped at 80 chars,
  max 3, empties and duplicates dropped. A reason is replaced by "Unusual activity" if it contains: injection text
  ("ignore", "previous instructions", "system:", "you are now", "prompt"), any digit or number word (except "one"),
  any non-ASCII or invisible character (look-alike letters, zero-width spaces), an account id, a URL or email, a promise,
  a name, OTP/PIN, or a decision word (approv-, blocked, cancel, declin-, revers-, sent, released, completed,
  processed, paused, held, on hold, under review).
- Amount: currency symbol + western grouping, decimals only when needed (`₹9,000`, `₹9,000.50`), rounded to cents.
  The validator requires that exact string (or the same value in Indian grouping, `₹1,00,000`).
  PaySim amounts are synthetic units shown with ₹ for the demo only; set `GENAI_CURRENCY` to change the symbol.
- Validator (`validate.py`): at most 40 words and 300 characters, one line; the amount as above; no other number
  except the risk score written as `0.97` or `97%`; no number words; no non-ASCII/invisible characters; no account ids,
  URLs, names (honorific or greeting + capitalised word, small denylist incl. the demo persona names), promises
  (safe/secure/protected, refund, money back, guarantee, nothing to worry), or OTP/PIN outside the fixed line
  "Never share your OTP or PIN"; no decision-changing words; STEP_UP must ask to confirm/verify and not say
  paused/held/under review; HOLD must say paused/held/on hold/under review.
- Word allowlist (model text only): every word in a model-written alert must come from the templates, this
  payment's own reason words, or a short list of calm words (`CALM` in `validate.py`). A blocklist alone kept leaking
  new phrasings in review ("read the code from your SMS to our agent"), so anything outside the list falls back.
  A scam-pattern rule also blocks "send/transfer/pay/share ... to our/the/team/agent" built from allowed words.
- Limits: this is pattern matching, not understanding. It is strict on purpose (a good model sentence that trips a
  rule just falls back to the template), but it cannot prove a text is harmless. That is why the template is the
  default and the model is optional. `tests/test_alerts.py` keeps every bypass found in review as a regression test.

## Providers (`GENAI_PROVIDER`, read at call time)
- `template` (default): no keys, no network.
- `watsonx`: `ibm-watsonx-ai` SDK imported lazily; env `WATSONX_URL`, `WATSONX_APIKEY`, `WATSONX_PROJECT_ID`,
  `WATSONX_MODEL_ID` (default `ibm/granite-3-8b-instruct`; check the exact id against the models available in the
  project). Chat API, `temperature=0`, `max_tokens=100`; the client is cached between calls. Not exercised live in tests.
- `openai_compat`: any OpenAI-style `/chat/completions` endpoint via stdlib `urllib` (e.g. Ollama with a local Granite
  model at `http://localhost:11434/v1`). Env `GENAI_BASE_URL`, `GENAI_MODEL`, optional `GENAI_API_KEY`. Temperature 0.
- Prompts live in `prompts/system.md` and `prompts/fewshot.json`, loaded per call with built-in defaults if missing.
  Reasons go in a `<reasons>` block labelled as data, not instructions.

## Failure behaviour
```
facts -> sanitize/minimise -> provider (timeout GENAI_TIMEOUT_S, default 1.5 s, under the API's 2 s guard)
      -> validate -> ok: model text
                  -> else: template text + warning log (reason only)
template text fails validation (should not happen) -> fixed safe message per decision
```
Missing env/key/SDK, timeout, any exception or failed validation all fall back to the template. Logger
`zshield.genai` logs provider, txn_id and the reason code (exception class or validator problems); never keys, amounts
or reasons.
