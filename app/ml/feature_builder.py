import pandas as pd
from app.features.external_features import get_department_market_risk


DEPT_ATTRITION_RATE_MAPPING = {
    "Sales": 0.53,
    "Technology": 0.32,
    "HR": 0.41,
    "Finance": 0.38,
    "Operations": 0.47,
}


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "department_name" in df.columns and "salary" in df.columns:
        if "salary_pct_in_dept" not in df.columns:
            # inference tarafında tek kayıt gelirse neutral değer kullanmak
            if len(df) == 1:
                df["salary_pct_in_dept"] = 0.5
            else:
                df["salary_pct_in_dept"] = df.groupby("department_name")["salary"].rank(pct=True)

    if "department_name" in df.columns and "dept_attrition_rate" not in df.columns:
        df["dept_attrition_rate"] = df["department_name"].map(
            lambda x: DEPT_ATTRITION_RATE_MAPPING.get(x, 0.40)
        )

    if {"engagement_score", "overtime_hours_monthly"}.issubset(df.columns):
        if "engagement_x_overtime" not in df.columns:
            df["engagement_x_overtime"] = (
                df["engagement_score"] * df["overtime_hours_monthly"]
            )

    if "department_name" in df.columns and "dept_market_risk" not in df.columns:
        df["dept_market_risk"] = df["department_name"].apply(get_department_market_risk)

    return df