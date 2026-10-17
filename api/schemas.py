from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class Txn(BaseModel):
    """Request body for POST /score. Field names follow docs/API_CONTRACT.md exactly.
    Bad input (missing field, negative amount, NaN/inf) is rejected with HTTP 422."""

    model_config = ConfigDict(allow_inf_nan=False)

    txn_id: str = Field(min_length=1, max_length=64)
    step: int = Field(ge=0)
    type: str = Field(min_length=1, max_length=32)
    amount: float = Field(ge=0)
    nameOrig: str = Field(min_length=1, max_length=64)
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str = Field(min_length=1, max_length=64)
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
