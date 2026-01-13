import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Corporate Pulse Command Center", layout="wide")

# Initialize Session State
if 'analyzed_ticker' not in st.session_state:
    st.session_state['analyzed_ticker'] = None

# --- SIDEBAR: METHODOLOGY ONLY ---
with st.sidebar:
    st.header("📘 Methodology")
    st.markdown("""
    **The Gap Score Formula:**
    $$ Gap = | P/E - Hype | $$
    * **>50:** Bubble Risk
    * **<20:** Undervalued
    """)
    st.divider()
    st.caption("v3.0 | Portfolio Edition")

st.title("⚡ The Corporate Pulse Engine")

# Load Secrets
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    n8n_url = st.secrets["N8N_WEBHOOK_URL"]
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception:
    st.error("❌ Secrets missing!")
    st.stop()

# --- 2. FUNCTIONS ---

def get_db_data(allow_sim):
    """Fetch global data for the scatter plot"""
    response = supabase.table('pulse_logs').select("*").order('created_at', desc=True).limit(200).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        cols = ['pe_ratio', 'hype_score', 'gap_score']
        for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        if not allow_sim:
            df = df[~df['top_news'].astype(str).str.contains("SIMULATION", na=False)]
    return df

def get_ticker_history(ticker, allow_sim):
    """Fetch specific history for the Deep Dive chart"""
    response = supabase.table('pulse_logs').select("*").eq('ticker', ticker).order('created_at', desc=False).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        cols = ['pe_ratio', 'hype_score', 'gap_score']
        for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        if not allow_sim:
            df = df[~df['top_news'].astype(str).str.contains("SIMULATION", na=False)]
    return df

# --- 3. TOP SECTION: CONTROLS & LIVE LOOP ---

# We move the toggle HERE so it is on the main screen
c_toggle, c_blank = st.columns([1, 4])
with c_toggle:
    show_sim = st.toggle("Include Simulation Data", value=True)

st.subheader("📡 Live Market Intelligence")
global_df = get_db_data(show_sim)

if not global_df.empty:
    latest_df = global_df.sort_values('created_at').drop_duplicates('ticker', keep='last')
    clean_df = latest_df[latest_df['pe_ratio'] > 0].copy()
    if not clean_df.empty:
        fig = px.scatter(
            clean_df, x="pe_ratio", y="hype_score", size="gap_score", color="ticker",
            title=f"Monitoring {len(clean_df)} Active Assets",
            labels={"pe_ratio": "Reality (P/E)", "hype_score": "Hype (Sentiment)"},
            size_max=60, height=450
        )
        fig.add_shape(type="line", x0=0, y0=50, x1=1000, y1=50, line=dict(color="gray", dash="dot"))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Database empty. Toggle 'Include Simulation Data' to see demo.")

st.divider()

# --- 4. BOTTOM SECTION: COMMAND CENTER ---
st.subheader("🎯 Strategic Command Center")

col1, col2 = st.columns([1, 2])
with col1:
    target_stock = st.text_input("Target Ticker", value="NVDA").upper()
    
    if st.button("🚀 Initiate Analysis"):
        st.session_state['analyzed_ticker'] = target_stock 
        
        # LIVE DATA FETCH
        with st.spinner(f"Analyzing {target_stock}..."):
            try:
                res = requests.get(n8n_url, params={"ticker": target_stock}, timeout=5)
                
                # --- UPDATED VALIDATION LOGIC ---
                if res.status_code == 200:
                    try:
                        data = res.json()
                        # Check if the JSON is valid (has a ticker)
                        if isinstance(data, list) and len(data) > 0: data = data[0]
                        
                        if data.get('ticker'): 
                            st.success("✅ Live Data Acquired.")
                        else:
                            st.warning("⚠️ Live Feed Empty. Falling back to database.")
                    
                    except ValueError:
                        # This catches the HTML "Application Error" specifically
                        st.warning("⚠️ External Data Provider is undergoing maintenance. Displaying cached intelligence.")
                else:
                    st.warning(f"⚠️ Live Feed Unstable ({res.status_code}). Using cached data.")
            except Exception:
                st.warning("⚠️ Live Feed Timeout. Displaying cached intelligence.")

# --- DISPLAY RESULTS ---
if st.session_state['analyzed_ticker']:
    ticker = st.session_state['analyzed_ticker']
    
    # Fetch Data
    hist_df = get_ticker_history(ticker, show_sim)

    if not hist_df.empty:
        hist_df['created_at'] = pd.to_datetime(hist_df['created_at'])
        latest = hist_df.iloc[-1]
        
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ticker", ticker)
        c2.metric("Reality (P/E)", latest['pe_ratio'])
        c3.metric("Emotion (Hype)", f"{latest['hype_score']}%")
        
        gap = latest['gap_score']
        if gap > 50: color = "#ff4b4b"
        elif gap < 20: color = "#09ab3b"
        else: color = "#ffa500"
        
        with c4:
            st.markdown(f"""<style>div[data-testid="stMetricValue"] {{ color: {color} !important; }}</style>""", unsafe_allow_html=True)
            st.metric("Strategic Gap", gap)

        # Trend Chart
        st.divider()
        st.subheader("📈 Historical Trend Analysis")
        fig_hist = px.line(
            hist_df, x='created_at', y=['hype_score', 'gap_score'],
            title=f"{ticker}: Sentiment vs. Gap (Simulation Mode: {'ON' if show_sim else 'OFF'})",
            color_discrete_map={"hype_score": "#3498db", "gap_score": "#e74c3c"}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Trend Insight
        latest_gap = hist_df.iloc[-1]['gap_score']
        avg_gap = hist_df['gap_score'].mean()
        if latest_gap > avg_gap * 1.2:
            st.warning(f"⚠️ **Trend Alert:** The Strategic Gap is **20% higher** than average.")
        else:
            st.info(f"✅ **Trend Stability:** The Gap is consistent with historical averages.")
            
        # News
        st.divider()
        st.caption(f"📰 LATEST INTEL: {ticker}")
        st.success(f"**Headline:** {latest['top_news']}")
        
    else:
        # HANDLING FOR NEW STOCKS (like NFLX)
        st.divider()
        st.error(f"❌ No historical data found for {ticker}.")
        st.info(f"💡 **Demo Tip:** Try **NVDA, TSLA, or AAPL** to see the Simulation Engine in action.")