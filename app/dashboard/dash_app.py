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
    return pd.read_sql(query, engine)


def build_summary_card(title: str, value: str):
    return html.Div(
        [
            html.H4(title, style={"marginBottom": "10px"}),
            html.P(value, style={"fontSize": "28px", "fontWeight": "bold", "margin": "0"}),
        ],
        style={
            "padding": "20px",
            "border": "1px solid #ddd",
            "borderRadius": "12px",
            "minWidth": "220px",
            "backgroundColor": "#fafafa",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
        },
    )


app = Dash(__name__)
app.title = "People Analytics Dashboard"

app.layout = html.Div(
    style={"fontFamily": "Arial", "margin": "20px"},
    children=[
        html.H1("People Analytics Dashboard"),
        html.P("Churn prediction monitoring and management view"),

        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr 1fr auto",
                "gap": "20px",
                "alignItems": "end",
                "marginBottom": "20px",
            },
            children=[
                html.Div(
                    [
                        html.Label("Risk Filter"),
                        dcc.Dropdown(
                            id="risk-filter",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "High", "value": "high"},
                                {"label": "Medium", "value": "medium"},
                                {"label": "Low", "value": "low"},
                            ],
                            value="all",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label("Department Filter"),
                        dcc.Dropdown(
                            id="department-filter",
                            options=[],
                            value="all",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label("Minimum Churn Probability"),
                        dcc.Slider(
                            id="probability-slider",
                            min=0.0,
                            max=1.0,
                            step=0.05,
                            value=0.0,
                            marks={
                                0.0: "0.0",
                                0.2: "0.2",
                                0.4: "0.4",
                                0.6: "0.6",
                                0.8: "0.8",
                                1.0: "1.0",
                            },
                        ),
                    ]
                ),
                html.Button("Refresh Data", id="refresh-button", n_clicks=0, style={"height": "40px"}),
            ],
        ),

        dcc.Interval(id="auto-refresh", interval=30 * 1000, n_intervals=0),

        html.Div(id="summary-cards", style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),

        html.Br(),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                dcc.Graph(id="risk-label-chart"),
                dcc.Graph(id="department-risk-chart"),
            ],
        ),

        html.Br(),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"},
            children=[
                dcc.Graph(id="probability-histogram"),
                dcc.Graph(id="department-volume-chart"),
            ],
        ),

        html.Br(),

        html.H3("Top 10 Highest-Risk Predictions"),
        dash_table.DataTable(
            id="top-risk-table",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontFamily": "Arial",
                "fontSize": "14px",
            },
            style_header={"fontWeight": "bold"},
        ),

        html.Br(),

        html.H3("Filtered Prediction Log"),
        dash_table.DataTable(
            id="predictions-table",
            page_size=12,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontFamily": "Arial",
                "fontSize": "14px",
            },
            style_header={"fontWeight": "bold"},
            filter_action="native",
            sort_action="native",
        ),
    ],
)


@app.callback(
    Output("department-filter", "options"),
    Output("department-filter", "value"),
    Input("refresh-button", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
)
def populate_department_filter(_, __):
    df = load_prediction_logs()

    if df.empty:
        return [{"label": "All", "value": "all"}], "all"

    departments = sorted(df["department_name"].dropna().unique().tolist())
    options = [{"label": "All", "value": "all"}] + [
        {"label": dept, "value": dept} for dept in departments
    ]
    return options, "all"


@app.callback(
    Output("summary-cards", "children"),
    Output("risk-label-chart", "figure"),
    Output("department-risk-chart", "figure"),
    Output("probability-histogram", "figure"),
    Output("department-volume-chart", "figure"),
    Output("top-risk-table", "data"),
    Output("top-risk-table", "columns"),
    Output("predictions-table", "data"),
    Output("predictions-table", "columns"),
    Input("refresh-button", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
    Input("risk-filter", "value"),
    Input("department-filter", "value"),
    Input("probability-slider", "value"),
)
def update_dashboard(_, __, risk_filter, department_filter, min_probability):
    df = load_prediction_logs()

    if df.empty:
        empty_fig = px.bar(title="No data yet")
        return (
            [html.Div("No prediction data yet.")],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            [],
            [],
            [],
            [],
        )

    filtered_df = df.copy()

    if risk_filter != "all":
        filtered_df = filtered_df[filtered_df["churn_risk_label"] == risk_filter]

    if department_filter != "all":
        filtered_df = filtered_df[filtered_df["department_name"] == department_filter]

    filtered_df = filtered_df[filtered_df["churn_probability"] >= min_probability]

    if filtered_df.empty:
        empty_fig = px.bar(title="No data for selected filters")
        return (
            [
                build_summary_card("Total Predictions", "0"),
                build_summary_card("Average Churn Risk", "0"),
                build_summary_card("High Risk Count", "0"),
                build_summary_card("Selected Department", str(department_filter)),
            ],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            [],
            [],
            [],
            [],
        )

    total_predictions = len(filtered_df)
    avg_risk = round(filtered_df["churn_probability"].mean(), 4)
    high_risk_count = int((filtered_df["churn_risk_label"] == "high").sum())
    selected_department = department_filter if department_filter != "all" else "All"

    summary_cards = [
        build_summary_card("Total Predictions", str(total_predictions)),
        build_summary_card("Average Churn Risk", str(avg_risk)),
        build_summary_card("High Risk Count", str(high_risk_count)),
        build_summary_card("Selected Department", selected_department),
    ]

    risk_counts = (
        filtered_df["churn_risk_label"]
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
        filtered_df.groupby("department_name", as_index=False)["churn_probability"]
        .mean()
        .sort_values("churn_probability", ascending=False)
    )

    dept_fig = px.bar(
        dept_risk,
        x="department_name",
        y="churn_probability",
        title="Average Churn Probability by Department",
    )

    histogram_fig = px.histogram(
        filtered_df,
        x="churn_probability",
        nbins=20,
        title="Churn Probability Distribution",
    )

    dept_volume = (
        filtered_df.groupby("department_name", as_index=False)
        .size()
        .sort_values("size", ascending=False)
    )

    dept_volume_fig = px.bar(
        dept_volume,
        x="department_name",
        y="size",
        title="Prediction Volume by Department",
    )

    top_risk_df = (
        filtered_df.sort_values(["churn_probability", "created_at"], ascending=[False, False])
        .head(10)
        .copy()
    )
    top_risk_df["created_at"] = top_risk_df["created_at"].astype(str)

    top_columns = [{"name": col, "id": col} for col in top_risk_df.columns]
    top_data = top_risk_df.to_dict("records")

    table_df = filtered_df.copy()
    table_df["created_at"] = table_df["created_at"].astype(str)

    table_columns = [{"name": col, "id": col} for col in table_df.columns]
    table_data = table_df.to_dict("records")

    return (
        summary_cards,
        risk_fig,
        dept_fig,
        histogram_fig,
        dept_volume_fig,
        top_data,
        top_columns,
        table_data,
        table_columns,
    )


if __name__ == "__main__":
    app.run(debug=True, port=8050)