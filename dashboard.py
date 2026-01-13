import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from supabase import create_client, Client

# --- 1. CONFIGURATION & LAYOUT ---
st.set_page_config(page_title="Corporate Pulse Command Center", layout="wide")

# --- SIDEBAR: CONTROLS & METHODOLOGY ---
with st.sidebar:
    st.header("⚙️ Data Controls")
    # THE TOGGLE: Checked = Show Demo Data, Unchecked = Real Data Only
    show_sim = st.checkbox("Include Simulation Data", value=True, help="Toggle to show historical backtesting data vs. live production data.")
    
    st.divider()
    st.header("📘 Methodology")
    st.markdown("""
    **The Gap Score Formula:**
    $$ Gap = | P/E - Hype | $$
    * **High Gap (>50):** Speculative Risk.
    * **Low Gap (<20):** Efficient Pricing.
    """)
    st.caption("v2.2 | Analytics Engine Active")

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

def get_db_data(allow_sim):
    """Fetch data and filter based on the toggle"""
    # We fetch more rows (200) to ensure we have enough history to show
    response = supabase.table('pulse_logs').select("*").order('created_at', desc=True).limit(200).execute()
    df = pd.DataFrame(response.data)
    
    if not df.empty:
        # Convert numbers
        cols = ['pe_ratio', 'hype_score', 'gap_score']
        for c in cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        # FILTER LOGIC: If checkbox is OFF, hide rows with [SIMULATION] tag
        if not allow_sim:
            df = df[~df['top_news'].astype(str).str.contains("SIMULATION", na=False)]
            
    return df

# --- 3. TOP SECTION: LIVE MARKET LOOP ---
st.subheader("📡 Live Market Intelligence")

df = get_db_data(show_sim)

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
        fig.add_shape(type="line", x0=0, y0=50, x1=1000, y1=50, line=dict(color="gray", dash="dot"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found for current filter.")
else:
    st.info("Database empty. Try enabling Simulation Data.")

st.divider()

# --- 4. BOTTOM SECTION: DEEP DIVE ---
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
                if isinstance(data, list) and len(data) > 0: data = data[0]
                
                # Variables
                gap = float(data.get('gap_score', 0))
                pe = data.get('pe_ratio', 0)
                hype = data.get('hype_score', 0)
                ticker = data.get('ticker', target_stock)
                news_text = data.get('top_news', "No recent headlines.")

                # Colors
                if gap > 50: color, msg, d_color = "#ff4b4b", "HIGH DIVERGENCE", "inverse"
                elif gap < 20: color, msg, d_color = "#09ab3b", "HEALTHY SYNC", "normal"
                else: color, msg, d_color = "#ffa500", "MODERATE GAP", "off"

                # Metrics
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Ticker", ticker)
                c2.metric("Reality (P/E)", pe)
                c3.metric("Emotion (Hype)", f"{hype}%")
                with c4:
                    st.markdown(f"""<style>div[data-testid="stMetricValue"] {{ color: {color} !important; }}</style>""", unsafe_allow_html=True)
                    st.metric("Strategic Gap", gap, delta=msg, delta_color=d_color)

                # --- TREND CHART (Uses the Toggle) ---
                st.divider()
                st.subheader("📈 Historical Trend Analysis")
                
                # Filter the HISTORY based on the toggle as well
                hist_df = df[df['ticker'] == ticker].sort_values('created_at')
                
                if not hist_df.empty and len(hist_df) > 1:
                    hist_df['created_at'] = pd.to_datetime(hist_df['created_at'])
                    
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
                else:
                    st.caption("Not enough data points for a trend line yet.")

                st.success(f"**Latest Headline:** {news_text}")

            else:
                st.error(f"Engine Error: {res.status_code}")
        except Exception as e:
            st.error(f"Sync Failed: {e}")