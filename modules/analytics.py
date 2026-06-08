"""
Analytics module: computes aggregated metrics and builds Plotly charts
from the meetings stored in the database.
"""

import json
import logging
from collections import Counter
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# ── Brand palette ──────────────────────────────────────────────────────────────
COLOR_PRIMARY = "#6366F1"   # indigo
COLOR_ACCENT  = "#22D3EE"   # cyan
COLOR_SUCCESS = "#10B981"   # emerald
COLOR_WARNING = "#F59E0B"   # amber
COLOR_DANGER  = "#EF4444"   # red
COLOR_BG      = "#0F172A"   # slate-900
COLOR_SURFACE = "#1E293B"   # slate-800
COLOR_TEXT    = "#F1F5F9"   # slate-100

PALETTE = [COLOR_PRIMARY, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER,
           "#A855F7", "#FB923C", "#34D399", "#60A5FA", "#F472B6"]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLOR_TEXT, family="DM Sans, sans-serif"),
    margin=dict(l=16, r=16, t=40, b=16),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


# ── Metric helpers ─────────────────────────────────────────────────────────────

def compute_summary_metrics(meetings: list[dict]) -> dict[str, int]:
    """Return high-level KPI counts across all stored meetings."""
    total_tasks = 0
    total_decisions = 0
    total_deadlines = 0

    for m in meetings:
        total_tasks      += len(_safe_json(m.get("action_items", "[]")))
        total_decisions  += len(_safe_json(m.get("decisions",    "[]")))
        total_deadlines  += len(_safe_json(m.get("deadlines",    "[]")))

    return {
        "total_meetings":  len(meetings),
        "total_tasks":     total_tasks,
        "total_decisions": total_decisions,
        "total_deadlines": total_deadlines,
    }


def _safe_json(raw: str) -> list:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# ── Chart builders ─────────────────────────────────────────────────────────────

def chart_meetings_over_time(meetings: list[dict]) -> go.Figure:
    """Line chart: number of meetings uploaded per day."""
    if not meetings:
        return _empty_chart("No meeting data yet")

    dates = [m.get("upload_date", "")[:10] for m in meetings]
    counts = Counter(dates)
    df = pd.DataFrame(sorted(counts.items()), columns=["Date", "Meetings"])

    fig = px.area(
        df, x="Date", y="Meetings",
        title="Meetings Over Time",
        color_discrete_sequence=[COLOR_PRIMARY],
    )
    fig.update_traces(line_color=COLOR_PRIMARY, fillcolor=f"rgba(99,102,241,0.15)")
    fig.update_layout(**CHART_LAYOUT)
    _style_axes(fig)
    return fig


def chart_task_distribution(meetings: list[dict]) -> go.Figure:
    """Horizontal bar chart: tasks per meeting."""
    if not meetings:
        return _empty_chart("No task data yet")

    names, counts = [], []
    for m in meetings:
        names.append(m.get("meeting_name", "Unknown")[:30])
        counts.append(len(_safe_json(m.get("action_items", "[]"))))

    df = pd.DataFrame({"Meeting": names, "Tasks": counts})
    df = df.sort_values("Tasks", ascending=True).tail(10)

    fig = px.bar(
        df, x="Tasks", y="Meeting", orientation="h",
        title="Action Items per Meeting",
        color="Tasks",
        color_continuous_scale=[[0, "#1E293B"], [1, COLOR_PRIMARY]],
    )
    fig.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)
    _style_axes(fig)
    return fig


def chart_decision_frequency(meetings: list[dict]) -> go.Figure:
    """Pie / donut chart: decision count breakdown across top meetings."""
    if not meetings:
        return _empty_chart("No decision data yet")

    names, counts = [], []
    for m in meetings:
        n = len(_safe_json(m.get("decisions", "[]")))
        if n > 0:
            names.append(m.get("meeting_name", "Unknown")[:25])
            counts.append(n)

    if not names:
        return _empty_chart("No decisions detected yet")

    fig = go.Figure(go.Pie(
        labels=names,
        values=counts,
        hole=0.55,
        marker=dict(colors=PALETTE),
        textinfo="label+percent",
        textfont=dict(color=COLOR_TEXT, size=11),
    ))
    fig.update_layout(title="Decision Distribution", **CHART_LAYOUT)
    return fig


def chart_deadline_timeline(meetings: list[dict]) -> go.Figure:
    """Scatter plot: deadline entries across meetings."""
    rows = []
    for m in meetings:
        for dl in _safe_json(m.get("deadlines", "[]")):
            rows.append({
                "Meeting": m.get("meeting_name", "Unknown")[:25],
                "Deadline": dl.get("deadline", "")[:60],
                "Date":     dl.get("date", "TBD"),
            })

    if not rows:
        return _empty_chart("No deadlines detected yet")

    df = pd.DataFrame(rows)

    fig = px.scatter(
        df, x="Date", y="Meeting",
        title="Deadline Timeline",
        hover_data={"Deadline": True},
        color="Meeting",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(marker=dict(size=12, symbol="diamond"))
    fig.update_layout(**CHART_LAYOUT)
    _style_axes(fig)
    return fig


def chart_word_counts(meetings: list[dict]) -> go.Figure:
    """Bar chart: transcript word counts per meeting."""
    if not meetings:
        return _empty_chart("No data yet")

    names = [m.get("meeting_name", "Unknown")[:25] for m in meetings[-10:]]
    words = [m.get("word_count", 0) for m in meetings[-10:]]

    fig = px.bar(
        x=names, y=words,
        title="Transcript Length (Words)",
        labels={"x": "Meeting", "y": "Word Count"},
        color=words,
        color_continuous_scale=[[0, "#1E293B"], [1, COLOR_ACCENT]],
    )
    fig.update_layout(**CHART_LAYOUT, coloraxis_showscale=False)
    _style_axes(fig)
    return fig


# ── Helpers ────────────────────────────────────────────────────────────────────

def _empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color=COLOR_TEXT),
    )
    fig.update_layout(**CHART_LAYOUT)
    return fig


def _style_axes(fig: go.Figure) -> None:
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.05)",
        showline=False, zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.05)",
        showline=False, zeroline=False,
    )
