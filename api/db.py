"""SQLite audit log. Every decision, score, reasons, latency and analyst action is stored here.
One shared connection guarded by a lock (SQLite is fast enough for demo volumes)."""
import json
import sqlite3
import threading
import time
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    txn_id         TEXT PRIMARY KEY,
    ts             REAL NOT NULL,
    step           INTEGER,
<<<<<<< HEAD
    type           TEXT,
    nameOrig       TEXT,
    nameDest       TEXT,
=======
    type           TEXT NOT NULL DEFAULT '',
    nameOrig       TEXT NOT NULL DEFAULT '',
    nameDest       TEXT NOT NULL DEFAULT '',
>>>>>>> origin/ARMAANBRANCH
    amount         REAL NOT NULL,
    risk_score     REAL NOT NULL,
    decision       TEXT NOT NULL,
    reasons        TEXT NOT NULL,
    alert_text     TEXT NOT NULL,
    latency_ms     REAL NOT NULL,
    explain_ms     REAL NOT NULL DEFAULT 0,
    scorer         TEXT NOT NULL DEFAULT '',
    error          TEXT,
    analyst_status TEXT NOT NULL DEFAULT 'PENDING'
);
CREATE INDEX IF NOT EXISTS idx_decisions_ts ON decisions(ts);
CREATE INDEX IF NOT EXISTS idx_decisions_decision ON decisions(decision);
"""


class AuditDB:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        if path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(SCHEMA)
<<<<<<< HEAD
        self._migrate()

    def _migrate(self) -> None:
        """Older audit files (before /recent) lack type, nameOrig and nameDest: add them in place."""
        have = {r["name"] for r in self._conn.execute("PRAGMA table_info(decisions)")}
        for col in ("type", "nameOrig", "nameDest"):
            if col not in have:
                self._conn.execute(f"ALTER TABLE decisions ADD COLUMN {col} TEXT")
=======
        # Upgrade audit databases created before transaction details were retained.
        existing = {row[1] for row in self._conn.execute("PRAGMA table_info(decisions)")}
        for column, declaration in (
            ("type", "TEXT NOT NULL DEFAULT ''"),
            ("nameOrig", "TEXT NOT NULL DEFAULT ''"),
            ("nameDest", "TEXT NOT NULL DEFAULT ''"),
        ):
            if column not in existing:
                self._conn.execute(f"ALTER TABLE decisions ADD COLUMN {column} {declaration}")
>>>>>>> origin/ARMAANBRANCH

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ---- writes -------------------------------------------------------------------------
    def insert(self, rec: dict) -> bool:
        """Insert a decision. Returns False if txn_id already exists (duplicate)."""
        with self._lock:
            cur = self._conn.execute(
<<<<<<< HEAD
                "INSERT OR IGNORE INTO decisions (txn_id, ts, step, type, nameOrig, nameDest, amount,"
                " risk_score, decision, reasons, alert_text, latency_ms, explain_ms, scorer, error)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec["txn_id"], time.time(), rec.get("step"), rec.get("type"), rec.get("nameOrig"),
                 rec.get("nameDest"), rec["amount"], rec["risk_score"], rec["decision"],
                 json.dumps(rec["reasons"]), rec["alert_text"], rec["latency_ms"],
=======
                "INSERT OR IGNORE INTO decisions (txn_id, ts, step, type, nameOrig, nameDest, amount, risk_score, decision,"
                " reasons, alert_text, latency_ms, explain_ms, scorer, error)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec["txn_id"], time.time(), rec.get("step"), rec.get("type", ""),
                 rec.get("nameOrig", ""), rec.get("nameDest", ""), rec["amount"], rec["risk_score"],
                 rec["decision"], json.dumps(rec["reasons"]), rec["alert_text"], rec["latency_ms"],
>>>>>>> origin/ARMAANBRANCH
                 rec.get("explain_ms", 0.0), rec.get("scorer", ""), rec.get("error")),
            )
            return cur.rowcount == 1

    def set_status(self, txn_id: str, action: str) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE decisions SET analyst_status=? WHERE txn_id=?", (action, txn_id))
            return cur.rowcount == 1

    def reset(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM decisions")

    # ---- reads --------------------------------------------------------------------------
    @staticmethod
    def _row(r: sqlite3.Row) -> dict:
        d = dict(r)
        d["reasons"] = json.loads(d["reasons"])
        return d

    def get(self, txn_id: str) -> Optional[dict]:
        with self._lock:
            r = self._conn.execute("SELECT * FROM decisions WHERE txn_id=?", (txn_id,)).fetchone()
        return self._row(r) if r else None

    # Fields shared by /alerts and /recent (docs/API_CONTRACT.md).
    _FEED_COLS = ("txn_id, risk_score, decision, reasons, alert_text, analyst_status, amount,"
                  " COALESCE(type,'') AS type, step, COALESCE(nameOrig,'') AS nameOrig,"
                  " COALESCE(nameDest,'') AS nameDest, latency_ms")

    def _feed(self, where: str, limit: int) -> list:
        with self._lock:
            rows = self._conn.execute(
<<<<<<< HEAD
                f"SELECT {self._FEED_COLS} FROM decisions {where} ORDER BY ts DESC, rowid DESC LIMIT ?",
                (limit,)).fetchall()
        return [self._row(r) for r in rows]

    def alerts(self, limit: int = 50) -> list:
        """Flagged payments only (STEP_UP and HOLD), newest first."""
        return self._feed("WHERE decision != 'APPROVE'", limit)

    def recent(self, limit: int = 50) -> list:
        """Latest decisions of every type, including APPROVE, newest first."""
        return self._feed("", limit)
=======
                "SELECT txn_id, step, type, nameOrig, nameDest, amount, risk_score, decision,"
                " reasons, alert_text, analyst_status, latency_ms, ts"
                " FROM decisions WHERE decision != 'APPROVE' ORDER BY ts DESC, rowid DESC LIMIT ?",
                (limit,)).fetchall()
        return [self._row(r) for r in rows]

    def recent(self, limit: int = 200) -> list:
        with self._lock:
            rows = self._conn.execute(
                "SELECT txn_id, step, type, nameOrig, nameDest, amount, risk_score, decision,"
                " reasons, alert_text, analyst_status, latency_ms, ts"
                " FROM decisions ORDER BY ts DESC, rowid DESC LIMIT ?",
                (limit,)).fetchall()
        return [self._row(r) for r in rows]
>>>>>>> origin/ARMAANBRANCH

    def stats(self) -> dict:
        with self._lock:
            c = self._conn
            total, flagged, held, avg = c.execute(
                "SELECT COUNT(*), COALESCE(SUM(decision!='APPROVE'),0), COALESCE(SUM(decision='HOLD'),0),"
                " COALESCE(AVG(latency_ms),0) FROM decisions").fetchone()
            # Value intercepted = amount on HOLD payments, minus those an analyst later approved.
            intercepted = c.execute(
                "SELECT COALESCE(SUM(amount),0) FROM decisions"
                " WHERE decision='HOLD' AND analyst_status!='APPROVE'").fetchone()[0]
            p95 = 0.0
            if total:
                off = int(0.95 * (total - 1))
                p95 = c.execute("SELECT latency_ms FROM decisions ORDER BY latency_ms LIMIT 1 OFFSET ?",
                                (off,)).fetchone()[0]
        return {
            "total_processed": total,
            "flagged_count": flagged,
            "held_count": held,
            "value_intercepted": intercepted,
            "avg_latency_ms": round(avg, 3),
            "p95_latency_ms": round(p95, 3),
        }
