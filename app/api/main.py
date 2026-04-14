from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="People Analytics MLOps", version="0.1.0")


class HealthResponse(BaseModel):
    status: str


class ChurnPredictionRequest(BaseModel):
    age: int
    tenure_months: int
    salary: float
    engagement_score: float
    absenteeism_rate: float
    overtime_hours_monthly: float
    promoted_last_2y: bool


class ChurnPredictionResponse(BaseModel):
    churn_probability: float
    churn_risk_label: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/predict/churn", response_model=ChurnPredictionResponse)
def predict_churn(payload: ChurnPredictionRequest):
    risk = 0.15

    if payload.engagement_score < 3:
        risk += 0.25
    if payload.absenteeism_rate > 0.08:
        risk += 0.20
    if payload.overtime_hours_monthly > 20:
        risk += 0.15
    if not payload.promoted_last_2y and payload.tenure_months > 24:
        risk += 0.10

    risk = min(risk, 0.95)

    label = "low"
    if risk >= 0.70:
        label = "high"
    elif risk >= 0.40:
        label = "medium"

    return {
        "churn_probability": round(risk, 4),
        "churn_risk_label": label,
    }