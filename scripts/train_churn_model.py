import os
import joblib #modeli kaydetmek için
import pandas as pd

from sqlalchemy import create_engine
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

from app.core.config import settings


def main():
    engine = create_engine(settings.database_url) #config dosyasından gelen DB URL ile bağlantı kuruluyor.

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

    X = df.drop(columns=["employee_code", "attrition_flag"])
    y = df["attrition_flag"].astype(int)

    categorical_features = ["department_name", "gender", "job_title"]
    numeric_features = [
        "salary",
        "performance_score",
        "engagement_score",
        "absenteeism_rate",
        "overtime_hours_monthly",
    ]
    binary_features = ["promoted_last_2y"]

   #eksik varsa median ile doldur sonra scale et
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    #eksik kategorileri most_frequent ile doldur, metinleri makinenin anlayacağı sayısal vektöre çevir
    #handle_unknown="ignore" çok önemli: API’ye yeni, daha önce görülmemiş kategori gelirse sistem patlamasın.
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    # Bu yapı tüm feature’lara doğru işlemi uygular.
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
            ("bin", "passthrough", binary_features),
        ]
    )

    # Ham veriyi al → preprocessing yap → model uygula ve bunu tek nesne halinde sakla
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(
                n_estimators=200,
                max_depth=8,
                random_state=42,
                class_weight="balanced"
            )),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_proba)
    f1 = f1_score(y_test, y_pred)

    print(f"ROC AUC: {auc:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # Eğitilmiş model dosyaya dönüştü.Artık bu model notebook’a bağlı değil.Yani servise bağlanabilir.
    os.makedirs("artifacts", exist_ok=True)
    joblib.dump(model, "artifacts/churn_model.joblib")
    print("\nModel saved to artifacts/churn_model.joblib")


if __name__ == "__main__":
    main()