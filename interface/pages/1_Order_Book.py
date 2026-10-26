"""
1_Order_Book.py - Deep Order Book Analytics & Liquidity Distribution (Groww Light Theme)
Inspects price-time priority queues and dual heaps in the C11 matching engine.
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import FinMatchEngine
from style import apply_custom_style, render_top_navbar, render_disclaimer, render_navigation_bar, GROWW_GREEN, GROWW_RED
import auth
import market_data

st.set_page_config(page_title="Order Book | FinMatch", page_icon="📖", layout="wide")
apply_custom_style()

if "engine" not in st.session_state:
    st.session_state.engine = FinMatchEngine()

if "market_feed" not in st.session_state:
    st.session_state.market_feed = market_data.MarketDataFeed()

if "user" not in st.session_state:
    st.session_state.user = auth.get_user_by_id(1)

engine: FinMatchEngine = st.session_state.engine
feed: market_data.MarketDataFeed = st.session_state.market_feed
user = st.session_state.user

render_top_navbar(user, active_page="Order Book")
render_navigation_bar(active_page="Order Book")
render_disclaimer()

st.markdown("""
<div style='margin-bottom: 1.25rem;'>
    <div style='font-size: 1.6rem; font-weight: 800; color: #0F172A;'>📖 Deep Order Book Analytics</div>
    <div style='font-size: 0.88rem; color: #64748B;'>
        Real-time inspection of Dual Heap Priority Queues: Max-Heap for Bids (Highest Price Priority) and Min-Heap for Asks (Lowest Price Priority).
    </div>
