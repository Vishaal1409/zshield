from typing import List, Literal
from pydantic import BaseModel


class Txn(BaseModel):
    txn_id: str
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float


class ScoreResponse(BaseModel):
    txn_id: str
    risk_score: float
    decision: Literal["APPROVE", "STEP_UP", "HOLD"]
    reasons: List[str]
    alert_text: str
    latency_ms: float


class AnalystAction(BaseModel):
    txn_id: str
    action: Literal["APPROVE", "BLOCK", "ESCALATE"]
