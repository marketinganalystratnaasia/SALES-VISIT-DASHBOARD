import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from anthropic import Anthropic

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Visit Dashboard",
    page_icon="📊",
    layout="wide",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'DM Serif Display', serif;
}

.main {
    background: #0f1117;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a1d2e 0%, #16192a 100%);
    border: 1px solid rgba(99, 179, 237, 0.2);
    border-radius: 16px;
    padding: 1rem 1.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

[data-testid="metric-container"] label {
    color: #90cdf4 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem !important;
}

/* Section headers */
.section-title {
    font-family: 'DM Serif Display', serif;
    color: #e2e8f0;
    font-size: 1.4rem;
    padding: 0.4rem 0 0.2rem;
    border-bottom: 2px solid #3182ce;
    margin-bottom: 1rem;
}

/* Customer card */
.customer-card {
    background: linear-gradient(135deg, #1a1d2e 0%, #1e2235 100%);
    border: 1px solid rgba(99, 179, 237, 0.15);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}

.customer-card h4 {
    color: #90cdf4;
    font-family: 'DM Serif Display', serif;
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
}

.customer-card p {
    color: #a0aec0;
    margin: 0.2rem 0;
    font-size: 0.85rem;
}

.visit-badge {
    display: inline-block;
    background: #2b6cb0;
    color: #bee3f8;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

/* Chat area */
.chat-header {
    background: linear-gradient(90deg, #1a365d, #2a4365);
    border-radius: 12px 12px 0 0;
    padding: 0.8rem 1.2rem;
    color: #bee3f8;
    font-weight: 600;
    font-family: 'DM Serif Display', serif;
    font-size: 1rem;
}

/* Stagger animation */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}
.anim-1 { animation: fadeSlideIn 0.4s ease both; }
.anim-2 { animation: fadeSlideIn 0.5s 0.08s ease both; }
.anim-3 { animation: fadeSlideIn 0.5s 0.16s ease both; }

/* Selectbox & inputs */
.stSelectbox > div > div {
    background: #1a1d2e !important;
    border-color: rgba(99, 179, 237, 0.3) !important;
    color: #e2e8f0 !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: #1a1d2e;
    border-radius: 10px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #90cdf4;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #2b6cb0 !important;
    color: #fff !important;
}

/* Divider */
hr { border-color: rgba(99,179,237,0.15) !important; }

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    import gspread
    from google.oauth2.service_account import Credentials

    SHEET_ID   = "1rq9myyxJNmu92FxGKVsjH1X_GaKTCEalpwfle0o-roQ"
    SHEET_NAME = "ALL DATA"

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Streamlit Cloud: baca dari secrets. Lokal: baca dari credentials.json
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=scopes
        )
    else:
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=scopes
        )

    client = gspread.authorize(creds)
    sheet  = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data   = sheet.get_all_records()
    df     = pd.DataFrame(data)
    df.columns = df.columns.str.strip()

    # Normalise column names defensively
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "hari" in cl or "tanggal" in cl:
            col_map[c] = "HARI_TANGGAL"
        elif "sales" in cl:
            col_map[c] = "NAMA_SALES"
        elif "customer" in cl:
            col_map[c] = "NAMA_CUSTOMER"
        elif "pic" in cl:
            col_map[c] = "PIC"
        elif "deskripsi" in cl:
            col_map[c] = "DESKRIPSI"
        elif "feedback" in cl:
            col_map[c] = "FEEDBACK"
    df.rename(columns=col_map, inplace=True)

    for col in ["HARI_TANGGAL","NAMA_SALES","NAMA_CUSTOMER","PIC","DESKRIPSI","FEEDBACK"]:
        if col not in df.columns:
            df[col] = ""

    df["NAMA_CUSTOMER"] = df["NAMA_CUSTOMER"].astype(str).str.strip()
    df["NAMA_SALES"]    = df["NAMA_SALES"].astype(str).str.strip()
    df = df[df["NAMA_CUSTOMER"].notna() & (df["NAMA_CUSTOMER"] != "") & (df["NAMA_CUSTOMER"] != "nan")]
    return df


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="anim-1" style="margin-bottom:1.5rem">
  <h1 style="color:#000000; margin:0; font-size:2.2rem">📊 Sales Visit Dashboard</h1>
  <p style="color:#718096; margin:0.3rem 0 0; font-size:0.9rem">
      Data kunjungan sales — Google Sheets · ALL DATA
  </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────
with st.spinner("Mengambil data dari Google Sheets…"):
    try:
        df = load_data()
        load_ok = True
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        load_ok = False

if not load_ok:
    st.stop()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filter Data")

    all_sales = ["Semua"] + sorted(df["NAMA_SALES"].unique().tolist())
    sel_sales = st.selectbox("Sales Person", all_sales)

    # Filter customer list berdasarkan sales yang dipilih
    if sel_sales == "Semua":
        customer_pool = df
    else:
        customer_pool = df[df["NAMA_SALES"] == sel_sales]
    all_customers = ["Semua"] + sorted(customer_pool["NAMA_CUSTOMER"].unique().tolist())
    sel_customer = st.selectbox("Customer", all_customers)

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"<p style='color:#4a5568;font-size:0.75rem'>Total rows: {len(df)}</p>", unsafe_allow_html=True)

