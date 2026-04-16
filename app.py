"""
AEBAS Attendance Dashboard - Streamlit App
Fetches data directly from Zoho Sheets published link.
Auto-refreshes every 30 seconds to reflect Zoho sheet changes.
Usage: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ─── CONFIG ────────────────────────────────────────────────────────────────────
ZOHO_PUBLISHED_URL = "https://sheet.zohopublic.in/sheet/published/wue3rc6a91885551b45f9be4d618515f94991?download=xlsx"
REFRESH_SECONDS = 30
ATTENDANCE_THRESHOLD_GOOD = 0.75
ATTENDANCE_THRESHOLD_AVG = 0.50

st.set_page_config(
    page_title="AEBAS Attendance Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── AUTO-REFRESH (DEPLOYMENT FRIENDLY) ────────────────────────────────────────
# This handles the 30-second refresh without blocking the server thread
st_autorefresh(interval=REFRESH_SECONDS * 1000, key="datarefresh")

# ─── STYLES ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    /* Hide the sidebar button entirely */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        border: 1px solid #e9ecef;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important; border: 1px solid #dee2e6 !important;
        padding: 6px 18px !important; font-weight: 500 !important;
    }
    .file-info { font-size: 13px; color: #6c757d; margin-bottom: 0.5rem; }
    
    /* Stats card section */
    .stats-section-title {
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6c757d;
        margin: 0.2rem 0 0.6rem 0;
    }
    .stats-row {
        display: flex;
        gap: 12px;
        align-items: stretch;
        margin-bottom: 1rem;
    }
    .stats-row-item {
        flex: 1;
        min-width: 0;
        display: flex;
    }
    .stats-card {
        border-radius: 12px;
        padding: 1rem 1.2rem 0.8rem 1.2rem;
        border: 1px solid #e2e8f0;
        width: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        gap: 0;
    }
    .stats-card .sc-icon-wrap {
        width: 36px; height: 36px;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 8px;
    }
    .stats-card .sc-icon-wrap svg { width: 20px; height: 20px; }
    .stats-card .sc-label { font-size: 11px; font-weight: 700; text-transform: uppercase; opacity: 0.7; }
    .stats-card .sc-value { font-size: 24px; font-weight: 800; line-height: 1.15; }
    .stats-card .sc-sub { font-size: 11px; margin-top: auto; padding-top: 6px; opacity: 0.6; }

    /* Color Themes */
    .sc-blue   { background: #eff6ff; border-color: #bfdbfe; color: #1e40af; }
    .sc-blue .sc-icon-wrap { background: #dbeafe; } .sc-blue svg { stroke: #1d4ed8; }
    .sc-green  { background: #f0fdf4; border-color: #bbf7d0; color: #15803d; }
    .sc-green .sc-icon-wrap { background: #dcfce7; } .sc-green svg { stroke: #16a34a; }
    .sc-orange { background: #fff7ed; border-color: #fed7aa; color: #c2410c; }
    .sc-orange .sc-icon-wrap { background: #ffedd5; } .sc-orange svg { stroke: #ea580c; }
    .sc-purple { background: #faf5ff; border-color: #e9d5ff; color: #7e22ce; }
    .sc-purple .sc-icon-wrap { background: #f3e8ff; } .sc-purple svg { stroke: #9333ea; }
    .sc-teal   { background: #f0fdfa; border-color: #99f6e4; color: #0f766e; }
    .sc-teal .sc-icon-wrap { background: #ccfbf1; } .sc-teal svg { stroke: #0d9488; }
    .sc-indigo { background: #eef2ff; border-color: #c7d2fe; color: #3730a3; }
    .sc-indigo .sc-icon-wrap { background: #e0e7ff; } .sc-indigo svg { stroke: #4338ca; }
    .sc-rose   { background: #fff1f2; border-color: #fecdd3; color: #be123c; }
    .sc-rose .sc-icon-wrap { background: #ffe4e6; } .sc-rose svg { stroke: #e11d48; }
</style>
""", unsafe_allow_html=True)

