"""
2_Trade_History.py - Executed Trade History & Audit Ledger (Groww Light Theme)
Inspection of completed transactions executed by the C11 matching engine.
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import FinMatchEngine
from style import apply_custom_style, render_top_navbar, render_disclaimer, render_navigation_bar, GROWW_GREEN, GROWW_RED
import auth
import market_data

st.set_page_config(page_title="Trade History | FinMatch", page_icon="📜", layout="wide")
apply_custom_style()

if "engine" not in st.session_state:
    st.session_state.engine = FinMatchEngine()

if "user" not in st.session_state:
    st.session_state.user = auth.get_user_by_id(1)

engine: FinMatchEngine = st.session_state.engine
user = st.session_state.user

render_top_navbar(user, active_page="Trade History")
render_navigation_bar(active_page="Trade History")
render_disclaimer()

st.markdown("""
<div style='margin-bottom: 1.25rem;'>
    <div style='font-size: 1.6rem; font-weight: 800; color: #0F172A;'>📜 Executed Trade History & Audit Ledger</div>
    <div style='font-size: 0.88rem; color: #64748B;'>
        Complete, immutable audit log of all completed transactions processed by the C11 matching engine.
    </div>
</div>
""", unsafe_allow_html=True)

if not engine.is_available():
    st.error("C Matching Engine is not loaded.")
    st.stop()

col_filt, col_exp = st.columns([3, 1])
with col_filt:
    symbols = ["ALL"] + list(market_data.STOCKS_CATALOG.keys())
    selected = st.selectbox("Filter Trades by Stock Symbol", symbols, index=0)
    filter_sym = None if selected == "ALL" else selected

with col_exp:
    st.write("")
    st.write("")
    if st.button("💾 Export to CSV Files", use_container_width=True, help="Flush active in-memory orders and trade history to data/ CSV files"):
        os.makedirs("data", exist_ok=True)
        ok = engine.export_csv("data/exported_orders.csv", "data/exported_trades.csv")
        if ok:
            st.success("Successfully exported to `data/exported_orders.csv` and `data/exported_trades.csv`!")
        else:
            st.error("Failed to export records.")

trades = engine.get_recent_trades(filter_sym, max_trades=200)

if not trades:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.info("No trades executed yet. Place compatible Buy and Sell orders on the dashboard to see matches recorded here.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

df = pd.DataFrame(trades)
df["turnover"] = df["price"] * df["quantity"]

# Metric Cards with Groww styling
t_count = len(df)
t_vol = df["quantity"].sum()
t_turnover = df["turnover"].sum()
avg_px = t_turnover / t_vol if t_vol > 0 else 0

st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Trades Executed", f"{t_count:,}", "C Ledger Matches")
m2.metric("Total Shares Matched", f"{t_vol:,}", "Cumulative Executed")
m3.metric("Total Turnover", f"₹{t_turnover:,.2f}", "Total Traded Value")
m4.metric("Volume-Weighted Avg Price", f"₹{avg_px:,.2f}", "VWAP Execution")
st.markdown("</div>", unsafe_allow_html=True)

# Execution Price Timeline Chart with Groww Light theme
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown("#### 📈 Trade Price Execution Sequence")
fig = px.scatter(
    df,
    x="sequence",
    y="price",
    size="quantity",
    color="symbol",
    hover_data=["trade_id", "buy_order_id", "sell_order_id", "quantity", "turnover"],
    labels={"sequence": "Engine Match Sequence", "price": "Execution Price (INR ₹)", "quantity": "Volume"},
    title="Match Execution Price & Size by Sequence",
    color_discrete_sequence=["#00D09C", "#3B82F6", "#8B5CF6", "#F59E0B", "#EC4899", "#10B981"]
)
fig.update_layout(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    height=320,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis=dict(
        title="Engine Match Sequence",
        showgrid=True,
        gridcolor="#F1F5F9",
        tickfont=dict(color="#64748B", size=11)
    ),
    yaxis=dict(
        title="Execution Price (INR ₹)",
        showgrid=True,
        gridcolor="#F1F5F9",
        tickfont=dict(color="#64748B", size=11)
    )
)
st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Full Executions Ledger Table
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown("#### 📋 Detailed Trade Records")
df_display = df.copy()
df_display["price"] = df_display["price"].apply(lambda p: f"₹{p:,.2f}")
df_display["turnover"] = df_display["turnover"].apply(lambda t: f"₹{t:,.2f}")
df_display["quantity"] = df_display["quantity"].apply(lambda q: f"{q:,}")
df_display = df_display[["trade_id", "symbol", "buy_order_id", "sell_order_id", "price", "quantity", "turnover", "sequence"]]
df_display.columns = ["Trade ID", "Symbol", "Buyer Order ID", "Seller Order ID", "Execution Price", "Quantity", "Turnover", "Sequence"]
st.dataframe(df_display, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)
