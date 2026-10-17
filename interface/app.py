"""
FinMatch - Main Trading Terminal & Dashboard
Built with Streamlit and C11 High-Performance Matching Engine
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import os
import sys

# Ensure interface directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import FinMatchEngine
from style import apply_custom_style

# Page configuration
st.set_page_config(
    page_title="FinMatch | Trading Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply accessible high-contrast dark theme
apply_custom_style()

# Initialize Engine singleton in session_state
if "engine" not in st.session_state:
    st.session_state.engine = FinMatchEngine()

engine: FinMatchEngine = st.session_state.engine

# Sidebar Configuration
with st.sidebar:
    st.title("⚡ FinMatch Terminal")
    st.caption("C11 Core • Price-Time Priority • Academic DSA Project")

    # Engine Status
    if engine.is_available():
        st.success("🟢 C Engine Loaded (`finmatch.dll`)")
    else:
        st.error("🔴 C Engine Unavailable")
        st.info(engine.load_error or "Build `finmatch.dll` first.")
        if st.button("🔄 Retry Engine Reload", use_container_width=True):
            st.session_state.engine = FinMatchEngine()
            st.rerun()

    st.markdown("---")
    st.subheader("Market Settings")
    symbols_list = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "TATAMOTORS", "SBIN", "CUSTOM..."]
    selected_choice = st.selectbox("Active Stock Symbol", symbols_list, index=0)
    
    if selected_choice == "CUSTOM...":
        custom_input = st.text_input("Enter Symbol (Uppercase)", value="AAPL", max_chars=12)
        selected_symbol = custom_input.strip().upper() if custom_input.strip() else "RELIANCE"
    else:
        selected_symbol = selected_choice

    st.markdown("---")
    st.subheader("Simulation Controls")
    col_demo, col_rst = st.columns(2)
    with col_demo:
        if st.button("🚀 Seed Liquidity", use_container_width=True, help="Inject realistic bid/ask orders into the active C order book"):
            # Seed realistic simulated orders
            engine.place_order("MarketMaker1", selected_symbol, "BUY", 2490.00, 100)
            engine.place_order("MarketMaker2", selected_symbol, "BUY", 2485.50, 250)
            engine.place_order("RetailBuyer", selected_symbol, "BUY", 2480.00, 500)
            engine.place_order("MarketMaker1", selected_symbol, "SELL", 2510.00, 150)
            engine.place_order("MarketMaker3", selected_symbol, "SELL", 2515.00, 300)
            engine.place_order("Institutional", selected_symbol, "SELL", 2525.00, 450)
            st.toast(f"Seeded liquidity for {selected_symbol}!")
            st.rerun()

    with col_rst:
        if st.button("🧹 Reset Book", use_container_width=True, help="Wipe in-memory order books, queues, and trades"):
            engine.reset_engine()
            st.toast("Engine state reset.")
            st.rerun()

    st.markdown("---")
    st.caption("⚠️ **Educational Simulator Disclaimer**\n\nFinMatch is an academic simulation for Data Structures & Algorithms coursework. It does not process real money or connect to live exchanges.")

# Main Dashboard Header
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.markdown(f"## 📊 Market Overview — **{selected_symbol}** <span class='badge-sim'>SIMULATED</span>", unsafe_allow_html=True)
    st.markdown("Ultra-low latency limit-order matching with **Max/Min Heaps**, **FIFO queues**, and **$O(1)$ Hash Table** lookup.")

with col_header2:
    stats = engine.get_market_stats(selected_symbol) if engine.is_available() else {}
    last_px = stats.get("last_trade_price")
    if last_px:
        st.metric("Last Traded Price", f"₹{last_px:,.2f}", f"{stats.get('last_trade_qty', 0):,} shares")
    else:
        st.metric("Last Traded Price", "No Trades Yet", "—")

# Key Market Metrics Cards
mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
bb = stats.get("best_bid")
ba = stats.get("best_ask")
spread = stats.get("spread")
bid_vol = stats.get("total_buy_volume", 0)
ask_vol = stats.get("total_sell_volume", 0)

with mcol1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Best Bid (Highest Buyer)</div>
        <div class='metric-value metric-bid'>{"₹" + f"{bb:,.2f}" if bb else "—"}</div>
    </div>
    """, unsafe_allow_html=True)

