# ⚡ The Corporate Pulse Engine
### Real-Time Market Sentiment & Valuation Divergence Tool

**Live Dashboard:** https://corporate-pulse-engine-l8zwo4qtsz9iezyeiqp83p.streamlit.app/

## 📊 Executive Summary
In modern financial markets, asset prices are often driven by narrative ("Hype") rather than fundamentals ("Reality"). The **Corporate Pulse Engine** is a business intelligence tool designed to quantify this divergence in real-time.

By ingesting unstructured news data and contrasting it against hard financial ratios (P/E), this engine calculates a proprietary **"Strategic Gap Score"** to identify overvalued assets before market correction.

## 🛠 Architecture & Tech Stack
This project utilizes a serverless ETL pipeline to minimize latency and cost:
* **Orchestration:** n8n (AI-driven logic & data transformation)
* **Database:** Supabase (PostgreSQL for time-series persistence)
* **Frontend:** Streamlit (Python-based interactive dashboard)
* **APIs:** AlphaVantage (Market Data) & News Sentiment Engine

## 💡 Key Features
* **Automated "Gap" Analysis:** A custom algorithm ($Gap = |P/E - Sentiment|$) identifies high-risk assets.
* **Temporal Trend Monitoring:** Visualizes how market perception shifts over 24-hour cycles.
* **Volatility Alerts:** Automatically flags when the current gap exceeds historical averages by >20%.

## 📉 Business Use Case
For financial analysts and portfolio managers, this tool serves as an **Early Warning System**.
* *Scenario A:* High Sentiment + Low P/E = **Undervalued Growth Opportunity**
* *Scenario B:* High Sentiment + High P/E = **Speculative Bubble Risk**

---
*Created by Ali Ali*
*Concentration: Business & Data Analytics*
