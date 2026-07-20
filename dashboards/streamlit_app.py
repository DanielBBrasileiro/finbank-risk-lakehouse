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

# Page config
st.set_page_config(
    page_title="FinBank Risk Lakehouse | Intelligence Suite",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling (glassmorphism cards, typography)
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
    
    /* Metric cards — glassmorphism */
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
        # Postgres first
        engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
        with engine.connect() as conn:  # quick health check
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as postgres_err:
        if duckdb_file.exists():
            st.sidebar.warning("Postgres connection failed. Falling back to local DuckDB.")
            return create_engine(f"duckdb:///{duckdb_file}")
        else:
            raise postgres_err


@st.cache_data(ttl=300)
def read_sql(query: str, *, required: bool = True) -> pd.DataFrame:
    try:
        engine = get_engine()
        return pd.read_sql(query, engine)
    except Exception as exc:
        if required:
            st.error(f"Unable to load a required dashboard dataset: {exc}")
        return pd.DataFrame()


# AI assistant setup
if "agent" not in st.session_state:
    try:
        st.session_state.agent = build_risk_agent()
    except Exception as e:
        st.sidebar.error(f"AI Assistant offline: {e}")

# Sidebar chat
with st.sidebar:
    st.title("Risk Advisor")
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

# Main dashboard
st.title("FinBank Risk Lakehouse")
st.markdown("---")

# Load mart data
exposure = read_sql("select * from analytics_marts.mart_customer_exposure")
transactions = read_sql("select * from analytics_marts.mart_daily_transactions")
account_health = read_sql("select * from analytics_marts.mart_account_health")

if not exposure.empty:
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Credit Risk & Exposure", "💸 Transaction Monitoring", "🏦 Account Health", "🛡️ AI Governance & Ops"]
    )

    with tab1:
        # KPIs
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
        col4.metric("Avg Days Past Due", f"{avg_dpd:.1f} days")

        st.markdown("### Portfolio Insights")

        c1, c2 = st.columns([2, 1])

        # Readable legend labels
        risk_label_map = {
            "PERFORMING": "Performing",
            "WATCHLIST": "Watchlist",
            "HIGH_RISK": "High Risk",
            "DEFAULT_RISK": "Default Risk",
        }

        with c1:
            st.subheader("Exposure by Segment & Risk Level")
            exposure_chart = exposure.copy()
            exposure_chart["Risk Status"] = exposure_chart["portfolio_status"].map(risk_label_map).fillna(exposure_chart["portfolio_status"])
            fig_bar = px.bar(
                exposure_chart,
                x="segment",
                y="total_outstanding_balance",
                color="Risk Status",
                title="Outstanding Balance by Customer Segment",
                labels={
                    "segment": "Customer Segment",
                    "total_outstanding_balance": "Outstanding Balance (R$)",
                    "Risk Status": "Risk Status",
                },
                template="plotly_dark",
                color_discrete_map={
                    "Performing": "#00CC96",
                    "Watchlist": "#636EFA",
                    "High Risk": "#EF553B",
                    "Default Risk": "#AB63FA",
                },
            )
            fig_bar.update_layout(
                yaxis_tickprefix="R$ ",
                yaxis_tickformat=",.0f",
                legend_title_text="Risk Status",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            st.subheader("Risk Distribution")
            exposure_pie = exposure.copy()
            exposure_pie["Risk Status"] = exposure_pie["portfolio_status"].map(risk_label_map).fillna(exposure_pie["portfolio_status"])
            fig_pie = px.pie(
                exposure_pie,
                names="Risk Status",
                values="total_outstanding_balance",
                hole=0.4,
                title="Portfolio Risk Breakdown",
                template="plotly_dark",
                color="Risk Status",
                color_discrete_map={
                    "Performing": "#00CC96",
                    "Watchlist": "#636EFA",
                    "High Risk": "#EF553B",
                    "Default Risk": "#AB63FA",
                },
            )
            fig_pie.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}: R$ %{value:,.2f}<extra></extra>",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        # Transaction timeline
        st.markdown("### Transactional Intelligence")
        if not transactions.empty:
            daily = transactions.groupby("transaction_date", as_index=False).agg(
                {"total_amount": "sum", "suspicious_count": "sum"}
            )

            fig_line = go.Figure()
            fig_line.add_trace(
                go.Scatter(
                    x=daily["transaction_date"],
                    y=daily["total_amount"],
                    name="Transaction Volume (R$)",
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
                    name="Suspicious Activity (scaled)",
                    opacity=0.3,
                    marker_color="#EF553B",
                )
            )

            fig_line.update_layout(
                title="Daily Transaction Volume vs Suspicious Activity",
                xaxis_title="Date",
                yaxis_title="Transaction Volume (R$)",
                yaxis_tickprefix="R$ ",
                yaxis_tickformat=",.0f",
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified",
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No transaction data available.")

        # Streaming alerts
        st.markdown("---")
        st.markdown("### Real-Time Suspicious Ingestion Alerts (Redpanda / Local Fallback)")

        streaming_summary = read_sql("select * from raw.streaming_suspicious_summary", required=False)
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
        st.markdown("### Account Health Intelligence")

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

            h_col1.metric("Total Customers", f"{total_customers_ah:,}")
            h_col2.metric("Avg Active Ratio", f"{avg_active_ratio:.1f}%")
            h_col3.metric(
                "Blocked Customers",
                f"{blocked_customers:,}",
                delta=f"{(blocked_customers / total_customers_ah) * 100:.1f}% of total" if total_customers_ah > 0 else "0%",
                delta_color="inverse",
            )
            h_col4.metric("Total Accounts Managed", f"{total_accounts_sum:,}")

            ah1, ah2 = st.columns([2, 1])

            # Readable legend labels
            health_label_map = {
                "HEALTHY": "Healthy",
                "PARTIALLY_BLOCKED": "Partially Blocked",
                "FULLY_BLOCKED": "Fully Blocked",
                "ALL_CLOSED": "All Closed",
            }

            with ah1:
                st.subheader("Account Health by Segment")
                ah_bar_data = (
                    account_health.groupby(["segment", "account_health_status"], as_index=False)
                    .agg(customer_count=("customer_id", "count"))
                )
                ah_bar_data["Health Status"] = ah_bar_data["account_health_status"].map(health_label_map).fillna(ah_bar_data["account_health_status"])
                fig_ah_bar = px.bar(
                    ah_bar_data,
                    x="segment",
                    y="customer_count",
                    color="Health Status",
                    title="Customer Count by Segment and Health Status",
                    labels={
                        "segment": "Customer Segment",
                        "customer_count": "Number of Customers",
                        "Health Status": "Health Status",
                    },
                    template="plotly_dark",
                    color_discrete_map={
                        "Healthy": "#00CC96",
                        "Partially Blocked": "#FFA15A",
                        "Fully Blocked": "#EF553B",
                        "All Closed": "#636EFA",
                    },
                )
                fig_ah_bar.update_layout(legend_title_text="Health Status")
                st.plotly_chart(fig_ah_bar, use_container_width=True)

            with ah2:
                st.subheader("Health Distribution")
                ah_pie_data = account_health.copy()
                ah_pie_data["Health Status"] = ah_pie_data["account_health_status"].map(health_label_map).fillna(ah_pie_data["account_health_status"])
                fig_ah_pie = px.pie(
                    ah_pie_data,
                    names="Health Status",
                    hole=0.4,
                    title="Account Health Breakdown",
                    template="plotly_dark",
                    color="Health Status",
                    color_discrete_map={
                        "Healthy": "#00CC96",
                        "Partially Blocked": "#FFA15A",
                        "Fully Blocked": "#EF553B",
                        "All Closed": "#636EFA",
                    },
                )
                fig_ah_pie.update_traces(
                    textinfo="percent+label",
                    hovertemplate="%{label}: %{value} customers<extra></extra>",
                )
                st.plotly_chart(fig_ah_pie, use_container_width=True)

            st.markdown("---")
            st.markdown("### Active Ratio by State")
            fig_ah_state = px.box(
                account_health,
                x="state",
                y="active_ratio_pct",
                title="Distribution of Active Account Ratio by State",
                labels={
                    "state": "State (UF)",
                    "active_ratio_pct": "Active Accounts (%)",
                },
                template="plotly_dark",
                color_discrete_sequence=["#636EFA"],
            )
            fig_ah_state.update_layout(
                yaxis_ticksuffix="%",
                xaxis_categoryorder="category ascending",
            )
            st.plotly_chart(fig_ah_state, use_container_width=True)
        else:
            st.info("No account health data available. Run `make pipeline` and `make dbt` first.")

    with tab4:
        st.subheader("Governed AI Copilot Audit Trail")
        st.markdown(
            "This tab provides transparency into the AI Copilot safety, "
            "showing which questions were processed, which files were retrieved, and which queries were blocked by guardrails."
        )

        # Try DB first, then fall back to local JSONL
        def read_audit_logs() -> pd.DataFrame:
            import json

            # DB source
            db_df = read_sql("select * from analytics_marts.mart_ai_copilot_audit", required=False)
            if not db_df.empty:
                return db_df
            # JSONL fallback
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
            # KPIs
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

            # Outcome breakdown chart
            audit_status_labels = {"answered": "Answered", "rejected": "Blocked by Guardrails"}
            audit_chart_data = audits.groupby("status").size().reset_index(name="count")
            audit_chart_data["Status"] = audit_chart_data["status"].map(audit_status_labels).fillna(audit_chart_data["status"])
            fig_audit = px.bar(
                audit_chart_data,
                x="Status",
                y="count",
                title="AI Copilot Query Outcomes",
                labels={
                    "Status": "Query Outcome",
                    "count": "Number of Queries",
                },
                color="Status",
                template="plotly_dark",
                color_discrete_map={"Answered": "#00CC96", "Blocked by Guardrails": "#EF553B"},
            )
            fig_audit.update_layout(legend_title_text="Query Outcome")
            st.plotly_chart(fig_audit, use_container_width=True)

            # Audit log table
            st.markdown("### Recent Audited Interactions")
            st.dataframe(
                audits[
                    ["audit_timestamp", "status", "question", "citations", "guarded_sql", "response"]
                ]
                .rename(
                    columns={
                        "audit_timestamp": "Timestamp",
                        "status": "Status",
                        "question": "Question",
                        "citations": "Citations",
                        "guarded_sql": "Generated SQL",
                        "response": "Response",
                    }
                )
                .sort_values("Timestamp", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No audit logs recorded yet. Ask a question to the AI Copilot in the sidebar to populate logs!"
            )

else:
    st.warning("No data found. Please run the ingestion pipeline first.")
