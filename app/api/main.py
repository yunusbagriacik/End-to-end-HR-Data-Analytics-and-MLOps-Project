# Bu dosya eğitilmiş modeli daha sonra web servisi haline getirmek için yazıldı.
"""
-FastAPI ile endpoint tanımlıyoruz:
/health
/predict/churn

health: Sistem yaşıyor mu diye kontrol etmek için.
predict/churn: Yeni çalışan feature’ları geldiğinde churn skoru döndürmek için.

-Pydantic request/response

Bu sayede API’ye gelen veri kontrol edilir:
eksik alan var mı?
tip doğru mu?
salary sayı mı?
promoted_last_2y boolean mı?

Bu production API için çok önemlidir.
"""
import joblib
import pandas as pd

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import ChurnPredictionLog


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
    churn_risk_label: str


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

    churn_probability = float(model.predict_proba(input_df)[0][1])

    if churn_probability >= 0.70:
        label = "high"
    elif churn_probability >= 0.40:
        label = "medium"
    else:
        label = "low"

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
        churn_probability=churn_probability,
        churn_risk_label=label,
    )

    db.add(log_row)
    db.commit()

    return {
        "churn_probability": round(churn_probability, 4),
        "churn_risk_label": label,
    }