import joblib
import pandas as pd

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import ChurnPredictionLog
from app.ml.feature_builder import add_engineered_features

app = FastAPI(title="People Analytics MLOps", version="0.1.0")

model = joblib.load("artifacts/churn_model.joblib")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class HealthResponse(BaseModel):
    status: str


class ChurnPredictionRequest(BaseModel):
    department_name: str
    gender: str
    job_title: str
    salary: float
    performance_score: float
    engagement_score: float
    absenteeism_rate: float
    overtime_hours_monthly: float
    promoted_last_2y: bool


class ChurnPredictionResponse(BaseModel):
    churn_probability: float
    predicted_label: int
    risk_level: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/predict/churn", response_model=ChurnPredictionResponse)
def predict_churn(payload: ChurnPredictionRequest, db: Session = Depends(get_db)):
    input_df = pd.DataFrame([{
        "department_name": payload.department_name,
        "gender": payload.gender,
        "job_title": payload.job_title,
        "salary": payload.salary,
        "performance_score": payload.performance_score,
        "engagement_score": payload.engagement_score,
        "absenteeism_rate": payload.absenteeism_rate,
        "overtime_hours_monthly": payload.overtime_hours_monthly,
        "promoted_last_2y": payload.promoted_last_2y,
    }])

    input_df = add_engineered_features(input_df)

    probability = model.predict_proba(input_df)[0][1]
    prediction = int(probability >= 0.33692988753318787)

    risk_level = "high" if probability >= 0.7 else "medium" if probability >= 0.4 else "low"

    log_row = ChurnPredictionLog(
        department_name=payload.department_name,
        gender=payload.gender,
        job_title=payload.job_title,
        salary=payload.salary,
        performance_score=payload.performance_score,
        engagement_score=payload.engagement_score,
        absenteeism_rate=payload.absenteeism_rate,
        overtime_hours_monthly=payload.overtime_hours_monthly,
        promoted_last_2y=payload.promoted_last_2y,
        churn_probability=float(probability),
        churn_risk_label=risk_level,
        prediction_source = "api"
    )

    db.add(log_row)
    db.commit()

    return {
        "churn_probability": round(float(probability), 4),
        "predicted_label": prediction,
        "risk_level": risk_level
    }

"""
{
  "department_name": "Sales",
  "gender": "M",
  "job_title": "Sales Analyst",
  "salary": 38000,
  "performance_score": 2.7,
  "engagement_score": 2.4,
  "absenteeism_rate": 0.12,
  "overtime_hours_monthly": 26,
  "promoted_last_2y": false
}
"""