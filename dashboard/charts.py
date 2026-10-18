import plotly.express as px
import plotly.graph_objects as go

COLORS = {"APPROVE": "#66765b", "STEP_UP": "#aa7840", "HOLD": "#965460"}
LAYOUT = dict(
    template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Arial, sans-serif", color="#172B4D", size=14),
    xaxis=dict(tickfont=dict(size=13), title_font=dict(size=14)),
    yaxis=dict(tickfont=dict(size=13), title_font=dict(size=14)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=13)),
    margin=dict(l=12, r=12, t=28, b=10),
)

def decision_chart(df):
    if df.empty or "decision" not in df:
        fig = go.Figure()
        fig.update_layout(**LAYOUT, annotations=[dict(text="No API data yet", showarrow=False)])
        return fig
    counts = df.decision.value_counts().reindex(["APPROVE", "STEP_UP", "HOLD"], fill_value=0).rename_axis("Decision").reset_index(name="Count")
    fig = px.pie(counts, names="Decision", values="Count", hole=.64, color="Decision", color_discrete_map=COLORS)
    fig.update_traces(textinfo="percent", textfont_size=12, hovertemplate="%{label}: %{value}<extra></extra>")
    fig.update_layout(**LAYOUT, showlegend=True)
    return fig

def activity_chart(df):
    if df.empty or df["time"].isna().all():
        fig = go.Figure()
        fig.update_layout(**LAYOUT, annotations=[dict(text="No recent transactions from API", showarrow=False)])
        return fig
    grouped = df.dropna(subset=["time"]).set_index("time").resample("5min").size().reset_index(name="Transactions")
    fig = px.area(grouped, x="time", y="Transactions", color_discrete_sequence=["#71566d"])
    fig.update_traces(fill="tozeroy", fillcolor="rgba(113,86,109,.12)", line=dict(width=2), hovertemplate="%{x|%H:%M}<br>%{y} transactions<extra></extra>")
    fig.update_layout(**LAYOUT, showlegend=False, xaxis_title="Time", yaxis_title="Transactions", hovermode="x unified")
    return fig

def amount_by_type(df):
    if df.empty or "type" not in df or "amount" not in df:
        fig = go.Figure()
        fig.update_layout(**LAYOUT, annotations=[dict(text="No recent transactions from API", showarrow=False)])
        return fig
    fig = px.bar(df, x="type", y="amount", color="decision", barmode="group", color_discrete_map=COLORS, labels={"type": "Transaction type", "amount": "Amount (units)", "decision": "Decision"})
    fig.update_layout(**LAYOUT, hovermode="x unified")
    return fig

def latency_chart(df, p95=None):
    fig = go.Figure()
    if not df.empty and df["time"].notna().any():
        ordered = df.dropna(subset=["time"]).sort_values("time")
        for decision in ["APPROVE", "STEP_UP", "HOLD"]:
            part = ordered[ordered.decision == decision]
            if part.empty:
                continue
            fig.add_trace(go.Scatter(x=part.time, y=part.latency_ms, mode="lines+markers", name=decision, line=dict(color=COLORS[decision], width=2), marker=dict(size=5), customdata=part.txn_id, hovertemplate="%{x|%H:%M:%S}<br>%{y:.3f} ms<br>%{customdata}<extra>%{fullData.name}</extra>"))
    if not fig.data:
        fig.add_annotation(text="No recent latency data from API", showarrow=False)
    if p95 is not None:
        fig.add_hline(y=p95, line_dash="dash", line_color="#455a64", annotation_text=f"p95 {p95:.3f} ms", annotation_position="top left")
    fig.update_layout(**LAYOUT, xaxis_title="Time", yaxis_title="Latency (ms)", hovermode="x unified")
    return fig
