# 🧠 AI Meeting Intelligence SaaS

> **Automatically transform meeting transcripts into structured business intelligence.**

A production-grade Streamlit application that analyzes meeting transcripts and surfaces summaries, action items, decisions, deadlines, and interactive analytics — all exportable as professional PDF reports.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Smart Summaries** | Extractive NLP summarization using TF-IDF-style sentence scoring |
| **Action Item Extraction** | Detects task assignments with person + task mapping |
| **Decision Tracking** | Identifies business decisions and their surrounding context |
| **Deadline Detection** | Extracts dates, due dates, and time-bound commitments |
| **Analytics Dashboard** | Interactive Plotly charts across all meetings |
| **PDF Report Export** | Branded, professional PDF report generation via ReportLab |
| **SQLite Persistence** | All meetings and analysis stored locally — no external DB needed |

---

## 🖥️ Screenshots

> Upload the `assets/sample_transcript.txt` file to see a fully populated analysis immediately.

**Home Dashboard** — KPI metrics and recent meetings overview  
**Upload Page** — TXT/PDF upload with live progress analysis  
**Meeting Analysis** — Tabbed view: Summary · Tasks · Decisions · Deadlines  
**Analytics Dashboard** — 5 interactive Plotly charts  
**Reports Page** — One-click PDF generation and download  

---

## 🏗️ Architecture

```
meeting-intelligence-saas/
│
├── app.py                        # Streamlit application entry point
├── requirements.txt
├── .streamlit/config.toml        # Streamlit theme configuration
│
├── modules/
│   ├── transcript_parser.py      # TXT/PDF extraction and text cleaning
│   ├── summary_engine.py         # Extractive summarization + topic extraction
│   ├── action_item_extractor.py  # Regex + heuristic task assignment detection
│   ├── decision_tracker.py       # Decision statement detection
│   ├── deadline_detector.py      # Date and deadline extraction
│   ├── analytics.py              # Plotly chart builders + KPI aggregation
│   └── pdf_generator.py          # ReportLab branded PDF report generator
│
├── database/
│   ├── init_db.py                # SQLite schema management and CRUD helpers
│   └── meetings.db               # Auto-created SQLite database
│
├── assets/
│   └── sample_transcript.txt     # Demo transcript for testing
│
└── reports/                      # Output directory for generated PDFs
```

---

## ⚙️ Tech Stack

- **Frontend**: Streamlit 1.35+
- **Backend**: Python 3.11+
- **NLP**: Custom regex + TF-IDF sentence scoring (no external model dependency)
- **Charts**: Plotly 5.x
- **PDF**: ReportLab 4.x
- **Database**: SQLite (via standard library `sqlite3`)
- **File Parsing**: PyPDF2

---

## 🚀 Installation & Local Development

### Prerequisites
- Python 3.11 or higher
- pip

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/meeting-intelligence-saas.git
cd meeting-intelligence-saas

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 📖 Usage

1. **Upload Transcript** — Navigate to *Upload Transcript*, give your meeting a name, and upload a `.txt` or `.pdf` file.
2. **View Analysis** — Instantly see summary, action items, decisions, and deadlines in the tabbed view.
3. **Browse Meetings** — Use *Meeting Analysis* to review any past meeting.
4. **Explore Analytics** — The *Analytics Dashboard* shows trends across all meetings.
5. **Export PDF** — Go to *Reports* and download a branded PDF report for any meeting.

### Demo
Upload `assets/sample_transcript.txt` immediately after installation to explore all features with pre-populated data.

---

## 🌐 Deployment

### Render (Recommended)

1. Push your repository to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Environment**: Python 3.11
4. Deploy.

> **Note**: The SQLite database is stored on the local filesystem. For production persistence across deploys, consider using a persistent disk volume on Render or migrating to a hosted database.

### Streamlit Community Cloud

1. Push to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set `app.py` as the entry point.
4. Deploy — it's free for public repos.

---

## 🔮 Future Improvements

- [ ] OpenAI / Anthropic Claude integration for abstractive summarization
- [ ] Speaker diarization and sentiment analysis per speaker
- [ ] Export to Google Docs / Notion
- [ ] Slack / Teams webhook integration for action item delivery
- [ ] Multi-user authentication (Supabase or Auth0)
- [ ] Email reminders for detected deadlines
- [ ] Bulk transcript processing pipeline
- [ ] REST API layer (FastAPI) for programmatic access

---

## 📄 License

MIT License — free for personal and commercial use.

---

*Built with Python, Streamlit, Plotly, and ReportLab.*
