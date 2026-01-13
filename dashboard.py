import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from supabase import create_client, Client
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Corporate Pulse Command Center", layout="wide")

# Initialize Session State
if 'analyzed_ticker' not in st.session_state:
    st.session_state['analyzed_ticker'] = None
if 'latest_live_data' not in st.session_state:
    st.session_state['latest_live_data'] = None

# --- SIDEBAR: METHODOLOGY ---
with st.sidebar:
    st.header("📘 Methodology")
    st.markdown("""
    **The Gap Score Formula:**
    $$ Gap = | P/E - Hype | $$
    
    **Analyst Signals:**
    * 🔴 **High Risk (>50):** Valuation decoupled from reality.
    * 🟢 **Undervalued (<20):** Strong fundamentals, low hype.
    * ⚪ **Speculative:** Negative earnings (P/E N/A).
    """)
    st.divider()
    st.caption("v4.0 | Business Intelligence Suite")

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

def get_recommendation(gap, pe, hype):
    """Business Logic Engine: Generates Prescriptive Analytics"""
    # Logic based on [cite: 65, 66] - Handle insufficient data
    if pe == 0 or pe == "N/A":
        return "⚠️ SPECULATIVE HOLD", "Earnings are negative or missing. Market sentiment is driving price purely on speculation. High volatility expected.", "#808080"
    
    # Logic based on [cite: 59, 60] - Bubble Risk
    if gap > 50:
        return "🔴 REDUCE EXPOSURE", "The asset is effectively a bubble. Hype has completely detached from fundamental reality. Risk of correction is high.", "#ff4b4b"
    
    # Logic based on [cite: 61, 62] - Value Buy
    if gap < 20:
        return "🟢 VALUE OPPORTUNITY", "Fundamentals are strong relative to market sentiment. The asset may be overlooked or oversold.", "#09ab3b"
    
    # Logic based on [cite: 63, 64] - Hold
    return "🟡 HOLD / NEUTRAL", "Valuation is consistent with market sentiment. No significant inefficiency detected.", "#ffa500"

# --- 3. TOP SECTION: CONTROLS & LIVE LOOP ---

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
        st.session_state['latest_live_data'] = None 
        
        with st.spinner(f"Querying AlphaVantage & N8N Engine (Max 45s)..."):
            try:
                res = requests.get(n8n_url, params={"ticker": target_stock}, timeout=45)
                
                if res.status_code == 200:
                    try:
                        data = res.json()
                        if isinstance(data, list) and len(data) > 0: data = data[0]
                        
                        if data.get('ticker'): 
                            st.success("✅ Live Data Acquired.")
                            st.session_state['latest_live_data'] = data
                        else:
                            st.warning("⚠️ Live Feed Empty. Falling back to database.")
                    except ValueError:
                        st.warning("⚠️ External Data Provider is undergoing maintenance. Displaying cached intelligence.")
                else:
                    st.warning(f"⚠️ Live Feed Unstable ({res.status_code}). Using cached data.")
            except Exception:
                st.warning("⚠️ Live Feed Timeout. Displaying cached intelligence.")

# --- DISPLAY RESULTS ---
if st.session_state['analyzed_ticker']:
    ticker = st.session_state['analyzed_ticker']
    live_data = st.session_state['latest_live_data']
    
    # 1. Fetch History from DB
    hist_df = get_ticker_history(ticker, show_sim)

    # 2. Determine Data Source
    display_data = None
    if live_data:
        display_data = live_data
    elif not hist_df.empty:
        display_data = hist_df.iloc[-1].to_dict()

    # 3. RENDER METRICS
    if display_data:
        # --- PRO DEBUGGER ---
        with st.expander("🕵️‍♂️ View Raw API Data (Debug)"):
            st.json(display_data)

        # --- DATA PARSING ---
        raw_pe = display_data.get('pe_ratio')
        if raw_pe is None: raw_pe = display_data.get('PERatio')
        
        try:
            pe_value = float(raw_pe) if raw_pe is not None else 0.0
        except (ValueError, TypeError):
            pe_value = 0.0
            
        try: hype_value = float(display_data.get('hype_score', 0))
        except: hype_value = 0.0
            
        try: gap_value = float(display_data.get('gap_score', 0))
        except: gap_value = 0.0

        # Logic: Valid vs Invalid P/E
        if pe_value > 0:
            pe_display = round(pe_value, 2)
            if gap_value == 0: gap_value = abs(pe_value - hype_value)
            gap_display = round(gap_value, 2)
        else:
            pe_display = "N/A"
            gap_display = "N/A" 
            pe_value = 0 # Ensure 0 for logic check

        # --- THE RECOMMENDATION ENGINE (New!) ---
        # This function call implements the business logic requested in [cite: 53]
        rec_title, rec_desc, rec_color = get_recommendation(gap_value if gap_display != "N/A" else 0, pe_display, hype_value)

        # Metrics Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ticker", ticker)
        c2.metric("Reality (P/E)", pe_display)
        c3.metric("Emotion (Hype)", f"{hype_value}%")
        with c4:
            st.markdown(f"""<style>div[data-testid="stMetricValue"] {{ color: {rec_color} !important; }}</style>""", unsafe_allow_html=True)
            st.metric("Strategic Gap", gap_display)

        # --- RECOMMENDATION BOX ---
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: rgba(50, 50, 50, 0.2); border-left: 5px solid {rec_color}; margin-top: 20px;">
            <h3 style="color: {rec_color}; margin:0;">{rec_title}</h3>
            <p style="margin:0; font-size: 1.1em;">{rec_desc}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("") # Spacer

        # --- CSV DOWNLOAD (New!) ---
        # Implements the Managerial Hand-off requirement [cite: 75, 78]
        export_df = pd.DataFrame([{
            "Ticker": ticker,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "PE_Ratio": pe_display,
            "Hype_Score": hype_value,
            "Gap_Score": gap_display,
            "Recommendation": rec_title,
            "Headline": display_data.get('top_news', 'N/A')
        }])
        
        csv = export_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download Analyst Report (CSV)",
            data=csv,
            file_name=f"{ticker}_Pulse_Analysis.csv",
            mime="text/csv",
        )

        # News Banner
        st.divider()
        st.caption(f"📰 LATEST INTEL: {ticker}")
        st.success(f"**Headline:** {display_data.get('top_news', 'No headline available.')}")

    else:
        st.error(f"❌ No data available for {ticker}.")

    # 4. RENDER CHART
    if not hist_df.empty:
        hist_df['created_at'] = pd.to_datetime(hist_df['created_at'])
        st.divider()
        st.subheader("📈 Historical Trend Analysis")
        fig_hist = px.line(
            hist_df, x='created_at', y=['hype_score', 'gap_score'],
            title=f"{ticker}: Sentiment vs. Gap (Simulation Mode: {'ON' if show_sim else 'OFF'})",
            color_discrete_map={"hype_score": "#3498db", "gap_score": "#e74c3c"}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    elif live_data:
        st.divider()
        st.info(f"ℹ️ **First Data Point Captured:** This is the first analysis for {ticker}. Trend lines will appear after subsequent runs.")
    else:
        st.info(f"💡 **Demo Tip:** Try **NVDA, TSLA, or AAPL** to see the Simulation Engine in action.")