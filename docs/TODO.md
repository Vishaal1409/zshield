# TODO: text to add once the work is done

The deck, demo script, abstract, problem statement, personas and responsible-AI page now describe only what is built and measured, as of Sun 18 Oct. This file holds everything that was taken out. Add an item only after you have seen the work run. Then follow the steps under "After any change" at the bottom.

`[[...]]` marks a blank to fill with the real value.

---

## 1. Trained model, exported to ONNX (Joshua)

**Done when:** `model/model.onnx` and `model/feature_columns.json` are in the repo, and `curl localhost:8000/health` shows `"scorer": "onnx"`.

| Where | Change |
|---|---|
| `docs/deck/storyline.md`, slide 3, Small | Replace "The score and the reasons come from a rule-based scorer." with "The score comes from a [[XGBoost or LightGBM]] model exported to ONNX." |
| Slide 5, bullet 1 | "scorer" → "ONNX model ([[model name]])". In Small, delete "(tested with a stand-in model)". |
| Slide 7, bullet 1 | Replace with: "Trained on PaySim with a time-based split: train steps [[a–b]], validate [[c–d]], test [[e–f]]. Class weights for rare fraud." |
| Slide 7, Small | Add before the PaySim sentence: "Baseline: logistic regression. Thresholds chosen by cost: missed fraud against extra checks ([[two-sentence logic from Joshua]])." |
| `docs/abstract/abstract_draft.md`, all three | After the routing sentence, add: "The score comes from a [[model]] exported to ONNX, trained on synthetic PaySim data with a time-based split." |
| `docs/problem/problem_statement.md`, "What ZShield does" | Bullet 1: add "with a [[model]] exported to ONNX". |
| `docs/responsible_ai.md`, intro | Replace the rule-based scorer sentence with "The API runs the ONNX model `[[file]]`; `GET /health` shows `onnx`." |
| `docs/deck/demo_script.md`, pre-flight | `/health` should show `"scorer": "onnx"`. Say "the model", not "the rule-based scorer". |

Then: re-run the load test and the sample replay (see item 13). Every replay number changes.

## 2. Model results (Joshua)

**Done when:** test-split metrics exist and the charts are saved.

- Slide 8, add as bullet 1 (move the alert-safety bullet into the speaker notes): "Test steps [[e–f]]: PR-AUC [[x]] against a logistic regression baseline of [[y]]; recall [[r]] at a [[f]] false-positive rate."
- Slide 8, Box: "VISUAL: PR curve, model against baseline, and confusion matrix (Joshua)".
- Slide 8, Small: replace "with the rule-based scorer" with "with the ONNX model". Keep the machine name.
- Abstract, long version: "On the test steps, PR-AUC is [[x]] against [[y]] for the baseline, and recall is [[r]] at a [[f]] false-positive rate."
- Never quote accuracy.

## 3. SHAP reasons wired into the API (Joshua, with Abhinava)

**Done when:** `model/explain.py` has `explain_top3(features)`, the API uses it, and `/score` returns its reasons. Reason strings must follow the format note in `docs/handoffs.md` (to Joshua), or the safety filter replaces them.

- Slide 3, bullet 2: "Flagged payments get the top 3 SHAP reasons and a short customer alert."
- Slide 3, Small: "The reasons come from SHAP; rule reasons are the fallback."
- Slide 8, Box: add "SHAP summary plot (Joshua)".
- `docs/problem/personas.md` (Meera) and `docs/problem/problem_statement.md`: "up to 3 plain reasons" → "the top 3 reasons (SHAP)".
- `docs/responsible_ai.md`, Transparency row: "The top 3 reasons come from SHAP (`model.explain.explain_top3`); rule reasons in `api/decision.py` are the fallback."
- Re-run the replay. The reason wording in the alert text on slide 4 and in the script will change.

## 4. Fairness and drift numbers (Joshua; amount bands from Balaa)

**Done when:** every `[[NEEDS]]` in `docs/fairness_robustness_template.md` is filled from a real run.

- `docs/responsible_ai.md`, Fairness row, add: "We compare false-positive and miss rates by payment type and amount band. Largest gap: [[gap]]. Full table: `docs/fairness_robustness_template.md`."
- `docs/responsible_ai.md`, Limits row, add: "Early against late steps: [[PSI or KS value]]."
- Slide 9, bullet 3, add: "Error rates checked by payment type and amount band: [[one-line result]]."
- `README.md`, Responsible AI section: link the filled report again.

## 5. EDA charts and data methodology (Balaa)

**Done when:** charts are in `docs/eda/`, `features/data_card.md` is filled, and the methodology text is written.

- Slide 7, Box: "VISUAL: EDA chart, fraud by payment type and over time (Balaa, docs/eda/)". The feature table can move to the speaker notes.
- Slide 7, Small, add: "PaySim: [[rows]] payments, fraud rate [[x]]%."
- `docs/responsible_ai.md`, Privacy row: add `features/data_card.md` to "How a judge can see it".
- Fairness template (b): confirm whether fraud appears only in TRANSFER and CASH_OUT.

## 6. Demo stream and story files (Balaa) and Demo Mode (Armaan)

