import os
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

from sqlalchemy import create_engine
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix, f1_score,precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from app.core.config import settings
from app.ml.feature_builder import add_engineered_features


def main():
    engine = create_engine(settings.database_url)

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
        e.promoted_last_2y,
        e.attrition_flag
    FROM employees e
    JOIN departments d
      ON e.department_id = d.id
    """

    df = pd.read_sql(query, engine)
    df = add_engineered_features(df)

    X = df.drop(columns=["employee_code", "attrition_flag"])
    y = df["attrition_flag"].astype(int)

    categorical_features = ["department_name", "gender", "job_title"]
    numeric_features = [
        "salary",
        "performance_score",
        "engagement_score",
        "absenteeism_rate",
        "overtime_hours_monthly",
        "salary_pct_in_dept",
        "dept_attrition_rate",
        "engagement_x_overtime",
        "dept_market_risk"
    ]
    binary_features = ["promoted_last_2y"]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
            ("bin", "passthrough", binary_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", XGBClassifier(
                n_estimators=400,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric="logloss"
            )),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )


    mlflow.set_experiment("churn_prediction")

    with mlflow.start_run():
        model.fit(X_train, y_train)

        y_proba = model.predict_proba(X_test)[:, 1]

        precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
        f1_scores = 2 * (precisions[:-1] * recalls[:-1]) / (precisions[:-1] + recalls[:-1] + 1e-9)
        best_idx = f1_scores.argmax()
        best_threshold = thresholds[best_idx]

        print("Best threshold:", best_threshold)

        y_pred = (y_proba >= best_threshold).astype(int)

        auc = roc_auc_score(y_test, y_proba)
        f1 = f1_score(y_test, y_pred)

        print(f"ROC AUC: {auc:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))

        os.makedirs("artifacts", exist_ok=True)
        joblib.dump(model, "artifacts/churn_model.joblib")
        print("\nModel saved to artifacts/churn_model.joblib")

        mlflow.log_param("model_type", "xgboost_v1")
        mlflow.log_param("n_estimators", 400)
        mlflow.log_param("max_depth", 5)
        mlflow.log_param("learning_rate", 0.05)
        mlflow.log_param("subsample", 0.8)
        mlflow.log_param("colsample_bytree", 0.8)
        mlflow.log_param(
            "feature_set",
            "baseline + salary_pct_in_dept + dept_attrition_rate + engagement_x_overtime + dept_market_risk"
        )
        mlflow.log_metric("roc_auc", auc)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("best_threshold", float(best_threshold))

        input_example = X_train.head(3).copy()
        signature = infer_signature(X_train, model.predict_proba(X_train))

        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            signature=signature,
            input_example=input_example,
            registered_model_name="hr_churn_model"
        )


if __name__ == "__main__":
    mlflow.set_tracking_uri("file:/app/mlruns")
    mlflow.set_experiment("churn_prediction")
    main()