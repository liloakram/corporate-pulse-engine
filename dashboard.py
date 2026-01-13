import streamlit as st
import requests

st.set_page_config(page_title="Corporate Pulse Command Center", layout="wide")
st.title("📈 Corporate Pulse: Strategic Command Center")

# --- Sidebar ---
st.sidebar.header("Stock Intelligence")
target_stock = st.sidebar.text_input("Enter Ticker", value="NVDA").upper()

N8N_WEBHOOK_URL = "https://liloakram.app.n8n.cloud/webhook/pulse-data"

if st.sidebar.button('🚀 Run Analysis'):
    with st.spinner(f'Analyzing {target_stock}...'):
        try:
            res = requests.get(N8N_WEBHOOK_URL, params={"ticker": target_stock})
            if res.status_code == 200:
                data = res.json()
                gap = float(data.get('perceptionGap', 0))
                
                # 1. FIXED COLOR LOGIC
                # High Risk (>50): Red
                # Healthy (<20): Green
                # Moderate (20-50): Neutral Gray
                if gap > 50:
                    color, msg, d_color = "#ff4b4b", "HIGH DIVERGENCE", "inverse"
                elif gap < 20:
                    color, msg, d_color = "#09ab3b", "HEALTHY SYNC", "normal"
                else:
                    color, msg, d_color = "#808080", "MODERATE GAP", "off"

                # 2. Main Metrics Row
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Ticker", data.get('ticker'))
                c2.metric("Reality (P/E)", data.get('peRatio'))
                c3.metric("Emotion (Hype)", f"{data.get('hypeScore')}%")
                
                with c4:
                    st.markdown(f"<style>div.st-key-gap [data-testid='stMetricValue'] {{ color: {color} !important; }}</style>", unsafe_allow_html=True)
                    with st.container(key="gap"):
                        st.metric("Strategic Gap", gap, delta=msg, delta_color=d_color)
                
                # 3. News Feed with FIXED BRACKET
                st.divider()
                st.subheader(f"📰 Intelligence Feed: {target_stock}")
                news = data.get('topNews', [])
                if news:
                    for item in news:
                        s = item['sentiment']
                        # Remove any stray brackets and apply color tags
                        clean_s = s.replace("]", "").replace("[", "")
                        
                        if "Bullish" in clean_s:
                            label = f":green[{clean_s}]"
                        elif "Bearish" in clean_s:
                            label = f":red[{clean_s}]"
                        else:
                            label = clean_s # White/Neutral
                            
                        st.markdown(f"**{label}** ({item['impact']} Impact) | [{item['title']}]({item['url']})")
                else:
                    st.info(f"No headlines found for {target_stock} in the last 24 hours.")
            else:
                st.error("Engine Error: API Limit or Connection Failed.")
        except Exception as e:
            st.error(f"Sync Failed: {e}")
