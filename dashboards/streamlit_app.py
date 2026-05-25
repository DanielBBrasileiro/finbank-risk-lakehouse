import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from src.ai_assistant.app import build_risk_agent

load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="FinBank Risk Lakehouse | Intelligence Suite",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Premium Look ---
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_engine():
    db_target = os.getenv("DB_TARGET", "").lower()
    duckdb_file = Path("data/warehouse.duckdb")

    if db_target == "duckdb" and duckdb_file.exists():
        return create_engine(f"duckdb:///{duckdb_file}")

    user = os.getenv("POSTGRES_USER", "finbank")
    password = os.getenv("POSTGRES_PASSWORD", "finbank")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "finbank")

    try:
        # Try connecting to Postgres
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
        # Test the connection quickly
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as postgres_err:
        if duckdb_file.exists():
            st.sidebar.warning("Postgres connection failed. Falling back to local DuckDB.")
            return create_engine(f"duckdb:///{duckdb_file}")
        else:
            raise postgres_err


@st.cache_data(ttl=300)
def read_sql(query: str) -> pd.DataFrame:
    try:
        engine = get_engine()
        # For DuckDB, SQLAlchemy connection may require running raw connection or pandas compatibility
        # pd.read_sql works nicely with duckdb SQLAlchemy engine
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return pd.DataFrame()


# --- AI Assistant Initialization ---
if "agent" not in st.session_state:
    try:
        st.session_state.agent = build_risk_agent()
    except Exception as e:
        st.sidebar.error(f"AI Assistant offline: {e}")

# --- Sidebar: AI Chat ---
with st.sidebar:
    st.title("🤖 Risk Advisor")
    st.caption("Governed copilot: offline demo or configured LLM provider")

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
                st.error("The governed risk copilot is currently unavailable.")

# --- Main Dashboard ---
st.title("🎯 FinBank Risk Lakehouse")
st.markdown("---")

# Load Data
exposure = read_sql("select * from analytics_marts.mart_customer_exposure")
transactions = read_sql("select * from analytics_marts.mart_daily_transactions")
account_health = read_sql("select * from analytics_marts.mart_account_health")

