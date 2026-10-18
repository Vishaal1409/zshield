from __future__ import annotations

import os
import random
import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st


DECISIONS = ["APPROVE", "STEP_UP", "HOLD"]
TX_TYPES = ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"]


def sample_data() -> pd.DataFrame:
    if "transactions" not in st.session_state:
        rng = random.Random(17)
        now = datetime.now()
        rows = []
        for i in range(160):
            decision = rng.choices(DECISIONS, weights=[83, 11, 6])[0]
            amount = round(rng.uniform(15, 8000) if decision != "HOLD" else rng.uniform(1200, 14000), 2)
            rows.append({
                "step": i + 1,
                "txn_id": f"TXN-{100000 + i}",
                "time": now - timedelta(seconds=(160 - i) * 22),
                "type": rng.choice(TX_TYPES),
                "amount": amount,
                "risk_score": round(rng.uniform(.01, .97) if decision != "APPROVE" else rng.uniform(.01, .38), 3),
                "decision": decision,
                "latency_ms": rng.randint(4, 39),
                "nameOrig": f"C{rng.randint(1000000, 9999999)}",
                "nameDest": f"C{rng.randint(1000000, 9999999)}",
                "analyst_status": "Needs review" if decision != "APPROVE" else "Auto-approved",
                "reasons": ["Unusual transfer amount", "New recipient", "Account activity changed"],
                "alert_text": "This transfer differs from the account's recent activity. Verify the recipient before the payment is released.",
            })
        st.session_state.transactions = pd.DataFrame(rows)
        st.session_state.started_at = time.time()
    return st.session_state.transactions.copy()


def stats(df: pd.DataFrame) -> dict:
    flagged = df[df.decision.isin(["STEP_UP", "HOLD"])]
    held = df[df.decision == "HOLD"]
    return {
        "total_processed": len(df),
        "flagged_count": len(flagged),
        "held_count": len(held),
        "value_intercepted": float(held.amount.sum()),
        "avg_latency_ms": float(df.latency_ms.mean()) if len(df) else 0,
        "p95_latency_ms": float(df.latency_ms.quantile(.95)) if len(df) else 0,
    }


def replay_story(story: str) -> None:
    df = sample_data()
    rng = random.Random()
    additions = []
    current = datetime.now()
    for i in range(12):
        if story == "Scam Drain":
            decision, amount, typ = ("HOLD", 9600 + i * 18, "TRANSFER") if i == 11 else ("APPROVE", rng.randint(20, 150), "PAYMENT")
        elif story == "Mule Burst":
            decision, amount, typ = ("STEP_UP", rng.randint(300, 1400), "TRANSFER") if i >= 7 else ("APPROVE", rng.randint(25, 250), "PAYMENT")
        else:
            decision, amount, typ = "APPROVE", rng.randint(12, 380), "PAYMENT"
        additions.append({
            "step": int(df.step.max()) + i + 1, "txn_id": f"DEMO-{int(time.time())}-{i}",
            "time": current + timedelta(seconds=i * 2), "type": typ, "amount": amount,
            "risk_score": .92 if decision == "HOLD" else (.68 if decision == "STEP_UP" else .08),
            "decision": decision, "latency_ms": rng.randint(5, 24), "nameOrig": f"C{rng.randint(1000000, 9999999)}",
            "nameDest": f"C{rng.randint(1000000, 9999999)}", "analyst_status": "Needs review" if decision != "APPROVE" else "Auto-approved",
            "reasons": ["Full balance transfer", "New recipient", "Activity outside normal pattern"] if decision == "HOLD" else ["Recipient activity increased", "Transfer pattern changed", "Amount differs from recent activity"],
            "alert_text": "A rapid transfer pattern has been flagged for review before settlement." if decision != "APPROVE" else "Payment approved with low observed risk.",
        })
    st.session_state.transactions = pd.concat([df, pd.DataFrame(additions)], ignore_index=True).tail(300)
    st.session_state.active_story = story


def format_money(value: float) -> str:
    return f"${value:,.0f}"
