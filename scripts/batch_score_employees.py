import joblib
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import ChurnPredictionLog
from app.ml.feature_builder import add_engineered_features


model = joblib.load("artifacts/churn_model.joblib")
engine = create_engine(settings.database_url)


def main():
    query = """
    SELECT
        e.employee_code,
        d.department_name,
        e.gender,
        e.job_title,
        e.salary,
        e.performance_score,
        e.engagement_score,
        e.absenteeism_rate,
        e.overtime_hours_monthly,
        e.promoted_last_2y
    FROM employees e
    JOIN departments d
      ON e.department_id = d.id
    """

    df = pd.read_sql(query, engine)
    df = add_engineered_features(df)

    prediction_input = df[[
        "department_name",
        "gender",
        "job_title",
        "salary",
        "performance_score",
        "engagement_score",
        "absenteeism_rate",
        "overtime_hours_monthly",
        "promoted_last_2y",
        "salary_pct_in_dept",
        "dept_attrition_rate",
        "engagement_x_overtime",
        "dept_market_risk",
    ]]
    probabilities = model.predict_proba(prediction_input)[:, 1]

    df["churn_probability"] = probabilities
    df["churn_risk_label"] = df["churn_probability"].apply(
        lambda x: "high" if x >= 0.70 else ("medium" if x >= 0.40 else "low")
    )

    db: Session = SessionLocal()

    try:
        for _, row in df.iterrows():
            log_row = ChurnPredictionLog(
                department_name=row["department_name"],
                gender=row["gender"],
                job_title=row["job_title"],
                salary=float(row["salary"]),
                performance_score=float(row["performance_score"]),
                engagement_score=float(row["engagement_score"]),
                absenteeism_rate=float(row["absenteeism_rate"]),
                overtime_hours_monthly=float(row["overtime_hours_monthly"]),
                promoted_last_2y=bool(row["promoted_last_2y"]),
                churn_probability=float(row["churn_probability"]),
                churn_risk_label=row["churn_risk_label"],
                prediction_source="batch"

            )
            db.add(log_row)

        db.commit()
        print(f"{len(df)} employee predictions inserted into churn_prediction_logs.")

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()


if __name__ == "__main__":
    main()