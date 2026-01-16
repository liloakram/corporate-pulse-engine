graph TD
    %% Nodes
    subgraph Ingestion_Layer ["Ingestion Layer (Python & n8n)"]
        A[Python Scripts<br/>yFinance Batch Loader] -->|Raw Data| D[Supabase DB]
        B[n8n Webhook<br/>Live News Scraper] -->|Sentiment Data| D
    end

    subgraph Storage_Layer ["Storage Layer (Supabase PostgreSQL)"]
        D[(pulse_logs<br/>Raw Data Table)]
        D --> E[executive_report<br/>SQL View]
    end

    subgraph Application_Layer ["Application & Presentation Layer"]
        E -->|Read Optimized| F[Looker Studio<br/>Executive Dashboard]
        D -->|Server-Side Filter| G[Streamlit App<br/>Analyst Command Center]
    end

    %% Styles
    classDef ingestion fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef storage fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef app fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;

    class A,B ingestion;
    class D,E storage;
    class F,G app;

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
