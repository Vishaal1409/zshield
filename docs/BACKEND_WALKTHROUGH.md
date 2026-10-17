# Backend walkthrough (Abhinava)

Everything in the plan's backend table that does not depend on a teammate is built and tested.
This page says what exists, how to run it, how each plan task maps to code, and what is still waiting on others.

## 1. Task status against the plan

| # | Plan task | Status | Where |
|---|---|---|---|
| 1 | FastAPI skeleton, `/health`, `/score` | Done (starter, now hardened) | `api/main.py`, `api/schemas.py` |
| 2 | Deploy dummy API on LinuxONE | **Blocked: needs Vishaal's login** | see section 6 |
| 3 | `producer.py` stream simulator, 50 to 500/s | Done | `api/producer.py`, `docs/samples/sample_stream.csv` |
| 5 | SQLite audit log, `/stats`, `/alerts`, `/analyst_action` | Done | `api/db.py`, `api/main.py` |
| 6 | State store, plug in `compute_live_features` | Done with provisional history features | `api/state.py` |
| 7 | Load ONNX once at startup | Loader done and tested on a stand-in model. **Real `model.onnx` waits for Joshua** | `api/model_runtime.py` |
| 8 | Decision engine, explain and alert calls, fail-safe | Done (Joshua's SHAP hook is optional) | `api/decision.py`, `api/main.py` |
| 9 | Load test p50/p95/p99 + throughput | Script done. **Run it on your laptop and on LinuxONE for the real table** | `api/loadtest.py` |
| 10 | Bad input and Balaa's 10 edge cases | Done for the cases in the plan. **Balaa's actual file not received** | `api/schemas.py`, tests |
| 11 | Help deploy final build to LinuxONE | Blocked until Vishaal deploys | section 6 |

## 2. Run it (Windows PowerShell, from the repo root)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-api.txt -r requirements-dev.txt

python -m pytest api/tests -q                       # 18 tests should pass
uvicorn api.main:app --port 8000                    # ONE worker only (state is in memory)
```

Second terminal (same venv):

```powershell
python -m api.producer docs/samples/sample_stream.csv --rate 200 --reset
curl http://localhost:8000/stats
curl http://localhost:8000/alerts
python -m api.loadtest --n 5000 --concurrency 1 --label "laptop"
python -m api.loadtest --n 5000 --concurrency 8 --label "laptop"
```

The loadtest appends a markdown table to `docs/loadtest_results.md`. The audit database is `zshield_audit.db` in the repo root (git-ignored). Override with `ZSHIELD_DB`.

## 3. What happens to one payment

1. **Validate.** Missing field, negative amount, NaN or infinity, empty id: HTTP 422 with a short error list. Zero and very large amounts are accepted.
2. **Duplicate check.** Same `txn_id` again returns the original decision. It is not re-scored and state is not touched.
3. **Features.** `StateStore.build_features` calls Balaa's `compute_live_features(txn, state)`, then adds `sender_txn_count_recent` and `recipient_inbound_count_recent` (last 6 steps, past events only) if her function did not.
4. **Score.** ONNX if `model/model.onnx` and `model/feature_columns.json` both exist, otherwise the placeholder rule. `/health` reports which one is live (`"scorer"`).
5. **Decide.** `model/thresholds.json`: score >= hold gives HOLD, >= step_up gives STEP_UP, else APPROVE. A bad thresholds file falls back to 0.5 / 0.9 and logs it.
6. **Fail-safe.** Any exception in steps 3 to 5 gives STEP_UP, score 0.5, reason "Scoring unavailable, extra check applied", and the error is stored in the audit log. Never a silent approve.
7. **Explain (flagged only).** Reasons from Joshua's `model.explain.explain_top3(features)` if it exists, else rule reasons (at most 3, never padded with invented ones). Alert text from `genai.explain.generate_alert` with a 2 s timeout and template fallback.
8. **Audit.** One row in SQLite: score, decision, reasons, alert text, latency, explain time, scorer, error, analyst status. A failed write is logged but never blocks the decision.

`latency_ms` in the response is steps 3 to 5 only. The alert/explain time is stored separately as `explain_ms`, so a slow LLM does not hide inside the scoring number. Say this when you quote latency.

## 4. Endpoints

Contract fields are unchanged. Additions are marked.

| Endpoint | Notes |
|---|---|
| `GET /health` | `{"status":"ok"}` plus **`scorer`** (additive) |
| `POST /score` | as in `docs/API_CONTRACT.md`. `reasons` has 1 to 3 items when flagged, empty when APPROVE |
| `GET /stats` | `value_intercepted` = HOLD amounts **minus** payments an analyst later approved |
| `GET /alerts` | latest 50 non-APPROVE, newest first, plus **`ts`** (additive) |
| `POST /analyst_action` | unknown `txn_id` now returns **HTTP 404** with `{"ok": false, ...}` (was 200) |
| `POST /admin/reset` | **new, not in contract.** Clears audit log and state so a demo story can be replayed |

Tell Vishaal about the three additions and the 404 change (the plan says contract changes go through him). Armaan needs to know about `/admin/reset`: without it, replaying a story returns the old decisions (duplicate ids) and "New recipient" no longer fires.

## 5. Measured so far (honest numbers)

Run in the cloud sandbox with the placeholder scorer, on x86, **not on your laptop and not on IBM Z**:

| Run | p50 end-to-end | p95 | p99 | Throughput |
|---|---|---|---|---|
| 1 client | 1.9 ms | 2.8 ms | 5.1 ms | about 490/s |
| 8 clients | 8.4 ms | 17.4 ms | 22.4 ms | about 795/s |

The API's own decision latency was about 0.03 ms p50 and under 0.1 ms p99 with the rule scorer. A real ONNX model will be slower, so **do not put these in the deck**. Re-run on your laptop once Joshua's model is in, and again on LinuxONE.

## 6. What is waiting on other people

| Waiting on | Needed | What you do when it arrives |
|---|---|---|
| Vishaal | LinuxONE login | On Z: `pip install -r requirements-api.txt`; note what fails (numpy and onnxruntime wheels for s390x are the risk); run the API with `--host 0.0.0.0`; call `/health` and `/score` from outside; post results. Then run `api.loadtest --label LinuxONE` there |
| Balaa | `demo_stream.csv` | `python -m api.producer data/demo_stream.csv --rate 200 --reset`. If it has no `txn_id` column ids are generated |
| Balaa | final `compute_live_features` | Replace nothing in `api/`. Check feature names. If she adds `sender_txn_count_recent` / `recipient_inbound_count_recent` herself, mine step aside (`setdefault`). **Agree the window (I used 6 steps)** so training and serving match |
| Balaa | 10 edge-case transactions | Post each to `/score`, check no 500s. Add any that fail to `api/tests/test_api.py` |
| Joshua | `model.onnx`, `thresholds.json` | Drop into `model/` |
| Joshua | **`model/feature_columns.json`** | JSON list of feature names in model input order. **This file is my assumption, not in the plan. Ask him for it** |
| Joshua | `explain.py` | I assumed `explain_top3(features: dict) -> list[str]`. Confirm the real name or change `_load_explainer` in `api/main.py` |
| Arun | `generate_alert(facts)` | Already called with `{"decision","amount","reasons"}`. Starter returns the template until he replaces it |

## 7. Known limits (say these out loud, do not hide them)

- Placeholder scorer is a hand-written rule, not the fraud model. `/health` says so.
- ONNX loading is tested only on a tiny stand-in logistic regression, not Joshua's XGBoost/LightGBM export. Re-test the moment his file arrives (output name and zipmap handling are the likely snags).
- State is in memory and single-process. Restarting the API forgets recipients and velocity (the audit log persists). Do not run more than one uvicorn worker.
- History-feature window (6 steps) and thresholds on counts (5 inbound, 10 sender) are provisional.
- The 18 tests ran on Python 3.13 on Linux. Target is 3.11. Not run on Windows or s390x.
- `model_runtime` and Docker work were not tested in Docker. Run `docker build -t zshield .` once on your machine if Docker is available.

## 8. Test checklist before code freeze (Sun 9:00 PM)

- [ ] `python -m pytest api/tests -q` passes
- [ ] `/health` shows `"scorer": "onnx"` (not placeholder) with Joshua's model loaded
- [ ] Producer at 200/s on `demo_stream.csv`: 0 errors, flagged cases look sensible
- [ ] Three demo stories replayed with `--reset` between them
- [ ] Fail-safe works: `test_model_failure_fails_safe_to_step_up_and_is_logged` passes (a scorer that raises gives STEP_UP and fills the audit `error` column)
- [ ] Load-test table saved for laptop and LinuxONE, labelled with the machine
- [ ] No `*.db`, keys or data files staged in git (`git status`)
