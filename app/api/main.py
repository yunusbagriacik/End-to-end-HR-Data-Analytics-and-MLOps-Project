import os
import pandas as pd
import mlflow
import mlflow.pyfunc
import joblib

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import ChurnPredictionLog
from app.ml.feature_builder import add_engineered_features

app = FastAPI(title="People Analytics MLOps", version="0.1.0")

""" app = FastAPI(
    title="People Analytics MLOps",
    version="0.1.0",
    root_path="/api",
    docs_url="/docs",
    openapi_url="/openapi.json"
)
"""

#model = joblib.load("artifacts/churn_model.joblib")

def load_model():
    mlflow.set_tracking_uri = settings.mlflow_model_uri
    model_uri = settings.mlflow_model_uri
    local_model_path = settings.local_model_path

    try:
        print(f"[MODEL] Trying MLflow Registry: {model_uri}")
        model = mlflow.sklearn.load_model(model_uri)
        print("[MODEL] Loaded from MLflow Registry")
        return model, "mlflow_registry"
    except Exception as e:
        print(f"[MODEL] MLflow load failed: {e}")

    try:
        print(f"[MODEL] Trying local joblib: {local_model_path}")
        model = joblib.load(local_model_path)
        print("[MODEL] Loaded from local joblib")
        return model, "local_joblib"
    except Exception as e:
        print(f"[MODEL] Local joblib load failed: {e}")

    raise RuntimeError("No model could be loaded from MLflow Registry or local joblib.")


model, model_source = load_model()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class HealthResponse(BaseModel):
    status: str
    source: str


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
    return {
            "status": "ok",
            "source": model_source
            }


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

    probability = float(model.predict_proba(input_df)[0][1])
    prediction = int(probability >= settings.churn_threshold)


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