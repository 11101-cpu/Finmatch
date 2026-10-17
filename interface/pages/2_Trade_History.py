"""
FinMatch - Page 2: Trade History & Audit Log
Inspection of executed matches, execution prices, and CSV persistence
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import FinMatchEngine
from style import apply_custom_style

st.set_page_config(page_title="Trade History | FinMatch", page_icon="📜", layout="wide")

apply_custom_style()

if "engine" not in st.session_state:
    st.session_state.engine = FinMatchEngine()

engine: FinMatchEngine = st.session_state.engine

st.title("📜 Executed Trade History & Audit Ledger")
st.caption("Complete, immutable audit log of all completed transactions executed by the C matching engine.")

if not engine.is_available():
    st.error("C Matching Engine is not loaded.")
    st.stop()

col_filt, col_exp = st.columns([3, 1])
with col_filt:
    symbols = ["ALL", "RELIANCE", "TCS", "INFY", "HDFCBANK", "TATAMOTORS", "SBIN"]
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
    st.info("No trades executed yet. Place compatible Buy and Sell orders on the dashboard to see matches recorded here.")
    st.stop()

df = pd.DataFrame(trades)
df["turnover"] = df["price"] * df["quantity"]

# Metric Cards with high contrast
t_count = len(df)
t_vol = df["quantity"].sum()
t_turnover = df["turnover"].sum()
avg_px = t_turnover / t_vol if t_vol > 0 else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Trades Executed", f"{t_count:,}", "C Ledger Matches")
m2.metric("Total Shares Matched", f"{t_vol:,}", "Cumulative Executed")
m3.metric("Total Turnover", f"₹{t_turnover:,.2f}", "Total Traded Value")
m4.metric("Volume-Weighted Avg Price", f"₹{avg_px:,.2f}", "VWAP Execution")

st.markdown("---")

# Execution Price Timeline Chart with high contrast
st.subheader("📈 Trade Price Execution Sequence")
fig = px.scatter(
    df,
    x="sequence",
    y="price",
    size="quantity",
    color="symbol",
    hover_data=["trade_id", "buy_order_id", "sell_order_id", "quantity", "turnover"],
    labels={"sequence": "Engine Match Sequence", "price": "Execution Price (INR ₹)", "quantity": "Volume"},
    title="Match Execution Price & Size by Sequence",
    template="plotly_dark"
)
fig.update_layout(
    paper_bgcolor="#151924",
    plot_bgcolor="#151924",
    font=dict(color="#f8fafc", size=12),
    height=340,
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(
        title=dict(text="Engine Match Sequence", font=dict(color="#f8fafc", size=12)),
        gridcolor="#28334a",
        tickfont=dict(color="#cbd5e1", size=11)
    ),
    yaxis=dict(
        title=dict(text="Execution Price (INR ₹)", font=dict(color="#f8fafc", size=12)),
        gridcolor="#28334a",
        tickfont=dict(color="#cbd5e1", size=11)
    )
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("📑 Detailed Audit Log")

df_display = df.copy()
df_display["Exec Price"] = df_display["price"].apply(lambda p: f"₹{p:,.2f}")
df_display["Turnover"] = df_display["turnover"].apply(lambda t: f"₹{t:,.2f}")
df_display = df_display[["trade_id", "symbol", "buy_order_id", "sell_order_id", "Exec Price", "quantity", "Turnover", "sequence"]]
df_display.columns = ["Trade ID", "Symbol", "Buy Order ID", "Sell Order ID", "Price", "Quantity", "Turnover", "Sequence"]

st.dataframe(df_display, use_container_width=True, hide_index=True)

# Direct CSV download button
csv_bytes = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Trade History (CSV)",
    data=csv_bytes,
    file_name=f"finmatch_trades_{selected.lower()}.csv",
    mime="text/csv",
)