# ─── SVG ICON LIBRARY ──────────────────────────────────────────────────────────
ICONS = {
    "calendar": """<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>""",
    "check_circle": """<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9"/><polyline points="9 12 11.5 14.5 16 10"/></svg>""",
    "hourglass": """<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M5 2h14"/><path d="M5 22h14"/><path d="M5 2l5.5 10L5 22"/><path d="M19 2l-5.5 10L19 22"/></svg>""",
    "bar_chart": """<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/><line x1="2" y1="20" x2="22" y2="20"/></svg>""",
    "clock": """<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15.5 15.5"/></svg>""",
    "book_open": """<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>""",
    "scale": """<svg viewBox="0 0 24 24" fill="none" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><line x1="12" y1="3" x2="12" y2="21"/><path d="M6 21h12"/><path d="M4 6l8-3 8 3"/><path d="M4 6c0 2.21 1.79 4 4 4s4-1.79 4-4"/><path d="M12 6c0 2.21 1.79 4 4 4s4-1.79 4-4"/></svg>""",
}

# ─── DATA LOADING FROM ZOHO ────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_SECONDS)
def load_data_from_zoho(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    excel_bytes = io.BytesIO(response.content)
    sheets = {}
    xl = pd.read_excel(excel_bytes, sheet_name=None, header=0)
    for sheet_name, df in xl.items():
        df = df.dropna(subset=["Name"])
        df = df[df["Name"].notna() & (df["Name"].astype(str).str.strip() != "")]
        date_cols = [c for c in df.columns if isinstance(c, (pd.Timestamp, datetime))]
        numeric_cols = ["No of days present", "No of days Absent", "Total Class Days", "Completed Class Days", "Pending Class Days", "Attendance Percentage", "Planned Hours", "Hours Delivered", "Balance Hours"]
        for dc in date_cols:
            df[dc] = df[dc].astype(str).str.strip().str.upper().replace({"NAN": "-", "": "-"})
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        sheets[sheet_name] = {
            "df": df,
            "date_cols": date_cols,
            "fetched_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        }
    return sheets

def pct_label(pct: float) -> str:
    if pct >= ATTENDANCE_THRESHOLD_GOOD: return "✅ Good"
    elif pct >= ATTENDANCE_THRESHOLD_AVG: return "⚠️ Average"
    return "❌ Low"

def _safe_first(series, fallback=0):
    vals = series.dropna()
    return vals.iloc[0] if len(vals) else fallback

def stats_row_html(cards: list) -> str:
    items = ""
    for icon_key, label, value, sub, theme in cards:
        svg = ICONS.get(icon_key, "")
        items += f"""
        <div class="stats-row-item">
            <div class="stats-card {theme}">
                <div class="sc-icon-wrap">{svg}</div>
                <div class="sc-label">{label}</div>
                <div class="sc-value">{value}</div>
                <div class="sc-sub">{sub}</div>
            </div>
        </div>"""
    return f'<div class="stats-row">{items}</div>'

# ─── PER-SHEET RENDER ──────────────────────────────────────────────────────────
def render_sheet(sheet_data: dict, sheet_name: str):
    df = sheet_data["df"].copy()
    date_cols = sheet_data["date_cols"]

    # Derive stats
    total_students = len(df)
    avg_pct = df["Attendance Percentage"].mean() if "Attendance Percentage" in df.columns else 0
    good_count = int((df["Attendance Percentage"] >= ATTENDANCE_THRESHOLD_GOOD).sum())
    low_count = int((df["Attendance Percentage"] < ATTENDANCE_THRESHOLD_AVG).sum())

    total_class_days = int(_safe_first(df["Total Class Days"])) if "Total Class Days" in df.columns else len(date_cols)
    completed_class_days = int(_safe_first(df["Completed Class Days"])) if "Completed Class Days" in df.columns else 0
    pending_class_days = int(_safe_first(df["Pending Class Days"])) if "Pending Class Days" in df.columns else 0
    planned_hours = int(_safe_first(df["Planned Hours"])) if "Planned Hours" in df.columns else 0
    hours_delivered = int(_safe_first(df["Hours Delivered"])) if "Hours Delivered" in df.columns else 0
    balance_hours = int(_safe_first(df["Balance Hours"])) if "Balance Hours" in df.columns else 0

    avg_pct_display = avg_pct * 100 if avg_pct <= 1.0 else avg_pct

    # Programme Stats Cards
    st.markdown('<p class="stats-section-title">Programme Overview</p>', unsafe_allow_html=True)
    cards = [
        ("calendar", "Total Class Days", str(total_class_days), "Planned", "sc-blue"),
        ("check_circle", "Completed", str(completed_class_days), f"{completed_class_days}/{total_class_days} done", "sc-green"),
        ("hourglass", "Pending", str(pending_class_days), "Remaining", "sc-orange"),
        ("bar_chart", "Avg Attendance", f"{avg_pct_display:.1f}%", "Overall", "sc-purple"),
        ("clock", "Planned Hrs", str(planned_hours), "Total", "sc-teal"),
        ("book_open", "Delivered", str(hours_delivered), "Done", "sc-indigo"),
        ("scale", "Balance", str(balance_hours), "Left", "sc-rose"),
    ]
    st.markdown(stats_row_html(cards), unsafe_allow_html=True)

    # Student KPIs
    st.markdown('<p class="stats-section-title">👥 Student Summary</p>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👥 Total Students", total_students)
    k2.metric("✅ Good (≥75%)", good_count)
    k3.metric("❌ Low (<50%)", low_count)
    k4.metric("⚠️ Average", total_students - good_count - low_count)

    st.markdown("---")

    # Charts Row
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        if date_cols:
            day_data = [{"Date": pd.Timestamp(dc).strftime("%d %b"), "Present": int((df[dc].astype(str).str.upper() == "P").sum()), "Absent": int((df[dc].astype(str).str.upper() == "A").sum())} for dc in date_cols]
            day_df = pd.DataFrame(day_data)
            fig = go.Figure()
            fig.add_bar(x=day_df["Date"], y=day_df["Present"], name="Present", marker_color="#1D9E75")
            fig.add_bar(x=day_df["Date"], y=day_df["Absent"], name="Absent", marker_color="#E24B4A")
            fig.update_layout(title="Daily Attendance Count", barmode="group", height=320, margin=dict(l=0, r=0, t=50, b=0), plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        fig2 = go.Figure(go.Pie(labels=["Good", "Average", "Low"], values=[good_count, (total_students - good_count - low_count), low_count], hole=0.5, marker_colors=["#1D9E75", "#EF9F27", "#E24B4A"]))
        fig2.update_layout(title="Rate Distribution", height=320, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    # Filters and Table
    st.markdown("#### 🔍 Student Details")
    f1, f2, f3 = st.columns([3, 2, 2])
    search = f1.text_input("Search Name", key=f"s_{sheet_name}")
    att_filter = f2.selectbox("Filter Status", ["All", "Good", "Average", "Low"], key=f"f_{sheet_name}")
    sort_by = f3.selectbox("Sort By", ["Name", "Attendance % ↓", "Days Present ↓"], key=f"so_{sheet_name}")

    view_df = df.copy()
    if search: view_df = view_df[view_df["Name"].astype(str).str.contains(search, case=False, na=False)]
    if sort_by == "Attendance % ↓": view_df = view_df.sort_values("Attendance Percentage", ascending=False)
    elif sort_by == "Days Present ↓": view_df = view_df.sort_values("No of days present", ascending=False)
    else: view_df = view_df.sort_values("Name")

    display_rows = [{"Name": str(row["Name"]), "Present": int(row.get("No of days present", 0)), "Absent": int(row.get("No of days Absent", 0)), "Attendance %": f"{row.get('Attendance Percentage', 0)*100:.1f}%", "Status": pct_label(row.get('Attendance Percentage', 0)), "Daily": " ".join(f"{'🟢' if str(row.get(dc, '')).upper() == 'P' else ('🔴' if str(row.get(dc, '')).upper() == 'A' else '⬜')}" for dc in date_cols)} for _, row in view_df.iterrows()]
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, height=400, hide_index=True)

# ─── MAIN APP ──────────────────────────────────────────────────────────────────
def main():
    st.markdown("## 📋 AEBAS Attendance Dashboard")

    with st.spinner("Fetching latest data from Zoho Sheets…"):
        try:
            data = load_data_from_zoho(ZOHO_PUBLISHED_URL)
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
            st.stop()

    first_sheet = next(iter(data.values()))
    fetched_at = first_sheet.get("fetched_at", "—")
    st.markdown(
        f'<div class="file-info">🌐 Source: <code>Zoho Sheets (live)</code> &nbsp;|&nbsp; '
        f'Last fetched: <b>{fetched_at}</b> &nbsp;|&nbsp; '
        f'Auto-refresh: <b>Active ({REFRESH_SECONDS}s)</b></div>',
        unsafe_allow_html=True
    )

    sheet_names = list(data.keys())
    tabs = st.tabs([f"🏫 {s}" for s in sheet_names])

    for tab, sheet_name in zip(tabs, sheet_names):
        with tab:
            render_sheet(data[sheet_name], sheet_name)

    st.markdown("---")
    st.markdown(f'<div style="text-align:center; font-size:12px; color:#adb5bd;">Dashboard auto-refreshes every {REFRESH_SECONDS} seconds.</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()