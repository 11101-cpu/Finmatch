"""
app.py - FinMatch Trading Terminal & Simulator (Groww-inspired Light Theme)
Integrated with C11 High-Performance Matching Engine, SQLite Authentication,
and Real-Time Simulated Market Data.
"""

import os
import sys
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ensure interface directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import style
import auth
import market_data

importlib.reload(style)
importlib.reload(auth)
importlib.reload(market_data)

from engine import FinMatchEngine
from style import apply_custom_style, render_top_navbar, render_disclaimer, render_navigation_bar, GROWW_GREEN, GROWW_RED

# Page configuration
st.set_page_config(
    page_title="FinMatch | Trading Simulator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Groww-inspired light theme
apply_custom_style()

# Initialize Singletons in session_state
if "engine" not in st.session_state:
    st.session_state.engine = FinMatchEngine()

if "market_feed" not in st.session_state:
    st.session_state.market_feed = market_data.MarketDataFeed()

if "user" not in st.session_state:
    # Auto-login to demo account for frictionless initial evaluation
    demo_user = auth.get_user_by_id(1)
    st.session_state.user = demo_user

if "selected_timeframe" not in st.session_state:
    st.session_state.selected_timeframe = "1D"

if "chart_type" not in st.session_state:
    st.session_state.chart_type = "line"

if "last_order_token" not in st.session_state:
    st.session_state.last_order_token = None

engine: FinMatchEngine = st.session_state.engine
feed: market_data.MarketDataFeed = st.session_state.market_feed
user = st.session_state.user

# Refresh current user's cash balance and portfolio from DB
if user:
    fresh_user = auth.get_user_by_id(user["id"])
    if fresh_user:
        st.session_state.user = fresh_user
        user = fresh_user


# ---------------------------------------------------------
# AUTHENTICATION SCREEN (When user is logged out)
# ---------------------------------------------------------
if not user:
    st.markdown("""
    <div style='text-align: center; margin-top: 1.5rem; margin-bottom: 2rem;'>
        <div style='font-size: 2.2rem; font-weight: 800; color: #0F172A; display: inline-flex; align-items: center; gap: 10px;'>
            <span style='color: #00D09C;'>●</span> FinMatch Trading Simulator
        </div>
        <p style='color: #64748B; font-size: 1rem; margin-top: 6px;'>
            Clean, ultra-fast paper trading powered by a native C11 matching engine. Inspired by Groww.
        </p>
    </div>
    """, unsafe_allow_html=True)

    render_disclaimer()

    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        auth_tab_login, auth_tab_signup, auth_tab_forgot = st.tabs(["🔑 Log In", "📝 Sign Up", "❓ Forgot Password"])

        with auth_tab_login:
            st.markdown("#### Welcome Back")
            with st.form("login_form"):
                login_email = st.text_input("Email Address", value="demo@groww.in")
                login_pwd = st.text_input("Password", type="password", value="groww123")
                login_submitted = st.form_submit_button("Log In to Trading Simulator", use_container_width=True)

                if login_submitted:
                    u, msg = auth.authenticate_user(login_email, login_pwd)
                    if u:
                        st.session_state.user = u
                        st.success(f"Welcome back, {u['full_name']}!")
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")
            if st.button("⚡ Fast Demo Log In (1-Click)", use_container_width=True):
                u = auth.get_user_by_id(1)
                if u:
                    st.session_state.user = u
                    st.rerun()

        with auth_tab_signup:
            st.markdown("#### Create Simulated Account")
            with st.form("signup_form"):
                reg_name = st.text_input("Full Name", placeholder="e.g. Rahul Verma")
                reg_email = st.text_input("Email Address", placeholder="rahul@example.com")
                reg_pwd = st.text_input("Password (min 6 characters)", type="password")
                reg_pwd_confirm = st.text_input("Confirm Password", type="password")
                reg_submitted = st.form_submit_button("Create Free Simulator Account", use_container_width=True)

                if reg_submitted:
                    ok, msg = auth.register_user(reg_name, reg_email, reg_pwd, reg_pwd_confirm)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        with auth_tab_forgot:
            st.markdown("#### Reset Account Password")
            with st.form("forgot_form"):
                f_email = st.text_input("Registered Email")
                f_new_pwd = st.text_input("New Password", type="password")
                f_conf_pwd = st.text_input("Confirm New Password", type="password")
                f_submitted = st.form_submit_button("Reset Password", use_container_width=True)

                if f_submitted:
                    ok, msg = auth.reset_password(f_email, f_new_pwd, f_conf_pwd)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    st.stop()


# ---------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;'>
        <span style='color: #00D09C; font-size: 1.4rem;'>●</span>
        <span style='font-size: 1.25rem; font-weight: 800; color: #0F172A;'>FinMatch</span>
    </div>
    <div style='font-size: 0.78rem; color: #64748B; margin-bottom: 1rem;'>
        C11 Core Engine • Price-Time Priority
    </div>
    """, unsafe_allow_html=True)

    # Engine Status Pill
    if engine.is_available():
        st.markdown("""
        <div style='background: #E8FAF4; border: 1px solid #00D09C; color: #00875A; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; gap: 6px; margin-bottom: 1rem;'>
            <span>🟢</span> C Engine Active (finmatch.dll)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("🔴 C Engine Unavailable")
        if st.button("🔄 Retry Engine Reload", use_container_width=True):
            st.session_state.engine = FinMatchEngine()
            st.rerun()

    st.markdown("### 🔍 Select Instrument")
    symbol_options = list(market_data.STOCKS_CATALOG.keys()) + ["CUSTOM..."]
    selected_choice = st.selectbox("Search Stock Symbol", symbol_options, index=0)

    if selected_choice == "CUSTOM...":
        custom_input = st.text_input("Enter Symbol (e.g. TATAPOWER)", value="WIPRO", max_chars=12)
        selected_symbol = custom_input.strip().upper() if custom_input.strip() else "RELIANCE"
    else:
        selected_symbol = selected_choice

    st.markdown("---")
    st.markdown("### 🕹️ Simulation Controls")

    col_seed, col_tick = st.columns(2)
    with col_seed:
        if st.button("🌱 Seed Book", use_container_width=True, help="Populate resting bids and asks around the simulated market price"):
            stock_data = feed.get_stock(selected_symbol)
            p = stock_data["current_price"]
            # Seed 3 bids and 3 asks around price
            engine.place_order("MM_Alpha", selected_symbol, "BUY", round(p * 0.995, 2), 150)
            engine.place_order("MM_Beta", selected_symbol, "BUY", round(p * 0.990, 2), 300)
            engine.place_order("MM_Gamma", selected_symbol, "BUY", round(p * 0.985, 2), 500)
            engine.place_order("MM_Alpha", selected_symbol, "SELL", round(p * 1.005, 2), 120)
            engine.place_order("MM_Beta", selected_symbol, "SELL", round(p * 1.010, 2), 250)
            engine.place_order("MM_Delta", selected_symbol, "SELL", round(p * 1.015, 2), 400)
            st.toast(f"Seeded 6 liquidity orders for {selected_symbol}!")
            st.rerun()

    with col_tick:
        if st.button("📈 Next Tick", use_container_width=True, help="Simulate real-time price fluctuation"):
            feed.simulate_tick(selected_symbol)
            st.rerun()

    if st.button("🧹 Reset Book", use_container_width=True, help="Wipe in-memory C orders and trade queues"):
        engine.reset_engine()
        st.toast(f"Engine order book reset.")
        st.rerun()

    st.markdown("---")
    st.markdown("### 👤 Account Details")
    st.markdown(f"**Trader:** {user['full_name']}")
    st.markdown(f"**Cash Balance:** ₹{user['cash_balance']:,.2f}")

    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.user = None
        st.rerun()


# ---------------------------------------------------------
# MAIN DASHBOARD CONTENT
# ---------------------------------------------------------

# Top Navigation Bar & Simulator Banner
render_top_navbar(user, active_page="Dashboard")
render_navigation_bar(active_page="Dashboard")
render_disclaimer()

# Retrieve Unified Market Data and C Engine Stats
stock = feed.get_stock(selected_symbol)
# Ensure order book always has active liquidity
if hasattr(market_data, "auto_seed_book_if_empty"):
    market_data.auto_seed_book_if_empty(engine, selected_symbol, stock["current_price"])
elif engine and engine.is_available():
    book = engine.get_order_book(selected_symbol)
    if book.get("total_bid_vol", 0) == 0 and book.get("total_ask_vol", 0) == 0:
        p = stock["current_price"]
        engine.place_order("MM_Alpha", selected_symbol, "BUY", round(p * 0.998, 2), 100)
        engine.place_order("MM_Beta", selected_symbol, "BUY", round(p * 0.995, 2), 250)
        engine.place_order("MM_Alpha", selected_symbol, "SELL", round(p * 1.002, 2), 120)
        engine.place_order("MM_Beta", selected_symbol, "SELL", round(p * 1.005, 2), 280)
engine_stats = engine.get_market_stats(selected_symbol) if engine.is_available() else {}

# If C Engine has trades for this symbol, anchor the stock's current price to the last trade price
last_engine_price = engine_stats.get("last_trade_price")
if last_engine_price and last_engine_price > 0:
    stock["current_price"] = last_engine_price
    abs_chg = round(stock["current_price"] - stock["previous_close"], 2)
    stock["change_absolute"] = abs_chg
    stock["change_percent"] = round((abs_chg / stock["previous_close"]) * 100, 2) if stock["previous_close"] else 0.0
    stock["is_positive"] = abs_chg >= 0

curr_price = stock["current_price"]
abs_change = stock["change_absolute"]
pct_change = stock["change_percent"]
is_pos = stock["is_positive"]

best_bid = engine_stats.get("best_bid")
best_ask = engine_stats.get("best_ask")
spread = engine_stats.get("spread")
active_bids_vol = engine_stats.get("total_buy_volume", 0)
active_asks_vol = engine_stats.get("total_sell_volume", 0)


# ---------------------------------------------------------
# STOCK HERO SECTION (Groww-styled Price & Indicator)
# ---------------------------------------------------------
col_hero_left, col_hero_right = st.columns([2.5, 1])

with col_hero_left:
    change_sign = "+" if abs_change >= 0 else ""
    arrow_indicator = "▲" if abs_change >= 0 else "▼"
    badge_class = "badge-positive" if is_pos else "badge-negative"

    st.markdown(f"""
    <div class="stock-hero">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="stock-title">{stock['name']}</div>
                <div class="stock-subtitle">NSE • {selected_symbol} • {stock['sector']}</div>
            </div>
            <span class="brand-badge">SIMULATED FEED</span>
        </div>
        <div style="display: flex; align-items: baseline; gap: 14px; margin-top: 8px;">
            <div class="stock-price-main">₹{curr_price:,.2f}</div>
            <div class="{badge_class}">
                <span>{change_sign}₹{abs_change:,.2f} ({change_sign}{pct_change:.2f}%)</span>
                <span>{arrow_indicator}</span>
            </div>
            <span style="font-size: 0.8rem; color: #64748B; font-weight: 500;">Today</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_hero_right:
    st.markdown(f"""
    <div class="groww-card" style="height: 100%;">
        <div style="font-size: 0.76rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 8px;">
            Market Depth Overview
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 0.85rem; color: #64748B;">Best Bid:</span>
            <span style="font-size: 0.88rem; font-weight: 700; color: #00D09C;">{"₹" + f"{best_bid:,.2f}" if best_bid else "—"}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 0.85rem; color: #64748B;">Best Ask:</span>
            <span style="font-size: 0.88rem; font-weight: 700; color: #EB5B3C;">{"₹" + f"{best_ask:,.2f}" if best_ask else "—"}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 0.85rem; color: #64748B;">Spread:</span>
            <span style="font-size: 0.88rem; font-weight: 700; color: #0F172A;">{"₹" + f"{spread:,.2f}" if spread is not None else "—"}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="font-size: 0.85rem; color: #64748B;">Active Orders:</span>
            <span style="font-size: 0.88rem; font-weight: 700; color: #0F172A;">{engine_stats.get('total_orders', 0):,}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# INTERACTIVE STOCK CHART (Groww Emerald / Coral Style)
# ---------------------------------------------------------
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)

col_tf, col_type = st.columns([3, 1])
with col_tf:
    # Timeframe selection
    tfs = ["1D", "1W", "1M", "3M", "1Y"]
    selected_tf = st.radio(
        "Timeframe",
        tfs,
        index=tfs.index(st.session_state.selected_timeframe),
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.selected_timeframe = selected_tf

with col_type:
    chart_style = st.selectbox(
        "Chart Style",
        ["Line (Groww Style)", "Candlestick"],
        index=0 if st.session_state.chart_type == "line" else 1,
        label_visibility="collapsed"
    )
    st.session_state.chart_type = "candlestick" if "Candlestick" in chart_style else "line"

# Fetch timeframe dataframe
df_chart = stock["histories"].get(selected_tf, stock["histories"]["1D"])
fig = market_data.build_groww_chart(
    df=df_chart,
    symbol=selected_symbol,
    chart_type=st.session_state.chart_type,
    is_positive=is_pos,
    previous_close=stock["previous_close"],
    height=400
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# TWO-COLUMN TRADING ROW: Order Placement vs Live Order Book
# ---------------------------------------------------------
col_trade_panel, col_depth_panel = st.columns([1.1, 1.3])

with col_trade_panel:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Order Placement")

    order_tab_buy, order_tab_sell = st.tabs(["🟢 BUY", "🔴 SELL"])

    # Suggested price logic
    default_buy_px = float(best_ask) if best_ask else float(curr_price)
    default_sell_px = float(best_bid) if best_bid else float(curr_price)

    # --- BUY TAB ---
    with order_tab_buy:
        with st.form("buy_order_form"):
            st.caption(f"Buy **{selected_symbol}** with simulated cash (Balance: ₹{user['cash_balance']:,.2f})")
            
            qty_buy = st.number_input("Shares Quantity", min_value=1, max_value=500000, value=10, step=1, key="buy_qty")
            px_buy = st.number_input("Limit Price (INR ₹)", min_value=0.05, max_value=1000000.0, value=default_buy_px, step=0.5, format="%.2f", key="buy_px")
            
            est_value_buy = qty_buy * px_buy
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #64748B;">
                    <span>Estimated Order Value:</span>
                    <span style="font-weight: 700; color: #0F172A;">₹{est_value_buy:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                    <span>Available Cash:</span>
                    <span style="font-weight: 600; color: #00875A;">₹{user['cash_balance']:,.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            submit_buy = st.form_submit_button(f"BUY {selected_symbol}", use_container_width=True)

            if submit_buy:
                token = f"buy_{user['id']}_{selected_symbol}_{qty_buy}_{px_buy}_{time.time():.2f}"
                if token != st.session_state.last_order_token:
                    st.session_state.last_order_token = token
                    
                    if est_value_buy > user["cash_balance"]:
                        st.error(f"Insufficient virtual cash! Required: ₹{est_value_buy:,.2f}, Available: ₹{user['cash_balance']:,.2f}")
                    elif not engine.is_available():
                        st.error("C matching engine is unavailable.")
                    else:
                        trader_name = f"User_{user['id']}_{user['full_name'].split()[0]}"
                        res = engine.place_order(trader_name, selected_symbol, "BUY", px_buy, qty_buy)
                        
                        if res.get("success"):
                            st.success(f"✅ Order **#{res['order_id']}** placed! Status: **{res['status']}**")
                            # Record order in user DB
                            auth.record_user_order(user["id"], {
                                "order_id": res["order_id"],
                                "symbol": selected_symbol,
                                "side": "BUY",
                                "price": px_buy,
                                "quantity": qty_buy,
                                "status": res["status"],
                                "filled_qty": res["filled_qty"],
                                "remaining_qty": res["remaining_qty"]
                            })
                            # If filled partially or fully, process execution
                            if res["filled_qty"] > 0:
                                auth.process_trade_execution(user["id"], selected_symbol, "BUY", px_buy, res["filled_qty"])
                                feed.update_from_engine_trade(selected_symbol, px_buy, res["filled_qty"])
                            st.rerun()
                        else:
                            st.error(f"❌ Order Rejected: {res.get('error')}")

    # --- SELL TAB ---
    with order_tab_sell:
        # Check current user holdings for this symbol
        user_portfolio = auth.get_user_portfolio(user["id"])
        user_holdings = {h["symbol"]: h["quantity"] for h in user_portfolio["holdings"]}
        available_shares = user_holdings.get(selected_symbol, 0)

        with st.form("sell_order_form"):
            st.caption(f"Sell **{selected_symbol}** from holdings (Available: **{available_shares} shares**)")
            
            qty_sell = st.number_input("Shares Quantity", min_value=1, max_value=max(1, available_shares), value=min(10, max(1, available_shares)), step=1, key="sell_qty")
            px_sell = st.number_input("Limit Price (INR ₹)", min_value=0.05, max_value=1000000.0, value=default_sell_px, step=0.5, format="%.2f", key="sell_px")

            est_value_sell = qty_sell * px_sell
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #64748B;">
                    <span>Estimated Credit Value:</span>
                    <span style="font-weight: 700; color: #0F172A;">₹{est_value_sell:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #64748B; margin-top: 4px;">
                    <span>Holdings Available:</span>
                    <span style="font-weight: 600; color: #334155;">{available_shares} shares</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            submit_sell = st.form_submit_button(f"SELL {selected_symbol}", use_container_width=True)

            if submit_sell:
                token = f"sell_{user['id']}_{selected_symbol}_{qty_sell}_{px_sell}_{time.time():.2f}"
                if token != st.session_state.last_order_token:
                    st.session_state.last_order_token = token

                    if qty_sell > available_shares:
                        st.error(f"Cannot sell more shares than you hold! Available: {available_shares}")
                    elif not engine.is_available():
                        st.error("C matching engine is unavailable.")
                    else:
                        trader_name = f"User_{user['id']}_{user['full_name'].split()[0]}"
                        res = engine.place_order(trader_name, selected_symbol, "SELL", px_sell, qty_sell)
                        
                        if res.get("success"):
                            st.success(f"✅ Sell Order **#{res['order_id']}** placed! Status: **{res['status']}**")
                            # Record order in user DB
                            auth.record_user_order(user["id"], {
                                "order_id": res["order_id"],
                                "symbol": selected_symbol,
                                "side": "SELL",
                                "price": px_sell,
                                "quantity": qty_sell,
                                "status": res["status"],
                                "filled_qty": res["filled_qty"],
                                "remaining_qty": res["remaining_qty"]
                            })
                            if res["filled_qty"] > 0:
                                auth.process_trade_execution(user["id"], selected_symbol, "SELL", px_sell, res["filled_qty"])
                                feed.update_from_engine_trade(selected_symbol, px_sell, res["filled_qty"])
                            st.rerun()
                        else:
                            st.error(f"❌ Order Rejected: {res.get('error')}")

    # --- Fast Cancel Active Order ---
    st.markdown("---")
    st.markdown("##### 🛑 Active Order Cancellation")
    col_can_id, col_can_btn = st.columns([2, 1])
    with col_can_id:
        cancel_input_id = st.number_input("Order ID", min_value=1, step=1, value=1, key="cancel_target_id", label_visibility="collapsed")
    with col_can_btn:
        if st.button("Cancel Order", use_container_width=True):
            c_res = engine.cancel_order(cancel_input_id)
            if c_res.get("success"):
                auth.update_user_order_status(cancel_input_id, "CANCELLED", 0, 0)
                st.success(f"Order #{cancel_input_id} CANCELLED. Released {c_res['cancelled_qty']} shares.")
                st.rerun()
            else:
                st.error(f"Cancellation failed: {c_res.get('error')}")

    st.markdown("</div>", unsafe_allow_html=True)


with col_depth_panel:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown(f"#### 📖 Order Book Depth ({selected_symbol})")
    
    book = engine.get_order_book(selected_symbol) if engine.is_available() else {"bids": [], "asks": []}
    bids = book.get("bids", [])
    asks = book.get("asks", [])

    col_book_bids, col_book_asks = st.columns(2)

    with col_book_bids:
        st.markdown("<div style='color: #00D09C; font-weight: 700; font-size: 0.88rem; margin-bottom: 6px;'>🟢 BIDS (BUYERS)</div>", unsafe_allow_html=True)
        if bids:
            df_b = pd.DataFrame(bids)
            df_b["Price"] = df_b["price"].apply(lambda p: f"₹{p:,.2f}")
            df_b["Qty"] = df_b["volume"]
            df_b["Orders"] = df_b["orders"]
            st.dataframe(df_b[["Price", "Qty", "Orders"]], use_container_width=True, hide_index=True, height=180)
        else:
            st.info("No active buy orders in book.")

    with col_book_asks:
        st.markdown("<div style='color: #EB5B3C; font-weight: 700; font-size: 0.88rem; margin-bottom: 6px;'>🔴 ASKS (SELLERS)</div>", unsafe_allow_html=True)
        if asks:
            df_a = pd.DataFrame(asks)
            df_a["Price"] = df_a["price"].apply(lambda p: f"₹{p:,.2f}")
            df_a["Qty"] = df_a["volume"]
            df_a["Orders"] = df_a["orders"]
            st.dataframe(df_a[["Price", "Qty", "Orders"]], use_container_width=True, hide_index=True, height=180)
        else:
            st.info("No active sell orders in book.")

    # Visual Order Book Liquidity Distribution Chart
    if bids or asks:
        fig_depth = go.Figure()
        if bids:
            b_sorted = sorted(bids, key=lambda x: x["price"])
            fig_depth.add_trace(go.Scatter(
                x=[x["price"] for x in b_sorted],
                y=[x["volume"] for x in b_sorted],
                fill='tozeroy',
                mode='lines+markers',
                name='Bids (Buy Volume)',
                line=dict(color='#00D09C', width=2),
                fillcolor='rgba(0, 208, 156, 0.15)'
            ))
        if asks:
            a_sorted = sorted(asks, key=lambda x: x["price"])
            fig_depth.add_trace(go.Scatter(
                x=[x["price"] for x in a_sorted],
                y=[x["volume"] for x in a_sorted],
                fill='tozeroy',
                mode='lines+markers',
                name='Asks (Sell Volume)',
                line=dict(color='#EB5B3C', width=2),
                fillcolor='rgba(235, 91, 60, 0.15)'
            ))

        fig_depth.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=160,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(color="#64748B", size=10)),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(color="#64748B", size=10)),
            legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10))
        )
        st.plotly_chart(fig_depth, use_container_width=True, config={"displayModeBar": False})

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# USER PORTFOLIO & RECENT MATCHES SECTION
# ---------------------------------------------------------
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown("#### 💼 Your Simulated Portfolio")

port = auth.get_user_portfolio(user["id"])
user_holdings_list = port["holdings"]

if user_holdings_list:
    total_curr_val = 0.0
    for h in user_holdings_list:
        sym = h["symbol"]
        curr_p = feed.get_stock(sym)["current_price"]
        total_curr_val += (curr_p * h["quantity"])

    total_inv = port["total_invested"]
    total_pnl = total_curr_val - total_inv
    pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0.0

    p_c1, p_c2, p_c3, p_c4 = st.columns(4)
    p_c1.metric("Current Value", f"₹{total_curr_val:,.2f}")
    p_c2.metric("Total Invested", f"₹{total_inv:,.2f}")
    
    pnl_sign = "+" if total_pnl >= 0 else ""
    p_c3.metric(
        "Total Profit / Loss",
        f"{pnl_sign}₹{total_pnl:,.2f}",
        f"{pnl_sign}{pnl_pct:.2f}%",
        delta_color="normal" if total_pnl >= 0 else "inverse"
    )
    p_c4.metric("Available Cash", f"₹{user['cash_balance']:,.2f}")

    # Holdings Table
    holdings_display = []
    for h in user_holdings_list:
        sym = h["symbol"]
        curr_p = feed.get_stock(sym)["current_price"]
        h_val = curr_p * h["quantity"]
        h_pnl = h_val - h["total_invested"]
        h_pct = (h_pnl / h["total_invested"] * 100) if h["total_invested"] > 0 else 0.0
        
        sign = "+" if h_pnl >= 0 else ""
        holdings_display.append({
            "Stock": sym,
            "Shares": f"{h['quantity']:,}",
            "Avg Buy Price": f"₹{h['avg_buy_price']:,.2f}",
            "Current Price": f"₹{curr_p:,.2f}",
            "Invested Amount": f"₹{h['total_invested']:,.2f}",
            "Current Value": f"₹{h_val:,.2f}",
            "P&L (Unrealized)": f"{sign}₹{h_pnl:,.2f} ({sign}{h_pct:.2f}%)"
        })
    df_h = pd.DataFrame(holdings_display)
    st.dataframe(df_h, use_container_width=True, hide_index=True)
else:
    st.info("No active stock holdings in your portfolio. Use the BUY panel above to build your simulated equity positions!")

st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# RECENT TRADES FROM ENGINE
# ---------------------------------------------------------
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown(f"#### 📜 Recent Matching Engine Trades ({selected_symbol})")

recent_trades = engine.get_recent_trades(selected_symbol, max_trades=15) if engine.is_available() else []
if recent_trades:
    df_tr = pd.DataFrame(recent_trades)
    df_tr["Execution Price"] = df_tr["price"].apply(lambda p: f"₹{p:,.2f}")
    df_tr["Turnover"] = df_tr.apply(lambda r: f"₹{(r['price'] * r['quantity']):,.2f}", axis=1)
    df_tr["Quantity"] = df_tr["quantity"].apply(lambda q: f"{q:,}")
    df_tr_disp = df_tr[["trade_id", "buy_order_id", "sell_order_id", "Execution Price", "Quantity", "Turnover", "sequence"]].copy()
    df_tr_disp.columns = ["Trade ID", "Buyer Order ID", "Seller Order ID", "Execution Price", "Quantity", "Turnover", "Sequence"]
    st.dataframe(df_tr_disp, use_container_width=True, hide_index=True)
else:
    st.info(f"No executions recorded yet for {selected_symbol}. Match Buy and Sell orders to see trade entries.")

st.markdown("</div>", unsafe_allow_html=True)
