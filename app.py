"""
AI Meeting Intelligence SaaS — Main Streamlit Application
Entry point: streamlit run app.py
"""

import json
import logging
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

# ── Path setup ─────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ── Internal modules ──────────────────────────────────────────────────────────
from database.init_db import (
    delete_meeting,
    fetch_all_meetings,
    fetch_meeting_by_id,
    initialize_database,
    save_meeting,
)
from modules.action_item_extractor import (
    action_items_from_json,
    action_items_to_json,
    extract_action_items,
)
from modules.analytics import (
    chart_deadline_timeline,
    chart_decision_frequency,
    chart_meetings_over_time,
    chart_task_distribution,
    chart_word_counts,
    compute_summary_metrics,
)
from modules.deadline_detector import (
    deadlines_from_json,
    deadlines_to_json,
    extract_deadlines,
)
from modules.decision_tracker import (
    decisions_from_json,
    decisions_to_json,
    extract_decisions,
)
from modules.pdf_generator import generate_pdf_report
from modules.summary_engine import extract_key_topics, generate_summary
from modules.transcript_parser import parse_transcript

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Streamlit page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Meeting Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Google font */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background: #0F172A;
    color: #F1F5F9;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #1E293B !important;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] .stRadio label {
    color: #CBD5E1 !important;
    font-size: 0.9rem !important;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(99,102,241,0.18);
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #6366F1;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.78rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 4px;
}

/* Section header */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #F1F5F9;
}
.section-badge {
    background: #6366F1;
    color: white;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 999px;
}

/* Card container */
.card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
}

/* Summary text */
.summary-text {
    font-size: 0.95rem;
    line-height: 1.75;
    color: #CBD5E1;
}

/* Topic pill */
.topic-pill {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    color: #818CF8;
    border: 1px solid rgba(99,102,241,0.3);
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    margin: 3px;
}

/* Upload area */
.stFileUploader {
    background: #1E293B !important;
    border: 2px dashed #334155 !important;
    border-radius: 12px !important;
}

/* Tables */
.stDataFrame {
    background: #1E293B;
}
thead tr th {
    background: #6366F1 !important;
    color: white !important;
}
tbody tr:nth-child(even) td {
    background: rgba(255,255,255,0.02) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
    transition: opacity 0.2s;
}
.stButton > button:hover {
    opacity: 0.88;
    color: white;
}

/* Progress bars */
.stProgress > div > div {
    background: #6366F1;
}

/* Expanders */
.streamlit-expanderHeader {
    background: #1E293B !important;
    border-radius: 10px !important;
    color: #F1F5F9 !important;
}

/* Page title */
.page-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #F1F5F9;
    margin-bottom: 4px;
}
.page-desc {
    font-size: 0.9rem;
    color: #64748B;
    margin-bottom: 24px;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid #1E293B;
    margin: 20px 0;
}

