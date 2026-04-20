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


def load_batch_prediction_logs() -> pd.DataFrame:
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
        prediction_source,
        created_at
    FROM churn_prediction_logs
    WHERE prediction_source = 'batch'
    ORDER BY created_at DESC
    """
    return pd.read_sql(query, engine)


def load_api_prediction_logs() -> pd.DataFrame:
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
        prediction_source,
        created_at
    FROM churn_prediction_logs
    WHERE prediction_source = 'api'
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


def generate_insights(df: pd.DataFrame) -> list:
    insights = []

    if df.empty:
        return [
            {
                "title": "No data available",
                "action": "Generate predictions through the API or batch scoring process.",
            }
        ]

    dept_risk = df.groupby("department_name")["churn_probability"].mean()
    top_dept = dept_risk.idxmax()
    top_dept_val = round(dept_risk.max(), 4)

    insights.append({
        "title": f"{top_dept} department has highest risk ({top_dept_val})",
        "action": "Investigate workload, compensation, and team conditions in this department."
    })

    low_eng = df[df["engagement_score"] < 3]["churn_probability"].mean()
    high_eng = df[df["engagement_score"] >= 4]["churn_probability"].mean()

    if pd.notna(low_eng) and pd.notna(high_eng) and low_eng > high_eng:
        insights.append({
            "title": "Low engagement strongly increases churn",
            "action": "Launch engagement surveys, 1:1 meetings, and feedback programs."
        })

    high_ot = df[df["overtime_hours_monthly"] > 20]["churn_probability"].mean()
    low_ot = df[df["overtime_hours_monthly"] <= 10]["churn_probability"].mean()

    if pd.notna(high_ot) and pd.notna(low_ot) and high_ot > low_ot:
        insights.append({
            "title": "High overtime is a churn driver",
            "action": "Balance workloads and reduce overtime pressure."
        })

    low_salary = df[df["salary"] < 40000]["churn_probability"].mean()
    high_salary = df[df["salary"] > 70000]["churn_probability"].mean()

    if pd.notna(low_salary) and pd.notna(high_salary) and low_salary > high_salary:
        insights.append({
            "title": "Low salary group has higher churn",
            "action": "Review compensation bands and adjust salary structure."
        })

    no_promo = df[df["promoted_last_2y"] == False]["churn_probability"].mean()
    promo = df[df["promoted_last_2y"] == True]["churn_probability"].mean()

    if pd.notna(no_promo) and pd.notna(promo) and no_promo > promo:
        insights.append({
            "title": "Lack of promotion increases churn",
            "action": "Create clear career progression and promotion plans."
        })

    return insights


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
                            options=[{"label": "All", "value": "all"}],
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

        html.Br(),

        html.H3("Insights"),
        html.Div(
            id="insights-panel",
            style={
                "padding": "15px",
                "border": "1px solid #ddd",
                "borderRadius": "10px",
                "backgroundColor": "#f9f9f9"
            }
        ),

        html.Hr(),
        html.H2("Realtime API Predictions"),

        html.Div(
            id="api-summary-cards",
            style={
                "display": "flex",
                "gap": "15px",
                "marginBottom": "20px",
                "flexWrap": "wrap"
            }
        ),

        dcc.Graph(id="api-risk-distribution-chart"),

        html.H3("Recent API Predictions"),
        dash_table.DataTable(
            id="api-predictions-table",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "8px"},
            style_header={"fontWeight": "bold"},
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
    df = load_batch_prediction_logs()

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
    Output("insights-panel", "children"),
    Output("api-summary-cards", "children"),
    Output("api-risk-distribution-chart", "figure"),
    Output("api-predictions-table", "data"),
    Output("api-predictions-table", "columns"),
    Input("refresh-button", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
    Input("risk-filter", "value"),
    Input("department-filter", "value"),
    Input("probability-slider", "value"),
)
def update_dashboard(_, __, risk_filter, department_filter, min_probability):
    df = load_batch_prediction_logs()

    empty_fig = px.bar(title="No data yet")

    if df.empty:
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
            [html.Div("No insights available yet.")],
            [html.Div("No API prediction data yet.")],
            empty_fig,
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
        no_data_fig = px.bar(title="No data for selected filters")
        api_df = load_api_prediction_logs()

        if not api_df.empty:
            api_total = len(api_df)
            api_high_risk = len(api_df[api_df["churn_risk_label"] == "high"])
            api_avg_prob = round(api_df["churn_probability"].mean(), 4)

            api_summary_cards = [
                build_summary_card("Total API Predictions", str(api_total)),
                build_summary_card("High Risk Predictions", str(api_high_risk)),
                build_summary_card("Avg API Churn Probability", str(api_avg_prob)),
            ]

            api_risk_counts = api_df["churn_risk_label"].value_counts().reset_index()
            api_risk_counts.columns = ["risk_label", "count"]

            api_risk_fig = px.bar(
                api_risk_counts,
                x="risk_label",
                y="count",
                title="API Risk Distribution"
            )

            api_table_df = api_df.copy()
            api_table_df["created_at"] = api_table_df["created_at"].astype(str)
            api_table_data = api_table_df.head(10).to_dict("records")
            api_table_columns = [{"name": col, "id": col} for col in api_table_df.columns]
        else:
            api_summary_cards = [html.Div("No API prediction data yet.")]
            api_risk_fig = no_data_fig
            api_table_data = []
            api_table_columns = []

        return (
            [
                build_summary_card("Total Predictions", "0"),
                build_summary_card("Average Churn Risk", "0"),
                build_summary_card("High Risk Count", "0"),
                build_summary_card("Selected Department", str(department_filter)),
            ],
            no_data_fig,
            no_data_fig,
            no_data_fig,
            no_data_fig,
            [],
            [],
            [],
            [],
            [html.Div("No insights available for selected filters.")],
            api_summary_cards,
            api_risk_fig,
            api_table_data,
            api_table_columns,
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

    risk_counts = filtered_df["churn_risk_label"].value_counts().reset_index()
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

    insights = generate_insights(filtered_df)
    insight_elements = [
        html.Div(
            [
                html.P(item["title"], style={"fontWeight": "bold"}),
                html.P(f"Action: {item['action']}", style={"color": "#555"}),
            ],
            style={
                "marginBottom": "10px",
                "padding": "10px",
                "borderBottom": "1px solid #eee"
            }
        )
        for item in insights
    ]

    api_df = load_api_prediction_logs()

    api_total = len(api_df)
    api_high_risk = len(api_df[api_df["churn_risk_label"] == "high"]) if not api_df.empty else 0
    api_avg_prob = round(api_df["churn_probability"].mean(), 4) if not api_df.empty else 0

    api_summary_cards = [
        build_summary_card("Total API Predictions", str(api_total)),
        build_summary_card("High Risk Predictions", str(api_high_risk)),
        build_summary_card("Avg API Churn Probability", str(api_avg_prob)),
    ]

    if not api_df.empty:
        api_risk_counts = api_df["churn_risk_label"].value_counts().reset_index()
        api_risk_counts.columns = ["risk_label", "count"]

        api_risk_fig = px.bar(
            api_risk_counts,
            x="risk_label",
            y="count",
            title="API Risk Distribution"
        )

        api_table_df = api_df.copy()
        api_table_df["created_at"] = api_table_df["created_at"].astype(str)
        api_table_data = api_table_df.head(10).to_dict("records")
        api_table_columns = [{"name": col, "id": col} for col in api_table_df.columns]
    else:
        api_risk_fig = px.bar(
            pd.DataFrame({"risk_label": [], "count": []}),
            x="risk_label",
            y="count",
            title="API Risk Distribution"
        )
        api_table_data = []
        api_table_columns = []

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
        insight_elements,
        api_summary_cards,
        api_risk_fig,
        api_table_data,
        api_table_columns,
    )


if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0",port=8050)