"""
FinMatch - Page 1: Order Book Visualizer
In-depth inspection of Buy/Sell Priority Queues and Price Levels
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import FinMatchEngine
from style import apply_custom_style

st.set_page_config(page_title="Order Book | FinMatch", page_icon="📖", layout="wide")

apply_custom_style()

if "engine" not in st.session_state:
    st.session_state.engine = FinMatchEngine()

engine: FinMatchEngine = st.session_state.engine

st.title("📖 Deep Order Book Analytics")
st.caption("Price-Time Priority Queues • Dual Heap Representation (Max-Heap for Bids, Min-Heap for Asks)")

if not engine.is_available():
    st.error("C Matching Engine is not loaded.")
    st.stop()

col_sym, col_refresh = st.columns([3, 1])
with col_sym:
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "TATAMOTORS", "SBIN"]
    symbol = st.selectbox("Select Active Symbol", symbols, index=0)
with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

book = engine.get_order_book(symbol)
stats = engine.get_market_stats(symbol)

bb = stats.get("best_bid")
ba = stats.get("best_ask")
spread = stats.get("spread")

# Summary Bar
c1, c2, c3, c4 = st.columns(4)
c1.metric("Best Bid", f"₹{bb:,.2f}" if bb else "—", "Highest Buy Price")
c2.metric("Best Ask", f"₹{ba:,.2f}" if ba else "—", "Lowest Sell Price")
c3.metric("Spread", f"₹{spread:,.2f}" if spread is not None else "—", "Difference (Ask - Bid)")
c4.metric("Market Depth", f"{book.get('total_bid_vol', 0) + book.get('total_ask_vol', 0):,} shares", "Total Liquidity")

st.markdown("---")

col_bids, col_asks = st.columns(2)
bids = book.get("bids", [])
asks = book.get("asks", [])

with col_bids:
    st.markdown("<h4 style='color:#10b981; border-bottom: 2px solid #10b981; padding-bottom: 4px;'>🟢 BIDS (Max-Heap: Highest Price Priority)</h4>", unsafe_allow_html=True)
    if bids:
        df_bids = pd.DataFrame(bids)
        df_bids["cum_vol"] = df_bids["volume"].cumsum()
        df_bids["price_disp"] = df_bids["price"].apply(lambda p: f"₹{p:,.2f}")
        df_disp_b = df_bids[["price_disp", "volume", "cum_vol", "orders"]].copy()
        df_disp_b.columns = ["Bid Price", "Level Volume", "Cumulative", "Orders"]
        st.dataframe(df_disp_b, use_container_width=True, hide_index=True)
    else:
        st.info("No active buy orders in book.")

with col_asks:
    st.markdown("<h4 style='color:#f43f5e; border-bottom: 2px solid #f43f5e; padding-bottom: 4px;'>🔴 ASKS (Min-Heap: Lowest Price Priority)</h4>", unsafe_allow_html=True)
    if asks:
        df_asks = pd.DataFrame(asks)
        df_asks["cum_vol"] = df_asks["volume"].cumsum()
        df_asks["price_disp"] = df_asks["price"].apply(lambda p: f"₹{p:,.2f}")
        df_disp_a = df_asks[["price_disp", "volume", "cum_vol", "orders"]].copy()
        df_disp_a.columns = ["Ask Price", "Level Volume", "Cumulative", "Orders"]
        st.dataframe(df_disp_a, use_container_width=True, hide_index=True)
    else:
        st.info("No active sell orders in book.")

# Visual Market Depth
if bids or asks:
    st.markdown("### 📊 Cumulative Market Depth Curve")
    fig = go.Figure()

    if bids:
        # Sort ascending for bids so cumulative curve steps up to best bid
        bids_sorted = sorted(bids, key=lambda x: x["price"])
        prices = [b["price"] for b in bids_sorted]
        cum_vol = []
        running = 0
        for b in reversed(bids_sorted):
            running += b["volume"]
            cum_vol.append(running)
        cum_vol.reverse()

        fig.add_trace(go.Scatter(
            x=prices,
            y=cum_vol,
            fill='tozeroy',
            mode='lines+markers',
            name='Bids (Cumulative)',
            line=dict(color='#10b981', width=2.5),
            fillcolor='rgba(16, 185, 129, 0.25)'
        ))

    if asks:
        asks_sorted = sorted(asks, key=lambda x: x["price"])
        prices = [a["price"] for a in asks_sorted]
        cum_vol = []
        running = 0
        for a in asks_sorted:
            running += a["volume"]
            cum_vol.append(running)

        fig.add_trace(go.Scatter(
            x=prices,
            y=cum_vol,
            fill='tozeroy',
            mode='lines+markers',
            name='Asks (Cumulative)',
            line=dict(color='#f43f5e', width=2.5),
            fillcolor='rgba(244, 63, 94, 0.25)'
        ))

    fig.update_layout(
        paper_bgcolor="#151924",
        plot_bgcolor="#151924",
        font=dict(color="#f8fafc", size=12),
        height=380,
        xaxis=dict(
            title=dict(text="Price (INR ₹)", font=dict(color="#f8fafc", size=12)),
            gridcolor="#28334a",
            tickfont=dict(color="#cbd5e1", size=11)
        ),
        yaxis=dict(
            title=dict(text="Cumulative Volume (Shares)", font=dict(color="#f8fafc", size=12)),
            gridcolor="#28334a",
            tickfont=dict(color="#cbd5e1", size=11)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#e2e8f0", size=11)
        )
    )
    st.plotly_chart(fig, use_container_width=True)