if not exposure.empty:
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Credit Risk & Exposure", "💸 Transaction Monitoring", "🏦 Account Health", "🛡️ AI Governance & Ops"]
    )

    with tab1:
        # --- Top KPIs ---
        col1, col2, col3, col4 = st.columns(4)

        total_customers = exposure["customer_id"].nunique()
        total_balance = exposure["total_outstanding_balance"].sum()
        high_risk_count = exposure[exposure["portfolio_status"].isin(["HIGH_RISK", "DEFAULT_RISK"])][
            "customer_id"
        ].nunique()
        avg_dpd = exposure["avg_days_past_due"].mean()

        col1.metric("Active Customers", f"{total_customers:,}")
        col2.metric("Portfolio Exposure", f"R$ {total_balance / 1e6:.1f}M")
        col3.metric(
            "Critical Exposure",
            f"{high_risk_count:,}",
            delta=f"{(high_risk_count / total_customers) * 100:.1f}% of total",
            delta_color="inverse",
        )
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
                    "PERFORMING": "#00CC96",
                    "WATCHLIST": "#636EFA",
                    "HIGH_RISK": "#EF553B",
                    "DEFAULT_RISK": "#AB63FA",
                },
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
                    "PERFORMING": "#00CC96",
                    "WATCHLIST": "#636EFA",
                    "HIGH_RISK": "#EF553B",
                    "DEFAULT_RISK": "#AB63FA",
                },
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        # --- Transaction Timeline ---
        st.markdown("### 💸 Transactional Intelligence")
        if not transactions.empty:
            daily = transactions.groupby("transaction_date", as_index=False).agg(
                {"total_amount": "sum", "suspicious_count": "sum"}
            )

            fig_line = go.Figure()
            fig_line.add_trace(
                go.Scatter(
                    x=daily["transaction_date"],
                    y=daily["total_amount"],
                    name="Volume (R$)",
                    line=dict(color="#636EFA", width=3),
                )
            )
            fig_line.add_trace(
                go.Bar(
                    x=daily["transaction_date"],
                    y=daily["suspicious_count"]
                    * (
                        daily["total_amount"].max() / daily["suspicious_count"].max()
                        if daily["suspicious_count"].max() > 0
                        else 1
                    ),
                    name="Suspicious (Normalized)",
                    opacity=0.3,
                    marker_color="#EF553B",
                )
            )

            fig_line.update_layout(
                title="Transaction Volume vs Suspicious Activity",
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No transaction data available.")

        # Real-time suspicious summary
        st.markdown("---")
        st.markdown("### 📡 Real-Time Suspicious Ingestion Alerts (Redpanda / local fallback)")

        streaming_summary = read_sql("select * from raw.streaming_suspicious_summary")
        if not streaming_summary.empty:
            s_col1, s_col2 = st.columns([1, 2])
            with s_col1:
                st.metric("Customers Under Alert", f"{len(streaming_summary):,}")
                st.metric(
                    "Flagged Ingress Volume", f"R$ {streaming_summary['total_suspicious_amount'].sum():,.2f}"
                )
            with s_col2:
                top_flagged = streaming_summary.sort_values("suspicious_count", ascending=False).head(5)
                st.write("**Top 5 Flagged Customers under Investigation**")
                st.dataframe(
                    top_flagged.rename(
                        columns={
                            "customer_id": "Customer ID",
                            "suspicious_count": "Alert Count",
                            "total_suspicious_amount": "Total Flagged (R$)",
                            "last_suspicious_timestamp": "Last Alert",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
        else:
            st.info(
                "No real-time suspicious streaming events received yet. Run `make streaming-demo` to simulate live stream ingestion."
            )

    with tab3:
        st.markdown("### 🏦 Account Health Intelligence")

        if not account_health.empty:
            h_col1, h_col2, h_col3, h_col4 = st.columns(4)

            total_customers_ah = account_health["customer_id"].nunique()
            avg_active_ratio = account_health["active_ratio_pct"].mean()
            blocked_customers = len(
                account_health[
                    account_health["account_health_status"].isin(["FULLY_BLOCKED", "PARTIALLY_BLOCKED"])
                ]
            )
            total_accounts_sum = int(account_health["total_accounts"].sum())

            h_col1.metric("Customers", f"{total_customers_ah:,}")
            h_col2.metric("Avg Active Ratio", f"{avg_active_ratio:.1f}%")
            h_col3.metric(
                "Blocked Customers",
                f"{blocked_customers:,}",
                delta=f"{(blocked_customers / total_customers_ah) * 100:.1f}% of total" if total_customers_ah > 0 else "0%",
                delta_color="inverse",
            )
            h_col4.metric("Total Accounts", f"{total_accounts_sum:,}")

            ah1, ah2 = st.columns([2, 1])

            with ah1:
                st.subheader("Account Health by Segment")
                fig_ah_bar = px.bar(
                    account_health.groupby(["segment", "account_health_status"], as_index=False)
                    .agg(customer_count=("customer_id", "count")),
                    x="segment",
                    y="customer_count",
                    color="account_health_status",
                    title="Account Health Status by Segment",
                    template="plotly_dark",
                    color_discrete_map={
                        "HEALTHY": "#00CC96",
                        "PARTIALLY_BLOCKED": "#FFA15A",
                        "FULLY_BLOCKED": "#EF553B",
                        "ALL_CLOSED": "#636EFA",
                    },
                )
                st.plotly_chart(fig_ah_bar, use_container_width=True)

            with ah2:
                st.subheader("Health Distribution")
                fig_ah_pie = px.pie(
                    account_health,
                    names="account_health_status",
                    hole=0.4,
                    template="plotly_dark",
                    color="account_health_status",
                    color_discrete_map={
                        "HEALTHY": "#00CC96",
                        "PARTIALLY_BLOCKED": "#FFA15A",
                        "FULLY_BLOCKED": "#EF553B",
                        "ALL_CLOSED": "#636EFA",
                    },
                )
                st.plotly_chart(fig_ah_pie, use_container_width=True)

            st.markdown("---")
            st.markdown("### 📋 Active Ratio by State")
            fig_ah_state = px.box(
                account_health,
                x="state",
                y="active_ratio_pct",
                title="Active Account Ratio Distribution by State",
                template="plotly_dark",
                color_discrete_sequence=["#636EFA"],
            )
            st.plotly_chart(fig_ah_state, use_container_width=True)
        else:
            st.info("No account health data available. Run `make pipeline` and `make dbt` first.")

    with tab4:
        st.subheader("🛡️ Governed AI Copilot Audit Trail")
        st.markdown(
            "This tab provides transparency into the AI Copilot safety, "
            "showing which questions were processed, which files were retrieved, and which queries were blocked by guardrails."
        )

        # Helper to read audit log
        def read_audit_logs() -> pd.DataFrame:
            import json

            # 1. Try DB
            db_df = read_sql("select * from analytics_marts.mart_ai_copilot_audit")
            if not db_df.empty:
                return db_df
            # 2. Try JSONL File
            audit_file = Path(os.getenv("AI_AUDIT_PATH", "data/ai_audit/copilot_audit.jsonl"))
            if audit_file.exists() and audit_file.stat().st_size > 0:
                records = []
                with audit_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
                df = pd.DataFrame(records)
                if not df.empty:
                    df["citations"] = df["citations"].apply(
                        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
                    )
                    df = df.rename(columns={"timestamp": "audit_timestamp"})
                    df["audit_timestamp"] = pd.to_datetime(df["audit_timestamp"])
                    return df
            return pd.DataFrame()

        audits = read_audit_logs()

        if not audits.empty:
            # Metrics
            a1, a2, a3 = st.columns(3)
            total_queries = len(audits)
            rejected_queries = len(audits[audits["status"] == "rejected"])
            rejection_rate = (rejected_queries / total_queries) * 100 if total_queries > 0 else 0.0

            a1.metric("Total AI Queries", f"{total_queries:,}")
            a2.metric(
                "Blocked by Guardrails",
                f"{rejected_queries:,}",
                delta=f"{rejection_rate:.1f}% block rate",
                delta_color="inverse",
            )
            a3.metric("System Mode", "Governed Hybrid")

            # Rejection vs Answered Chart
            fig_audit = px.bar(
                audits.groupby("status").size().reset_index(name="count"),
                x="status",
                y="count",
                title="Copilot Status Breakdown",
                color="status",
                template="plotly_dark",
                color_discrete_map={"answered": "#00CC96", "rejected": "#EF553B"},
            )
            st.plotly_chart(fig_audit, use_container_width=True)

            # Dataframe
            st.markdown("### 📋 Recent Audited Interactions")
            st.dataframe(
                audits[
                    ["audit_timestamp", "status", "question", "citations", "guarded_sql", "response"]
                ].sort_values("audit_timestamp", ascending=False),
                use_container_width=True,
            )
        else:
            st.info(
                "No audit logs recorded yet. Ask a question to the AI Copilot in the sidebar to populate logs!"
            )

else:
    st.warning("No data found. Please run the ingestion pipeline first.")
