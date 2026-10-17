# Arun's worklog: GenAI, responsible AI, storytelling

Branch: `arun/genai` (local only, not pushed). Only Vishaal merges to main.
Source of truth: `ZShield_IBM_Z_Datathon_Team_Plan.docx` (read 17 Oct), then the Claude Code prompt.

## Change from the plan doc
- Personas: the plan asks for two (fraud analyst, first-time user). Arun asked for a **third: a fraudster
  targeting the first-time user**. It is written as an illustrative profile at the level of publicly reported
  scam patterns, with no step-by-step method.

## Integration facts found in the repo
- `api/main.py` imports `generate_alert` and `template_alert` from `genai.explain`. Both names must stay.
- The API currently passes only `decision, amount, reasons` in `facts`. The module must cope with missing
  `txn_id, type, risk_score`. (Handoff to Abhinava: add them.)
- The API already wraps the call in a 2 s timeout and falls back to `template_alert`.

## Plan and agents

| Wave | Agent | Model | Owns | Tasks |
|---|---|---|---|---|
| 1 | A: research and problem framing | sonnet | `docs/problem/` | t1 |
| 1 | B: GenAI alert engineer | sonnet | `genai/` | t2, t4, t5 |
| 1 | C: responsible AI writer | sonnet | `docs/responsible_ai.md`, `docs/fairness_robustness_template.md` | t6, t11 |
| 2 | D: storyteller | sonnet | `docs/deck/`, `docs/abstract/` | t7, t8, t9, t10 |
| 3 | E: reviewer and fact-checker | opus | read-only report | t12 |
| - | Lead | opus | `docs/arun_worklog.md`, `docs/handoffs.md`, README TODOs | review, fixes, commits |

## Acceptance criteria (lead checks each one by opening the files and running the tests)
- **A:** exact problem line verbatim; 3–4 sentence README version; 3 personas (goal, pain, what ZShield
  changes, illustrative quote); 4–5 India stats, each with figure, exact quote, publisher, report, date, URL,
  access date and deck use. Every stat comes from a page the agent opened; 2023 or later unless it's the latest
  available; units exactly as the source states them; one stat chosen for the opener.
- **B:** `pytest genai/tests` passes offline with no keys; 10 named cases plus a mocked-model fallback test;
  alert is 40 words or fewer; summary is exactly 3 lines; the validator enforces all 7 rules; the functions
  never raise; `template_alert` is kept; the existing `api/tests` still pass.
- **C:** 8 checklist areas, each with what we do and where a judge sees it; a 6-bullet, 60-word version for the
  dashboard; a fairness template with `[[NEEDS: …]]` placeholders only.
- **D:** 10 slides with a headline, at most 3 bullets, visual plus supplier, and notes; IBM Z slide uses
  "designed for / deployable on"; a 16:9 pptx with labelled placeholders; a timed 3-minute script in two
  columns plus a 60 s backup; abstracts at about 100, 150 and 250 words with results left as placeholders.
- **E:** an issue list with severity, file:line and fix. The lead resolves every item and re-checks.

## Status log
- Sat 17 Oct: read plan doc and repo, created branch and venv, `api/tests` 18 passed. Wave 1 launched.