</div>
""", unsafe_allow_html=True)

if not engine.is_available():
    st.error("C Matching Engine is not loaded.")
    st.stop()

col_sym, col_seed, col_refresh = st.columns([2.5, 1, 1])
with col_sym:
    symbols = list(market_data.STOCKS_CATALOG.keys())
    symbol = st.selectbox("Select Active Stock Symbol", symbols, index=0)

stock_info = feed.get_stock(symbol)
# Ensure order book always has active liquidity
if hasattr(market_data, "auto_seed_book_if_empty"):
    market_data.auto_seed_book_if_empty(engine, symbol, stock_info["current_price"])
elif engine and engine.is_available():
    book_temp = engine.get_order_book(symbol)
    if book_temp.get("total_bid_vol", 0) == 0 and book_temp.get("total_ask_vol", 0) == 0:
        p = stock_info["current_price"]
        engine.place_order("MM_Alpha", symbol, "BUY", round(p * 0.998, 2), 100)
        engine.place_order("MM_Beta", symbol, "BUY", round(p * 0.995, 2), 250)
        engine.place_order("MM_Alpha", symbol, "SELL", round(p * 1.002, 2), 120)
        engine.place_order("MM_Beta", symbol, "SELL", round(p * 1.005, 2), 280)

with col_seed:
    st.write("")
    st.write("")
    if st.button("🌱 Seed Liquidity", use_container_width=True, help="Inject 5 bid and 5 ask orders into the C engine book"):
        p = stock_info["current_price"]
        engine.place_order("MM_Alpha", symbol, "BUY", round(p * 0.998, 2), 150)
        engine.place_order("MM_Beta", symbol, "BUY", round(p * 0.995, 2), 300)
        engine.place_order("Institutional", symbol, "BUY", round(p * 0.990, 2), 500)
        engine.place_order("MM_Alpha", symbol, "SELL", round(p * 1.002, 2), 150)
        engine.place_order("MM_Beta", symbol, "SELL", round(p * 1.005, 2), 300)
        engine.place_order("Institutional", symbol, "SELL", round(p * 1.010, 2), 500)
        st.toast(f"Seeded active liquidity for {symbol}!")
        st.rerun()

with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh Book", use_container_width=True):
        st.rerun()

book = engine.get_order_book(symbol)
stats = engine.get_market_stats(symbol)

bb = stats.get("best_bid")
ba = stats.get("best_ask")
spread = stats.get("spread")
tot_vol = book.get("total_bid_vol", 0) + book.get("total_ask_vol", 0)

# Summary Cards Bar
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Best Bid (Highest Buyer)", f"₹{bb:,.2f}" if bb else "—", "Max-Heap Top")
c2.metric("Best Ask (Lowest Seller)", f"₹{ba:,.2f}" if ba else "—", "Min-Heap Top")
c3.metric("Bid-Ask Spread", f"₹{spread:,.2f}" if spread is not None else "—", "Ask - Bid Difference")
c4.metric("Market Depth (Shares)", f"{tot_vol:,}", f"Bids: {book.get('total_bid_vol', 0):,} | Asks: {book.get('total_ask_vol', 0):,}")
st.markdown("</div>", unsafe_allow_html=True)

# Dual Split Order Book Tables
col_bids, col_asks = st.columns(2)
bids = book.get("bids", [])
asks = book.get("asks", [])

with col_bids:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #00D09C; margin-bottom: 8px;'>🟢 BIDS (Max-Heap: Highest Price Priority)</h4>", unsafe_allow_html=True)
    if bids:
        df_bids = pd.DataFrame(bids)
        df_bids["cum_vol"] = df_bids["volume"].cumsum()
        df_bids["price_disp"] = df_bids["price"].apply(lambda p: f"₹{p:,.2f}")
        df_disp_b = df_bids[["price_disp", "volume", "cum_vol", "orders"]].copy()
        df_disp_b.columns = ["Bid Price (INR)", "Level Volume", "Cumulative Shares", "Active Orders"]
        st.dataframe(df_disp_b, use_container_width=True, hide_index=True)
    else:
        st.info(f"No resting buy orders in the {symbol} book. Seed liquidity or place orders from the Dashboard.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_asks:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #EB5B3C; margin-bottom: 8px;'>🔴 ASKS (Min-Heap: Lowest Price Priority)</h4>", unsafe_allow_html=True)
    if asks:
        df_asks = pd.DataFrame(asks)
        df_asks["cum_vol"] = df_asks["volume"].cumsum()
        df_asks["price_disp"] = df_asks["price"].apply(lambda p: f"₹{p:,.2f}")
        df_disp_a = df_asks[["price_disp", "volume", "cum_vol", "orders"]].copy()
        df_disp_a.columns = ["Ask Price (INR)", "Level Volume", "Cumulative Shares", "Active Orders"]
        st.dataframe(df_disp_a, use_container_width=True, hide_index=True)
    else:
        st.info(f"No resting sell orders in the {symbol} book. Seed liquidity or place orders from the Dashboard.")
    st.markdown("</div>", unsafe_allow_html=True)

# Cumulative Market Depth Curve Chart
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown("#### 📊 Cumulative Market Depth Curve")

if bids or asks:
    fig = go.Figure()

    if bids:
        bids_sorted = sorted(bids, key=lambda x: x["price"])
        prices_b = [b["price"] for b in bids_sorted]
        cum_vol_b = []
        running = 0
        for b in reversed(bids_sorted):
            running += b["volume"]
            cum_vol_b.append(running)
        cum_vol_b.reverse()

        fig.add_trace(go.Scatter(
            x=prices_b,
            y=cum_vol_b,
            mode='lines',
            fill='tozeroy',
            name='Bids Depth (Buyers)',
            line=dict(color='#00D09C', width=2.5, shape='hv'),
            fillcolor='rgba(0, 208, 156, 0.15)'
        ))

    if asks:
        asks_sorted = sorted(asks, key=lambda x: x["price"])
        prices_a = [a["price"] for a in asks_sorted]
        cum_vol_a = []
        running = 0
        for a in asks_sorted:
            running += a["volume"]
            cum_vol_a.append(running)

        fig.add_trace(go.Scatter(
            x=prices_a,
            y=cum_vol_a,
            mode='lines',
            fill='tozeroy',
            name='Asks Depth (Sellers)',
            line=dict(color='#EB5B3C', width=2.5, shape='hv'),
            fillcolor='rgba(235, 91, 60, 0.15)'
        ))

    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified",
        xaxis=dict(
            title="Limit Price (INR ₹)",
            showgrid=True,
            gridcolor="#F1F5F9",
            tickfont=dict(color="#64748B", size=11)
        ),
        yaxis=dict(
            title="Cumulative Shares Available",
            showgrid=True,
            gridcolor="#F1F5F9",
            tickfont=dict(color="#64748B", size=11)
        ),
        legend=dict(orientation="h", y=1.05, x=0, font=dict(size=11))
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Insufficient active orders in the order book to render depth curve. Place orders or seed liquidity.")

st.markdown("</div>", unsafe_allow_html=True)
