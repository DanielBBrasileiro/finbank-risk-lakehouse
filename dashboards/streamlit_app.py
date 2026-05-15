import os
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Add src to path for absolute imports
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path / "src"))

from ai_assistant.app import RiskAgent

load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="FinBank Risk Lakehouse | Intelligence Suite",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #0e1117;
    }
    
    /* Glassmorphism card effect */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .stPlotlyChart {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- Database Connection ---
@st.cache_resource
def get_engine():
    user = os.getenv("POSTGRES_USER", "finbank")
    password = os.getenv("POSTGRES_PASSWORD", "finbank")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "finbank")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")

@st.cache_data(ttl=300)
def read_sql(query: str) -> pd.DataFrame:
    try:
        return pd.read_sql(query, get_engine())
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return pd.DataFrame()

# --- AI Assistant Initialization ---
if "agent" not in st.session_state:
    try:
        st.session_state.agent = RiskAgent(model_name="gemma-4-31b-it")
    except Exception as e:
        st.sidebar.error(f"AI Assistant offline: {e}")

# --- Sidebar: AI Chat ---
with st.sidebar:
    st.title("🤖 Risk Advisor")
    st.caption("Powered by Gemma 4 31b-it")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about the risk portfolio..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if "agent" in st.session_state:
                with st.spinner("Analyzing data..."):
                    response = st.session_state.agent.ask(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.error("Gemma 4 is currently unavailable.")

# --- Main Dashboard ---
st.title("🎯 FinBank Risk Lakehouse")
st.markdown("---")

# Load Data
exposure = read_sql("select * from analytics_marts.mart_customer_exposure")
transactions = read_sql("select * from analytics_marts.mart_daily_transactions")

if not exposure.empty:
    # --- Top KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_customers = exposure['customer_id'].nunique()
    total_balance = exposure['total_outstanding_balance'].sum()
    high_risk_count = exposure[exposure['portfolio_status'].isin(['HIGH_RISK', 'DEFAULT_RISK'])]['customer_id'].nunique()
    avg_dpd = exposure['avg_days_past_due'].mean()

    col1.metric("Active Customers", f"{total_customers:,}")
    col2.metric("Portfolio Exposure", f"R$ {total_balance/1e6:.1f}M")
    col3.metric("Critical Exposure", f"{high_risk_count:,}", delta=f"{(high_risk_count/total_customers)*100:.1f}% of total", delta_color="inverse")
    col4.metric("Avg DPD", f"{avg_dpd:.1f} days")

    st.markdown("### 📊 Portfolio Insights")
    
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Exposure by Segment & Risk Level")
        fig_bar = px.bar(
            exposure, 
            x="segment", 
            y="total_outstanding_balance", 
            color="portfolio_status",
            title="Exposure by Segment (Color by Risk Status)",
            template="plotly_dark",
            color_discrete_map={
                'PERFORMING': '#00CC96',
                'WATCHLIST': '#636EFA',
                'HIGH_RISK': '#EF553B',
                'DEFAULT_RISK': '#AB63FA'
            }
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        st.subheader("Risk Distribution")
        fig_pie = px.pie(
            exposure, 
            names="portfolio_status", 
            values="total_outstanding_balance",
            hole=0.4,
            template="plotly_dark",
            color="portfolio_status",
            color_discrete_map={
                'PERFORMING': '#00CC96',
                'WATCHLIST': '#636EFA',
                'HIGH_RISK': '#EF553B',
                'DEFAULT_RISK': '#AB63FA'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- Transaction Timeline ---
    st.markdown("### 💸 Transactional Intelligence")
    if not transactions.empty:
        daily = transactions.groupby("transaction_date", as_index=False).agg({
            "total_amount": "sum",
            "suspicious_count": "sum"
        })
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=daily["transaction_date"], y=daily["total_amount"],
            name="Volume (R$)", line=dict(color='#636EFA', width=3)
        ))
        fig_line.add_trace(go.Bar(
            x=daily["transaction_date"], y=daily["suspicious_count"] * (daily["total_amount"].max() / daily["suspicious_count"].max() if daily["suspicious_count"].max() > 0 else 1),
            name="Suspicious (Normalized)", opacity=0.3, marker_color='#EF553B'
        ))
        
        fig_line.update_layout(
            title="Transaction Volume vs Suspicious Activity",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_line, use_container_width=True)

else:
    st.warning("No data found. Please run the ingestion pipeline first.")