/* Toast / info banners */
.info-banner {
    background: rgba(99,102,241,0.1);
    border-left: 3px solid #6366F1;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    color: #CBD5E1;
    font-size: 0.88rem;
    margin-bottom: 12px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0F172A; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Bootstrap DB ──────────────────────────────────────────────────────────────
initialize_database()
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _metric_card(label: str, value: str | int, icon: str = "") -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-value">{icon} {value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def _section_header(title: str, badge: str = "") -> None:
    badge_html = f'<span class="section-badge">{badge}</span>' if badge else ""
    st.markdown(
        f'<div class="section-header">'
        f'<span class="section-title">{title}</span>{badge_html}</div>',
        unsafe_allow_html=True,
    )


def _render_kpi_row(metrics: dict) -> None:
    cols = st.columns(4)
    cards = [
        ("Total Meetings",  metrics["total_meetings"],  "📋"),
        ("Action Items",    metrics["total_tasks"],      "✅"),
        ("Decisions Made",  metrics["total_decisions"],  "🎯"),
        ("Deadlines Tracked", metrics["total_deadlines"], "📅"),
    ]
    for col, (label, value, icon) in zip(cols, cards):
        with col:
            st.markdown(_metric_card(label, value, icon), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

def page_home() -> None:
    """Landing / overview page."""
    st.markdown('<div class="page-title">🧠 AI Meeting Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-desc">Automatically transform meeting transcripts into actionable business intelligence.</div>',
        unsafe_allow_html=True,
    )

    meetings = fetch_all_meetings()
    metrics  = compute_summary_metrics(meetings)
    _render_kpi_row(metrics)

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="card">
            <div style="font-size:1.8rem; margin-bottom:8px;">📝</div>
            <div style="font-weight:600; color:#F1F5F9; margin-bottom:6px;">Smart Summaries</div>
            <div style="font-size:0.85rem; color:#64748B; line-height:1.6;">
            Extractive NLP summarization surfaces the most important discussion points from any length of transcript.
            </div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="card">
            <div style="font-size:1.8rem; margin-bottom:8px;">✅</div>
            <div style="font-weight:600; color:#F1F5F9; margin-bottom:6px;">Task Detection</div>
            <div style="font-size:0.85rem; color:#64748B; line-height:1.6;">
            Automatically identifies who is responsible for what — turning conversation into a structured task list.
            </div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="card">
            <div style="font-size:1.8rem; margin-bottom:8px;">📊</div>
            <div style="font-weight:600; color:#F1F5F9; margin-bottom:6px;">Analytics Dashboard</div>
            <div style="font-size:0.85rem; color:#64748B; line-height:1.6;">
            Track meeting health over time with interactive Plotly charts — decisions, deadlines, participation.
            </div></div>""", unsafe_allow_html=True)

    if meetings:
        st.markdown("<br>", unsafe_allow_html=True)
        _section_header("Recent Meetings", f"{len(meetings)} total")
        df = pd.DataFrame(meetings)[["id", "meeting_name", "upload_date", "word_count", "speaker_count"]]
        df.columns = ["ID", "Meeting Name", "Date", "Words", "Speakers"]
        st.dataframe(df.head(8), use_container_width=True, hide_index=True)


def page_upload() -> None:
    """Transcript upload and analysis page."""
    st.markdown('<div class="page-title">Upload Transcript</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-desc">Upload a TXT or PDF meeting transcript to begin analysis.</div>',
        unsafe_allow_html=True,
    )

    with st.form("upload_form", clear_on_submit=False):
        meeting_name = st.text_input(
            "Meeting Name",
            placeholder="e.g. Q3 Product Strategy — July 2025",
        )
        uploaded_file = st.file_uploader(
            "Upload Transcript",
            type=["txt", "pdf"],
            help="Supported formats: .txt, .pdf",
        )
        submitted = st.form_submit_button("Analyze Transcript", use_container_width=True)

    if submitted:
        if not meeting_name.strip():
            st.error("Please enter a meeting name.")
            return
        if uploaded_file is None:
            st.error("Please upload a transcript file.")
            return

        with st.spinner("Parsing and analyzing transcript…"):
            try:
                # Step 1: Parse
                parsed = parse_transcript(uploaded_file.read(), uploaded_file.name)
                transcript = parsed["clean_text"]

                progress = st.progress(0, text="Parsing transcript…")

                # Step 2: Summary
                progress.progress(20, text="Generating summary…")
                summary = generate_summary(transcript)
                topics  = extract_key_topics(transcript)

                # Step 3: Action items
                progress.progress(40, text="Extracting action items…")
                action_items = extract_action_items(transcript)

                # Step 4: Decisions
                progress.progress(60, text="Detecting decisions…")
                decisions = extract_decisions(transcript)

                # Step 5: Deadlines
                progress.progress(80, text="Detecting deadlines…")
                deadlines = extract_deadlines(transcript)

                # Step 6: Save
                progress.progress(95, text="Saving to database…")
                meeting_id = save_meeting(
                    meeting_name   = meeting_name.strip(),
                    upload_date    = datetime.now().isoformat(),
                    transcript     = transcript,
                    summary        = summary,
                    action_items   = action_items_to_json(action_items),
                    decisions      = decisions_to_json(decisions),
                    deadlines      = deadlines_to_json(deadlines),
                    word_count     = parsed["word_count"],
                    speaker_count  = parsed["speaker_count"],
                )
                progress.progress(100, text="Done!")

                st.success(f"Analysis complete! Meeting saved (ID: {meeting_id})")
                st.session_state["last_analyzed_id"] = meeting_id

                # Preview results
                st.markdown("---")
                _render_analysis_preview(summary, topics, action_items, decisions, deadlines)

            except Exception as exc:
                logger.exception("Analysis failed")
                st.error(f"Analysis failed: {exc}")


def _render_analysis_preview(summary, topics, action_items, decisions, deadlines) -> None:
    """Inline preview of analysis results after upload."""
    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Action Items", "Decisions", "Deadlines"])

    with tab1:
        st.markdown(f'<div class="card"><div class="summary-text">{summary}</div></div>',
                    unsafe_allow_html=True)
        if topics:
            pills = "".join(f'<span class="topic-pill">{t}</span>' for t in topics)
            st.markdown(f"<div style='margin-top:10px;'>{pills}</div>", unsafe_allow_html=True)

    with tab2:
        if action_items:
            df = pd.DataFrame(action_items)
            df.columns = ["Assignee", "Task"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No action items detected.")

    with tab3:
        if decisions:
            df = pd.DataFrame(decisions)
            df.columns = ["Decision", "Context"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No decisions detected.")

    with tab4:
        if deadlines:
            df = pd.DataFrame(deadlines)
            df.columns = ["Deadline Statement", "Date"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No deadlines detected.")


def page_analysis() -> None:
    """Meeting Analysis browser — view any saved meeting."""
    st.markdown('<div class="page-title">Meeting Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-desc">Browse and review detailed analysis for any uploaded meeting.</div>',
        unsafe_allow_html=True,
    )

    meetings = fetch_all_meetings()
    if not meetings:
        st.info("No meetings uploaded yet. Head to **Upload Transcript** to get started.")
        return

    options = {f"[{m['id']}] {m['meeting_name']} — {m['upload_date'][:10]}": m["id"] for m in meetings}
    selected_label = st.selectbox("Select a meeting", list(options.keys()))
    meeting_id = options[selected_label]
    meeting = fetch_meeting_by_id(meeting_id)

    if not meeting:
        st.error("Meeting not found.")
        return

    st.markdown("<br>", unsafe_allow_html=True)

    # Header stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(_metric_card("Words", meeting.get("word_count", 0), "📄"), unsafe_allow_html=True)
    with col2:
        st.markdown(_metric_card("Speakers", meeting.get("speaker_count", 0), "🎙️"), unsafe_allow_html=True)
    with col3:
        st.markdown(_metric_card("Tasks", len(action_items_from_json(meeting.get("action_items", "[]"))), "✅"), unsafe_allow_html=True)
    with col4:
        st.markdown(_metric_card("Decisions", len(decisions_from_json(meeting.get("decisions", "[]"))), "🎯"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Summary", "Action Items", "Decisions", "Deadlines", "Raw Transcript"]
    )

    summary       = meeting.get("summary", "")
    action_items  = action_items_from_json(meeting.get("action_items", "[]"))
    decisions     = decisions_from_json(meeting.get("decisions", "[]"))
    deadlines     = deadlines_from_json(meeting.get("deadlines", "[]"))

    with tab1:
        st.markdown(f'<div class="card"><div class="summary-text">{summary or "No summary available."}</div></div>',
                    unsafe_allow_html=True)

    with tab2:
        if action_items:
            df = pd.DataFrame(action_items)
            df.columns = ["Assignee", "Task"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No action items detected for this meeting.")

    with tab3:
        if decisions:
            df = pd.DataFrame(decisions)
            df.columns = ["Decision", "Context"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No decisions detected for this meeting.")

    with tab4:
        if deadlines:
            df = pd.DataFrame(deadlines)
            df.columns = ["Deadline Statement", "Date"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No deadlines detected for this meeting.")

    with tab5:
        transcript_text = meeting.get("transcript", "Transcript not stored.")
        st.text_area("Transcript", transcript_text, height=400)

    st.markdown("---")
    col_pdf, col_del = st.columns([3, 1])
    with col_pdf:
        if st.button("Generate PDF Report", key="gen_pdf"):
            all_meetings = fetch_all_meetings()
            metrics = compute_summary_metrics(all_meetings)
            pdf_bytes = generate_pdf_report(meeting, metrics)
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"meeting_report_{meeting_id}.pdf",
                mime="application/pdf",
            )
    with col_del:
        if st.button("Delete Meeting", key="del_meeting", type="secondary"):
            delete_meeting(meeting_id)
            st.success("Meeting deleted.")
            st.rerun()


def page_analytics() -> None:
    """Analytics dashboard page."""
    st.markdown('<div class="page-title">Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-desc">Aggregate insights and trends across all your meetings.</div>',
        unsafe_allow_html=True,
    )

    meetings = fetch_all_meetings()
    if not meetings:
        st.info("Upload meetings to see analytics.")
        return

    metrics = compute_summary_metrics(meetings)
    _render_kpi_row(metrics)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_meetings_over_time(meetings), use_container_width=True)
    with col2:
        st.plotly_chart(chart_word_counts(meetings), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(chart_task_distribution(meetings), use_container_width=True)
    with col4:
        st.plotly_chart(chart_decision_frequency(meetings), use_container_width=True)

    st.plotly_chart(chart_deadline_timeline(meetings), use_container_width=True)


def page_reports() -> None:
    """Reports page — bulk PDF generation."""
    st.markdown('<div class="page-title">Reports</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-desc">Generate and download PDF reports for any meeting.</div>',
        unsafe_allow_html=True,
    )

    meetings = fetch_all_meetings()
    if not meetings:
        st.info("No meetings available. Upload a transcript first.")
        return

    options = {f"[{m['id']}] {m['meeting_name']} — {m['upload_date'][:10]}": m["id"] for m in meetings}
    selected_label = st.selectbox("Select meeting for report", list(options.keys()))
    meeting_id = options[selected_label]
    meeting = fetch_meeting_by_id(meeting_id)

    if not meeting:
        st.error("Meeting not found.")
        return

    # Report preview
    st.markdown(f"""
    <div class="card">
        <div style="font-weight:600; color:#F1F5F9; font-size:1rem; margin-bottom:12px;">Report Preview</div>
        <div style="font-size:0.88rem; color:#64748B; line-height:1.8;">
            <b style="color:#CBD5E1;">Meeting:</b> {meeting.get('meeting_name', '')} <br>
            <b style="color:#CBD5E1;">Date:</b> {meeting.get('upload_date', '')[:10]} <br>
            <b style="color:#CBD5E1;">Words:</b> {meeting.get('word_count', 0):,} <br>
            <b style="color:#CBD5E1;">Action Items:</b> {len(action_items_from_json(meeting.get('action_items','[]')))} <br>
            <b style="color:#CBD5E1;">Decisions:</b> {len(decisions_from_json(meeting.get('decisions','[]')))} <br>
            <b style="color:#CBD5E1;">Deadlines:</b> {len(deadlines_from_json(meeting.get('deadlines','[]')))} <br>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Generate PDF Report", use_container_width=True):
        with st.spinner("Building report…"):
            all_meetings = fetch_all_meetings()
            metrics = compute_summary_metrics(all_meetings)
            pdf_bytes = generate_pdf_report(meeting, metrics)

        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"meeting_report_{meeting_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.success("Report ready — click above to download.")


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    with st.sidebar:
        st.markdown("""
        <div style="padding: 12px 0 24px 0;">
            <div style="font-size:1.25rem; font-weight:700; color:#F1F5F9;">🧠 MeetingIQ</div>
            <div style="font-size:0.75rem; color:#475569; margin-top:2px;">AI Meeting Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            options=["Home", "Upload Transcript", "Meeting Analysis", "Analytics Dashboard", "Reports"],
            label_visibility="collapsed",
        )

        st.markdown("<hr style='border-color:#1E293B; margin: 16px 0;'>", unsafe_allow_html=True)

        meetings = fetch_all_meetings()
        st.markdown(f"""
        <div style="font-size:0.78rem; color:#475569; line-height:2;">
            <div>Meetings: <b style="color:#CBD5E1;">{len(meetings)}</b></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.7rem; color:#334155; text-align:center; padding-top:8px;">
            Built with Streamlit · Python<br>
            Powered by NLP & ReportLab
        </div>
        """, unsafe_allow_html=True)

    # Route to selected page
    routing = {
        "Home":                page_home,
        "Upload Transcript":   page_upload,
        "Meeting Analysis":    page_analysis,
        "Analytics Dashboard": page_analytics,
        "Reports":             page_reports,
    }
    routing[page]()


if __name__ == "__main__":
    main()