**Done when:** `data/demo_stream.csv` and the three story files exist, and Demo Mode replays them.

- If the demo switches from `docs/samples/sample_stream.csv` to the story files, re-run and replace every replay number. They are: 252 payments, 245 approved, 5 STEP_UP, 2 HOLD, ₹48,000 / ₹31,500, ₹79,500 held, T240, T247–T251, "after five transfers".
- Places: slides 4, 8 and 10 in `storyline.md`, `demo_script.md`, and the long abstract.
- Script: replace the producer command with "Click Demo Mode: Scam Drain" (and so on) once the buttons exist.

## 7. Dashboard pages and Block button (Armaan)

**Done when:** Live Feed, Alert Detail, Impact and Under the Hood pages exist, and Block calls `POST /analyst_action`.

- `demo_script.md`, 0:30–2:00, on-screen column:
  - Scam Drain: "Open Alert Detail for the held payment: risk gauge, top 3 reasons, alert text."
  - Block row: replace the `/docs` step with "Click Block on Alert Detail. Status changes to BLOCK."
  - Normal Day: "Live Feed fills with APPROVE rows."
- Slide 4, Box: "VISUAL: Live Feed and Alert Detail screenshots (Armaan)".
- Slide 10, Box: "VISUAL: Impact page screenshot (Armaan)".
- `docs/responsible_ai.md`, Human oversight row: add "the Block button on the Alert Detail page".
- Abstract, long version: "through the API" → "from the dashboard".
- Armaan uses the 6-bullet short version in `docs/responsible_ai.md` on the Under the Hood page.

## 8. IBM Z / LinuxONE (Vishaal)

**Done when:** the API (and ideally the full demo) runs on LinuxONE, with a screenshot and a latency run there.

- Slide 6, headline: "ZShield runs on LinuxONE: [[exactly what ran]]." Only write "runs" if it ran. If it was emulated, say so.
- Slide 6, add as bullet 3 (move the package-list bullet to the notes): "On LinuxONE ([[machine]]): p95 [[x]] ms per payment, [[y]] payments per second."
- Slide 6, Box: "VISUAL: /health and /score on LinuxONE, screenshot (Vishaal)".
- Only if the model was compiled for the Telum on-chip AI accelerator (for example with the IBM Z Deep Learning Compiler) and measured, add: "Scored on the Telum on-chip AI accelerator: [[result]]." Otherwise say nothing about Telum.
- If onnxruntime was built for s390x, note how, in the README IBM Z section (Vishaal's).
- `demo_script.md`, 2:00–2:30: "ZShield runs on LinuxONE: [[what ran]]."
- Abstract, all three: "ZShield runs on IBM LinuxONE ([[what ran]])." In place of, or after, "designed for".
- `docs/responsible_ai.md`, last line: add what ran.

## 9. IBM watsonx.ai Granite alerts, live (Arun; needs watsonx credentials)

**Done when:** a live run with `GENAI_PROVIDER=watsonx` has produced alerts that pass the checks, and you have looked at them. The code exists and is tested with mocks only. Expect many model alerts to fall back to the template, because the checks are strict.

- Slide 3, Small, add: "Alerts can also be written by an IBM Granite model on watsonx.ai. Each one passes the same checks or falls back to the template."
- Abstract, medium and long: "Alerts come from fixed templates, or from an IBM Granite model on watsonx.ai, and every one is checked."
- `docs/responsible_ai.md`, Safe GenAI row: "optional language model" → "IBM Granite on watsonx.ai ([[model id]])".

## 10. Next steps (Arun, after feature freeze at 3 PM Sunday)

Slide 10 has no "next steps" line now, because the list depends on what lands by the freeze. At 3 PM, add as bullet 4, or swap it for the PIB bullet: "Next: [[items from this file still not done]]."

## 11. Abstract format (Vishaal)

When Vishaal confirms whether an abstract is required and its word limit, trim the matching version in `docs/abstract/abstract_draft.md` after items 1–9 are in.

## 12. README "What it does" (Vishaal)

It says "top reasons (SHAP)". That isn't true until item 3 is done. It is in his handoff.

## 13. Screenshots and backup clip of the current build (Arun, now)

These need no teammate. Take them from a fresh replay (`python -m api.producer docs/samples/sample_stream.csv --rate 20 --reset`):

- Dashboard after the replay, with T240 blocked (slide 4).
- The tiles (slide 10).
- One full recorded run of the demo script, as the backup clip.

---

## After any change

1. Re-run the measurements if the scorer, the data or the machine changed. Write them to `docs/deck/measured_<date>.md` and name the machine and the scorer. Use `.venv/bin/python -m api.loadtest --n 5000 --concurrency 1 --label "<machine>" --out docs/deck/measured_<date>.md`, the same with `--concurrency 8`, and a sample replay.
2. Rebuild the deck: `.venv/bin/python docs/deck/build_deck.py`.
3. Run the tests: `.venv/bin/python -m pytest genai/tests api/tests -q`.
4. Recount the words in the abstract and the script.
5. Run one more fact-check pass before 7:30 PM Sunday.
