import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from supabase import create_client, Client

# --- 1. CONFIGURATION & LAYOUT ---
st.set_page_config(page_title="Corporate Pulse Command Center", layout="wide")

# --- SIDEBAR: METHODOLOGY (Business Admin Focus) ---
with st.sidebar:
    st.header("📘 Methodology")
    st.markdown("""
    **The Gap Score Formula:**
    Quantifying the divergence between market reality and public perception.
    
    $$ Gap = | P/E - Hype | $$
    
    * **High Gap (>50):** Speculative Risk / Bubble.
    * **Low Gap (<20):** Efficient Market Pricing.
    
    *Data Sources: AlphaVantage (Fundamentals) & News Sentiment Engine.*
    """)
    st.divider()
    st.caption("v2.1 | Analytics Engine Active")

st.title("⚡ The Corporate Pulse Engine")

# Load Secrets
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    n8n_url = st.secrets["N8N_WEBHOOK_URL"]
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception:
    st.error("❌ Secrets missing! Please check Streamlit Cloud settings.")
    st.stop()

# --- 2. FUNCTIONS ---

def get_db_data():
    """Fetch the automated loop data from Supabase"""
    response = supabase.table('pulse_logs').select("*").order('created_at', desc=True).limit(50).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        cols = ['pe_ratio', 'hype_score', 'gap_score']
        for c in cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df

# --- 3. TOP SECTION: LIVE MARKET LOOP (The Graph) ---
st.subheader("📡 Live Market Intelligence")

df = get_db_data()
if not df.empty:
    latest_df = df.sort_values('created_at').drop_duplicates('ticker', keep='last')
    clean_df = latest_df[latest_df['pe_ratio'] > 0].copy()
    
    if not clean_df.empty:
        fig = px.scatter(
            clean_df, x="pe_ratio", y="hype_score", size="gap_score", color="ticker",
            title=f"Monitoring {len(clean_df)} Active Assets",
            labels={"pe_ratio": "Reality (P/E)", "hype_score": "Hype (Sentiment)"},
            size_max=60, height=450
        )
        # Add a reference line for "Average Hype"
        fig.add_shape(type="line", x0=0, y0=50, x1=1000, y1=50, line=dict(color="gray", dash="dot"))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Initializing Database... Data will appear here shortly.")

st.divider()

# --- 4. BOTTOM SECTION: DEEP DIVE (The New Styling) ---
st.subheader("🎯 Strategic Command Center")

col1, col2 = st.columns([1, 2])
with col1:
    target_stock = st.text_input("Target Ticker", value="NVDA").upper()
    run_btn = st.button("🚀 Initiate Analysis")

if run_btn:
    with st.spinner(f'Deciphering signal for {target_stock}...'):
        try:
            # Call n8n
            res = requests.get(n8n_url, params={"ticker": target_stock}, timeout=15)
            
            if res.status_code == 200:
                data = res.json()
                
                # FIX: Map n8n keys (snake_case) to Code variables
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                
                # Safely get values with defaults
                gap = float(data.get('gap_score', 0))
                pe = data.get('pe_ratio', 0)
                hype = data.get('hype_score', 0)
                ticker = data.get('ticker', target_stock)
                news_text = data.get('top_news', "No recent headlines found.")

                # 1. LOGIC: Color Coding the Gap
                if gap > 50:
                    color, msg, d_color = "#ff4b4b", "HIGH DIVERGENCE (Risk)", "inverse"
                elif gap < 20:
                    color, msg, d_color = "#09ab3b", "HEALTHY SYNC", "normal"
                else:
                    color, msg, d_color = "#ffa500", "MODERATE GAP", "off"

                # 2. UI: Display Metrics
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Ticker", ticker)
                c2.metric("Reality (P/E)", pe)
                c3.metric("Emotion (Hype)", f"{hype}%")
                
                with c4:
                    st.markdown(f"""<style>div[data-testid="stMetricValue"] {{ color: {color} !important; }}</style>""", unsafe_allow_html=True)
                    st.metric("Strategic Gap", gap, delta=msg, delta_color=d_color)

                # 3. ANALYTICS UPGRADE: Trend Analysis
                st.divider()
                st.subheader("📈 Historical Trend Analysis")
                
                # Fetch history for this specific ticker
                history_response = supabase.table('pulse_logs')\
                    .select("*")\
                    .eq('ticker', ticker)\
                    .order('created_at', desc=False)\
                    .execute()
                
                hist_df = pd.DataFrame(history_response.data)
                
                if not hist_df.empty and len(hist_df) > 1:
                    # clean dates
                    hist_df['created_at'] = pd.to_datetime(hist_df['created_at'])
                    
                    # Create a dual-line chart
                    fig_hist = px.line(
                        hist_df, 
                        x='created_at', 
                        y=['hype_score', 'gap_score'],
                        title=f"{ticker}: Sentiment vs. Strategic Gap Over Time",
                        labels={"value": "Score (0-100)", "created_at": "Time", "variable": "Metric"},
                        color_discrete_map={"hype_score": "#3498db", "gap_score": "#e74c3c"} # Blue & Red
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                    
                    # Business Insight Logic
                    latest_gap = hist_df.iloc[-