with mcol2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Best Ask (Lowest Seller)</div>
        <div class='metric-value metric-ask'>{"₹" + f"{ba:,.2f}" if ba else "—"}</div>
    </div>
    """, unsafe_allow_html=True)

with mcol3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Bid-Ask Spread</div>
        <div class='metric-value'>{"₹" + f"{spread:,.2f}" if spread is not None else "—"}</div>
    </div>
    """, unsafe_allow_html=True)

with mcol4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Total Active Bids</div>
        <div class='metric-value'>{bid_vol:,} <span style='font-size:0.85rem;color:#cbd5e1;'>shares</span></div>
    </div>
    """, unsafe_allow_html=True)

with mcol5:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-title'>Total Active Asks</div>
        <div class='metric-value'>{ask_vol:,} <span style='font-size:0.85rem;color:#cbd5e1;'>shares</span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Two-Column Layout: Left = Order Placement & Cancellation, Right = Real-time Order Book & Trades
col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("📝 Place Limit Order")
    with st.form("place_order_form", clear_on_submit=False):
        trader_id = st.text_input("Trader Identifier", value="Trader_Alpha", max_chars=30)
        col_side, col_qty = st.columns(2)
        with col_side:
            side_selection = st.radio("Order Side", ["BUY", "SELL"], horizontal=True)
        with col_qty:
            quantity = st.number_input("Quantity (Shares)", min_value=1, max_value=1000000, value=100, step=10)

        # Suggested price based on current book
        default_price = 2500.00
        if bb and side_selection == "BUY":
            default_price = float(bb)
        elif ba and side_selection == "SELL":
            default_price = float(ba)

        limit_price = st.number_input("Limit Price (INR ₹)", min_value=0.05, max_value=1000000.0, value=default_price, step=0.25, format="%.2f")

        submit_order = st.form_submit_button("⚡ Submit Order to C Engine", use_container_width=True)

        if submit_order:
            if not engine.is_available():
                st.error("C Matching Engine is not loaded.")
            else:
                res = engine.place_order(trader_id, selected_symbol, side_selection, limit_price, quantity)
                if res.get("success"):
                    st.success(f"✅ Order **#{res['order_id']}** Accepted! Status: **{res['status']}**")
                    col_r1, col_r2, col_r3 = st.columns(3)
                    col_r1.metric("Filled Qty", f"{res['filled_qty']:,}")
                    col_r2.metric("Remaining Qty", f"{res['remaining_qty']:,}")
                    col_r3.metric("Trades Triggered", res["trades_generated"])
                    st.rerun()
                else:
                    st.error(f"❌ Order Rejected: {res.get('error')}")

    st.markdown("---")
    st.subheader("🛑 Cancel Active Order")
    with st.form("cancel_order_form"):
        col_cid, col_cbtn = st.columns([2, 1])
        with col_cid:
            cancel_id = st.number_input("Order ID", min_value=1, step=1, value=1)
        with col_cbtn:
            st.write("")
            st.write("")
            cancel_btn = st.form_submit_button("Cancel Order", use_container_width=True)

        if cancel_btn:
            cres = engine.cancel_order(cancel_id)
            if cres.get("success"):
                st.success(f"✅ Order **#{cancel_id}** successfully CANCELLED. Released: **{cres['cancelled_qty']} shares**.")
                st.rerun()
            else:
                st.error(f"❌ Cancellation Failed: {cres.get('error')}")

with col_right:
    st.subheader(f"📖 Live Order Book Depth ({selected_symbol})")
    book = engine.get_order_book(selected_symbol) if engine.is_available() else {"bids": [], "asks": []}
    bids = book.get("bids", [])
    asks = book.get("asks", [])

    # Order book tables
    col_b, col_a = st.columns(2)
    with col_b:
        st.markdown("<h4 style='color:#10b981; text-align:center;'>BUY ORDERS (BIDS)</h4>", unsafe_allow_html=True)
        if bids:
            df_bids = pd.DataFrame(bids)
            df_bids["price"] = df_bids["price"].apply(lambda p: f"₹{p:,.2f}")
            df_bids.columns = ["Price (INR)", "Volume", "Orders"]
            st.dataframe(df_bids, use_container_width=True, hide_index=True)
        else:
            st.info("No active buy orders.")

    with col_a:
        st.markdown("<h4 style='color:#f43f5e; text-align:center;'>SELL ORDERS (ASKS)</h4>", unsafe_allow_html=True)
        if asks:
            df_asks = pd.DataFrame(asks)
            df_asks["price"] = df_asks["price"].apply(lambda p: f"₹{p:,.2f}")
            df_asks.columns = ["Price (INR)", "Volume", "Orders"]
            st.dataframe(df_asks, use_container_width=True, hide_index=True)
        else:
            st.info("No active sell orders.")

    # Depth Chart Visualization using Plotly with high contrast
    if bids or asks:
        bid_prices = [b["price"] for b in bids]
        bid_cum_vols = [b["volume"] for b in bids]
        ask_prices = [a["price"] for a in asks]
        ask_cum_vols = [a["volume"] for a in asks]

        fig = go.Figure()
        if bid_prices:
            # Sort ascending for bids
            b_sorted = sorted(zip(bid_prices, bid_cum_vols), key=lambda x: x[0])
            fig.add_trace(go.Scatter(
                x=[x[0] for x in b_sorted],
                y=[x[1] for x in b_sorted],
                fill='tozeroy',
                mode='lines+markers',
                name='Bids (Cumulative)',
                line=dict(color='#10b981', width=2.5),
                fillcolor='rgba(16, 185, 129, 0.25)'
            ))
        if ask_prices:
            a_sorted = sorted(zip(ask_prices, ask_cum_vols), key=lambda x: x[0])
            fig.add_trace(go.Scatter(
                x=[x[0] for x in a_sorted],
                y=[x[1] for x in a_sorted],
                fill='tozeroy',
                mode='lines+markers',
                name='Asks (Cumulative)',
                line=dict(color='#f43f5e', width=2.5),
                fillcolor='rgba(244, 63, 94, 0.25)'
            ))

        fig.update_layout(
            title=dict(text="Order Book Liquidity Distribution", font=dict(color="#ffffff", size=14)),
            paper_bgcolor="#151924",
            plot_bgcolor="#151924",
            font=dict(color="#f8fafc", size=12),
            height=280,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(
                title=dict(text="Price (INR ₹)", font=dict(color="#f8fafc", size=12)),
                gridcolor="#28334a",
                tickfont=dict(color="#cbd5e1", size=11)
            ),
            yaxis=dict(
                title=dict(text="Shares Available", font=dict(color="#f8fafc", size=12)),
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

# Recent Trades Row
st.markdown("---")
st.subheader("📜 Recent Executed Matches")
trades = engine.get_recent_trades(selected_symbol, max_trades=15) if engine.is_available() else []
if trades:
    df_trades = pd.DataFrame(trades)
    df_trades["price"] = df_trades["price"].apply(lambda p: f"₹{p:,.2f}")
    df_trades["turnover"] = df_trades.apply(lambda r: f"₹{(float(r['price'].replace('₹','').replace(',','')) * r['quantity']):,.2f}", axis=1)
    df_trades = df_trades[["trade_id", "buy_order_id", "sell_order_id", "price", "quantity", "turnover", "sequence"]]
    df_trades.columns = ["Trade ID", "Buyer ID", "Seller ID", "Exec Price", "Quantity", "Turnover", "Sequence"]
    st.dataframe(df_trades, use_container_width=True, hide_index=True)
else:
    st.info(f"No executions recorded yet for {selected_symbol}.")
