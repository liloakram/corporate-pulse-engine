import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from supabase import create_client, Client

# --- 1. SETUP ---
st.set_page_config(page_title="Hype vs Reality", layout="wide")
st.title("⚡ The Corporate Pulse Engine")

# Load Secrets (We know these work now!)
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
n8n_url = st.secrets["N8N_WEBHOOK_URL"]
supabase: Client = create_client(supabase_url, supabase_key)

# --- 2. FUNCTIONS ---

def get_db_data():
    """Fetch the automated loop data from Supabase"""
    # NO TRY/EXCEPT HERE -> If this fails, we want to see the error!
    response = supabase.table('pulse_logs').select("*").order('created_at', desc=True).limit(50).execute()
    df = pd.DataFrame(response.data)
    
    if df.empty:
        return pd.DataFrame()
        
    # Convert numbers to floats
    cols = ['pe_ratio', 'hype_score', 'gap_score']
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df

def trigger_n8n_analysis(ticker):
    """Send ticker to n8n Webhook"""
    try:
        # 1. Send Request
        response = requests.get(f"{n8n_url}?ticker={ticker}", timeout=20)
        
        # 2. Check Status
        if response.status_code != 200:
            return None, f"❌ n8n Error ({response.status_code}): {response.text}"
            
        # 3. Parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            return None, f"❌ Invalid JSON from n8n. Raw text: {response.text}"

        # 4. Handle Format (List vs Dict)
        if isinstance(data, list) and len(data) > 0:
            return data[0], None
        elif isinstance(data, dict):
            return data, None
        else:
            return None, "❌ n8n returned empty data."

    except requests.exceptions.Timeout:
        return None, "❌ Timeout: n8n took too long (>20s). Check if the workflow is Active."
    except Exception as e:
        return None, f"❌ Connection Error: {str(e)}"

# --- 3. DASHBOARD LAYOUT ---

# PART A: THE AUTOMATED LOOP
st.subheader("📡 Live Market Loop")

# Fetch Data
df = get_db_data()

if not df.empty:
    # Clean duplicates to show only the latest snapshot per ticker
    latest_df = df.sort_values('created_at').drop_duplicates('ticker', keep='last')
    
    # Filter out bad data (P/E 0)
    clean_df = latest_df[latest_df['pe_ratio'] > 0].copy()
    
    if not clean_df.empty:
        fig = px.scatter(
            clean_df, x="pe_ratio", y="hype_score", size="gap_score", color="ticker", text="ticker",
            title=f"Tracking {len(clean_df)} Active Stocks",
            labels={"pe_ratio": "Reality (P/E)", "hype_score": "Hype (Sentiment)"},
            size_max=60, height=500
        )
        # Add the 'Neutral' line
        fig.add_shape(type="line", x0=0, y0=50, x1=1000, y1=50, line=dict(color="gray", dash="dot"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Data found, but all P/E ratios are 0. (Market closed or bad data?)")
else:
    st.info("Database is empty. Waiting for n8n loop to run...")

st.divider()

# PART B: THE SEARCH BAR
st.subheader("🔍 Deep Dive Analysis (via n8n)")
col1, col2 = st.columns([1, 2])

with col1:
    search_ticker = st.text_input("Enter Ticker (e.g. NFLX)", "").upper()
    run_btn = st.button("Analyze Stock")

if run_btn and search_ticker:
    with st.spinner(f"Contacting n8n 'Fast Lane' for {search_ticker}..."):
        data, error = trigger_n8n_analysis(search_ticker)
        
        if error:
            st.error(error) # Show the error loudly!
        else:
            # Metrics
            pe = data.get('pe_ratio', 0)
            hype = data.get('hype_score', 0)
            gap = data.get('gap_score', 0)
            news = data.get('top_news', 'No news returned')

            m1, m2, m3 = st.columns(3)
            m1.metric("Reality (P/E)", pe)
            m2.metric("Hype Score", hype)
            m3.metric("Gap Score", gap, delta_color="inverse")
            
            st.success(f"**Latest News:** {news}")