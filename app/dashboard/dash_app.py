"""
Şu an dashboard teknik olarak çalışıyor ama sadece 2 kayıt olduğu için iş değeri sınırlı görünüyor.

Gerçek bir dashboard hissi için şunu yapıyorum: employees tablosundaki tüm 3000 çalışanı
eğitilmiş modelden geçirip churn_prediction_logs tablosuna basılacak. Buna batch scoring denir.

Bu çok önemli çünkü production’da genelde iki tahmin modu olur:
real-time scoring → API ile tek kişi
batch scoring → tüm çalışanlar için toplu skor
"""

import pandas as pd
from sqlalchemy import create_engine

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px

from app.core.config import settings


engine = create_engine(settings.database_url)


def load_prediction_logs() -> pd.DataFrame:
    query = """
    SELECT
        id,
        department_name,
        gender,
        job_title,
        salary,
        performance_score,
        engagement_score,
        absenteeism_rate,
        overtime_hours_monthly,
        promoted_last_2y,
        churn_probability,
        churn_risk_label,
        created_at
    FROM churn_prediction_logs
    ORDER BY created_at DESC
    """
    df = pd.read_sql(query, engine)
    return df


app = Dash(__name__)
app.title = "People Analytics Dashboard"

app.layout = html.Div(
    style={"fontFamily": "Arial", "margin": "20px"},
    children=[
        html.H1("People Analytics Dashboard"),
        html.P("Churn prediction monitoring and management view"),

        html.Button("Refresh Data", id="refresh-button", n_clicks=0),
        dcc.Interval(id="auto-refresh", interval=30 * 1000, n_intervals=0),

        html.Br(),
        html.Br(),

        html.Div(id="summary-cards", style={"display": "flex", "gap": "20px"}),

        html.Br(),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                dcc.Graph(id="risk-label-chart"),
                dcc.Graph(id="department-risk-chart"),
            ],
        ),

        html.Br(),

        html.H3("Latest Predictions"),
        dash_table.DataTable(
            id="predictions-table",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontFamily": "Arial",
                "fontSize": "14px",
            },
            style_header={
                "fontWeight": "bold",
            },
        ),
    ],
)


@app.callback(
    Output("summary-cards", "children"),
    Output("risk-label-chart", "figure"),
    Output("department-risk-chart", "figure"),
    Output("predictions-table", "data"),
    Output("predictions-table", "columns"),
    Input("refresh-button", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
)
def update_dashboard(_, __):
    df = load_prediction_logs()

    if df.empty:
        empty_fig = px.bar(title="No data yet")
        return (
            [
                html.Div("No prediction data yet.", style={"padding": "20px", "border": "1px solid #ccc"})
            ],
            empty_fig,
            empty_fig,
            [],
            [],
        )

    total_predictions = len(df)
    avg_risk = round(df["churn_probability"].mean(), 4)
    high_risk_count = int((df["churn_risk_label"] == "high").sum())

    summary_cards = [
        html.Div(
            [
                html.H3("Total Predictions"),
                html.P(str(total_predictions), style={"fontSize": "24px", "fontWeight": "bold"}),
            ],
            style={"padding": "20px", "border": "1px solid #ddd", "borderRadius": "10px", "minWidth": "220px"},
        ),
        html.Div(
            [
                html.H3("Average Churn Risk"),
                html.P(str(avg_risk), style={"fontSize": "24px", "fontWeight": "bold"}),
            ],
            style={"padding": "20px", "border": "1px solid #ddd", "borderRadius": "10px", "minWidth": "220px"},
        ),
        html.Div(
            [
                html.H3("High Risk Count"),
                html.P(str(high_risk_count), style={"fontSize": "24px", "fontWeight": "bold"}),
            ],
            style={"padding": "20px", "border": "1px solid #ddd", "borderRadius": "10px", "minWidth": "220px"},
        ),
    ]

    risk_counts = (
        df["churn_risk_label"]
        .value_counts()
        .reset_index()
    )
    risk_counts.columns = ["risk_label", "count"]

    risk_fig = px.bar(
        risk_counts,
        x="risk_label",
        y="count",
        title="Prediction Count by Risk Label",
    )

    dept_risk = (
        df.groupby("department_name", as_index=False)["churn_probability"]
        .mean()
        .sort_values("churn_probability", ascending=False)
    )

    dept_fig = px.bar(
        dept_risk,
        x="department_name",
        y="churn_probability",
        title="Average Churn Probability by Department",
    )

    table_df = df.copy()
    table_df["created_at"] = table_df["created_at"].astype(str)

    columns = [{"name": col, "id": col} for col in table_df.columns]
    data = table_df.to_dict("records")

    return summary_cards, risk_fig, dept_fig, data, columns


if __name__ == "__main__":
    app.run(debug=True, port=8050)