# Apply filters
fdf = df.copy()
if sel_sales != "Semua":
    fdf = fdf[fdf["NAMA_SALES"] == sel_sales]
if sel_customer != "Semua":
    fdf = fdf[fdf["NAMA_CUSTOMER"] == sel_customer]


# ─────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────
st.markdown('<div class="anim-2">', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Kunjungan",    len(fdf))
k2.metric("Jumlah Customer",    fdf["NAMA_CUSTOMER"].nunique())
k3.metric("Jumlah Sales",       fdf["NAMA_SALES"].nunique())
k4.metric("Rata-rata Visit/Cust",
          f"{len(fdf)/fdf['NAMA_CUSTOMER'].nunique():.1f}" if fdf["NAMA_CUSTOMER"].nunique() > 0 else "0")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Count of Visit",
    "📅 Visit Timeline",
    "💬 Feedback Summary",
    "🤖 AI Analyst",
])

# ══════════════════════════════════════════════
# TAB 1 — COUNT OF VISIT PER CUSTOMER
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-title">Count of Visit per Customer</p>', unsafe_allow_html=True)

    visit_count = (
        fdf.groupby("NAMA_CUSTOMER")
           .size()
           .reset_index(name="Jumlah Kunjungan")
           .sort_values("Jumlah Kunjungan", ascending=False)
    )

    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        total_customers = len(visit_count)
        if total_customers <= 1:
            top_n = total_customers
            st.info(f"Menampilkan {total_customers} customer.")
        else:
            max_val = min(30, total_customers)
            def_val = min(15, total_customers)
            min_val = 1
            top_n = st.slider("Tampilkan Top N Customer", min_val, max_val, def_val)
        chart_df = visit_count.head(top_n)
        fig = px.bar(
            chart_df,
            x="Jumlah Kunjungan",
            y="NAMA_CUSTOMER",
            orientation="h",
            color="Jumlah Kunjungan",
            color_continuous_scale=["#2b6cb0", "#63b3ed", "#bee3f8"],
            template="plotly_dark",
            labels={"NAMA_CUSTOMER": "Customer", "Jumlah Kunjungan": "Kunjungan"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=10, t=10, b=10),
            coloraxis_showscale=False,
            height=max(300, top_n * 28),
            font=dict(family="DM Sans"),
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.dataframe(
            visit_count.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            height=450,
        )


# ══════════════════════════════════════════════
# TAB 2 — VISIT TIME + SALES PER CUSTOMER
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-title">Visited Time & Sales Person per Customer</p>', unsafe_allow_html=True)

    sel_cust2 = st.selectbox(
        "Pilih Customer",
        sorted(fdf["NAMA_CUSTOMER"].unique().tolist()),
        key="cust2"
    )

    cust_df = fdf[fdf["NAMA_CUSTOMER"] == sel_cust2].copy()
    cust_df = cust_df.reset_index(drop=True)

    total_visits = len(cust_df)
    sales_list   = cust_df["NAMA_SALES"].unique().tolist()

    st.markdown(f"""
    <div class="customer-card anim-1">
        <h4>🏢 {sel_cust2}</h4>
        <span class="visit-badge">{total_visits} kunjungan</span>
        <p>👔 Sales: <strong style="color:#e2e8f0">{', '.join(sales_list)}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # Timeline table
    display_cols = [c for c in ["HARI_TANGGAL", "NAMA_SALES", "PIC", "DESKRIPSI"] if c in cust_df.columns]
    st.dataframe(
        cust_df[display_cols].rename(columns={
            "HARI_TANGGAL": "Tanggal",
            "NAMA_SALES":   "Sales",
            "PIC":          "PIC",
            "DESKRIPSI":    "Deskripsi",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Visit frequency by sales (pie)
    if len(cust_df) > 1:
        sales_share = cust_df.groupby("NAMA_SALES").size().reset_index(name="Count")
        fig2 = px.pie(
            sales_share,
            names="NAMA_SALES",
            values="Count",
            title=f"Proporsi Kunjungan per Sales — {sel_cust2}",
            template="plotly_dark",
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans"),
            margin=dict(t=40, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 3 — FEEDBACK SUMMARY PER CUSTOMER
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-title">Feedback Summary per Customer</p>', unsafe_allow_html=True)

    sel_cust3 = st.selectbox(
        "Pilih Customer",
        sorted(fdf["NAMA_CUSTOMER"].unique().tolist()),
        key="cust3"
    )

    cust_fb = fdf[fdf["NAMA_CUSTOMER"] == sel_cust3].copy()
    feedbacks = cust_fb["FEEDBACK"].dropna().astype(str).str.strip()
    feedbacks = feedbacks[feedbacks != ""]

    if len(feedbacks) == 0:
        st.info("Tidak ada data feedback untuk customer ini.")
    else:
        # Show raw feedbacks
        st.markdown(f"**{len(feedbacks)} feedback ditemukan:**")
        for i, (idx, row) in enumerate(cust_fb.iterrows(), 1):
            fb_text = str(row.get("FEEDBACK","")).strip()
            if fb_text and fb_text != "nan":
                tanggal = str(row.get("HARI_TANGGAL","")).strip()
                sales   = str(row.get("NAMA_SALES","")).strip()
                st.markdown(f"""
                <div class="customer-card" style="border-left: 3px solid #3182ce;">
                    <p style="color:#718096;font-size:0.75rem">#{i} · {tanggal} · {sales}</p>
                    <p style="color:#e2e8f0;font-size:0.9rem">{fb_text}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🤖 AI Summary Feedback")
        st.markdown(
            "*Gunakan tab **AI Analyst** untuk mendapatkan ringkasan otomatis feedback menggunakan Claude AI.*",
            help="Klik tab AI Analyst di atas"
        )


# ══════════════════════════════════════════════
# TAB 4 — AI ANALYST (Claude-powered)
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-title">🤖 AI Analyst — Powered by Claude</p>', unsafe_allow_html=True)
    st.markdown(
        "Tanyakan apa saja tentang data kunjungan sales Anda. "
        "Claude akan menganalisis berdasarkan data yang sudah dimuat.",
        unsafe_allow_html=False
    )

    # Build context string from dataframe
    @st.cache_data(show_spinner=False)
    def build_context(df_hash: int) -> str:
        summary_rows = []
        for cust, grp in df.groupby("NAMA_CUSTOMER"):
            visits = len(grp)
            sales  = ", ".join(grp["NAMA_SALES"].unique().tolist())
            dates  = ", ".join(grp["HARI_TANGGAL"].astype(str).tolist())
            fbs    = " | ".join(grp["FEEDBACK"].dropna().astype(str).str.strip().tolist())
            summary_rows.append(
                f"Customer: {cust} | Kunjungan: {visits} | Sales: {sales} | "
                f"Tanggal: {dates} | Feedback: {fbs}"
            )
        return "\n".join(summary_rows)

    data_context = build_context(hash(str(df.values.tobytes())))

    SYSTEM_PROMPT = f"""Kamu adalah analis sales yang berpengalaman. 
Berikut adalah data kunjungan sales (format: Customer | Jumlah Kunjungan | Sales | Tanggal | Feedback):

{data_context}

Jawab pertanyaan pengguna berdasarkan data di atas. 
Gunakan Bahasa Indonesia. Berikan analisis yang tajam, ringkas, dan actionable.
Jika diminta summarize feedback, kelompokkan tema-tema utama.
"""

    # Init chat history
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []

    # Suggested prompts
    st.markdown("**💡 Contoh pertanyaan:**")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Customer dengan kunjungan terbanyak?"):
            st.session_state.ai_messages.append({"role":"user","content":"Siapa customer dengan jumlah kunjungan terbanyak dan berapa kunjungannya?"})
    with c2:
        if st.button("Ringkasan semua feedback"):
            st.session_state.ai_messages.append({"role":"user","content":"Tolong rangkumkan semua feedback dari seluruh customer. Kelompokkan berdasarkan tema utama."})
    with c3:
        if st.button("Analisis performa tiap sales"):
            st.session_state.ai_messages.append({"role":"user","content":"Analisis performa masing-masing sales person berdasarkan jumlah kunjungan dan feedback yang diterima."})

    # Display messages
    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Tanya sesuatu tentang data kunjungan sales…")
    if user_input:
        st.session_state.ai_messages.append({"role":"user","content":user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Menganalisis…"):
                try:
                    api_key = os.environ.get("ANTHROPIC_API_KEY")
                    if not api_key:
                        st.error("⚠️ ANTHROPIC_API_KEY belum di-set. Tambahkan di file .env")
                        st.stop()
                    client = Anthropic(api_key=api_key)
                    resp = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        system=SYSTEM_PROMPT,
                        messages=st.session_state.ai_messages,
                    )
                    answer = resp.content[0].text
                    st.markdown(answer)
                    st.session_state.ai_messages.append({"role":"assistant","content":answer})
                except Exception as e:
                    err = f"⚠️ Gagal menghubungi Claude API: {e}"
                    st.error(err)
                    st.session_state.ai_messages.append({"role":"assistant","content":err})

    if st.session_state.ai_messages:
        if st.button("🗑️ Reset Chat", type="secondary"):
            st.session_state.ai_messages = []
            st.rerun()
