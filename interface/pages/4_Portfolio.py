"""
4_Portfolio.py - Dedicated Portfolio & Holdings Analytics (Groww Light Theme)
Real-time tracking of simulated equity holdings, capital allocation, and unrealized P&L.
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

st.set_page_config(page_title="Portfolio | FinMatch", page_icon="💼", layout="wide")
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

if not user:
    st.info("Please log in from the Dashboard to view your simulated portfolio.")
    st.stop()

# Refresh user
fresh_user = auth.get_user_by_id(user["id"])
if fresh_user:
    st.session_state.user = fresh_user
    user = fresh_user

render_top_navbar(user, active_page="Portfolio")
render_navigation_bar(active_page="Portfolio")
render_disclaimer()

st.markdown("""
<div style='margin-bottom: 1.25rem;'>
    <div style='font-size: 1.6rem; font-weight: 800; color: #0F172A;'>💼 Simulated Portfolio & Asset Allocation</div>
    <div style='font-size: 0.88rem; color: #64748B;'>
        Real-time valuation of your stock holdings, unrealized returns, and historical order executions.
    </div>
</div>
""", unsafe_allow_html=True)

port = auth.get_user_portfolio(user["id"])
holdings = port["holdings"]
cash = user["cash_balance"]

total_holdings_value = 0.0
holdings_enriched = []

for h in holdings:
    sym = h["symbol"]
    stock_p = feed.get_stock(sym)["current_price"]
    val = stock_p * h["quantity"]
    total_holdings_value += val
    pnl = val - h["total_invested"]
    pct = (pnl / h["total_invested"] * 100) if h["total_invested"] > 0 else 0.0
    
    holdings_enriched.append({
        "symbol": sym,
        "quantity": h["quantity"],
        "avg_price": h["avg_buy_price"],
        "current_price": stock_p,
        "invested": h["total_invested"],
        "current_value": val,
        "pnl": pnl,
        "pnl_pct": pct
    })

total_portfolio_value = total_holdings_value + cash
total_invested = port["total_invested"]
total_pnl = total_holdings_value - total_invested
total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

# Portfolio Summary Cards
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Net Worth", f"₹{total_portfolio_value:,.2f}", "Holdings + Virtual Cash")
c2.metric("Total Invested", f"₹{total_invested:,.2f}", f"{len(holdings)} Stock Positions")

pnl_sign = "+" if total_pnl >= 0 else ""
c3.metric(
    "Total Profit / Loss",
    f"{pnl_sign}₹{total_pnl:,.2f}",
    f"{pnl_sign}{total_pnl_pct:.2f}%",
    delta_color="normal" if total_pnl >= 0 else "inverse"
)
c4.metric("Available Cash", f"₹{cash:,.2f}", "Simulated Capital")
st.markdown("</div>", unsafe_allow_html=True)

# Allocation & Holdings Row
col_chart, col_table = st.columns([1, 1.8])

with col_chart:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("#### 🍩 Asset Allocation")
    
    alloc_data = []
    for h in holdings_enriched:
        alloc_data.append({"Asset": h["symbol"], "Value": h["current_value"]})
    alloc_data.append({"Asset": "Virtual Cash", "Value": cash})

    df_alloc = pd.DataFrame(alloc_data)
    fig_donut = px.pie(
        df_alloc,
        names="Asset",
        values="Value",
        hole=0.55,
        color_discrete_sequence=["#00D09C", "#3B82F6", "#8B5CF6", "#F59E0B", "#10B981", "#64748B"]
    )
    fig_donut.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=-0.1, x=0, font=dict(size=10))
    )
    st.plotly_chart(fig_donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_table:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("#### 📋 Active Positions")

    if holdings_enriched:
        display_list = []
        for h in holdings_enriched:
            sign = "+" if h["pnl"] >= 0 else ""
            display_list.append({
                "Stock": h["symbol"],
                "Quantity": f"{h['quantity']:,}",
                "Avg Price": f"₹{h['avg_price']:,.2f}",
                "Current Price": f"₹{h['current_price']:,.2f}",
                "Current Value": f"₹{h['current_value']:,.2f}",
                "Unrealized P&L": f"{sign}₹{h['pnl']:,.2f} ({sign}{h['pnl_pct']:.2f}%)"
            })
        st.dataframe(pd.DataFrame(display_list), use_container_width=True, hide_index=True, height=270)
    else:
        st.info("No active holdings found. Trade on the Dashboard to build your portfolio.")

    st.markdown("</div>", unsafe_allow_html=True)

# User's Orders History from SQLite
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown("#### 📑 Your Order History")

user_orders = auth.get_user_orders(user["id"])
if user_orders:
    df_o = pd.DataFrame(user_orders)
    df_o["Price"] = df_o["price"].apply(lambda p: f"₹{p:,.2f}")
    df_o["Side"] = df_o["side"].apply(lambda s: "🟢 BUY" if s == "BUY" else "🔴 SELL")
    df_o["Order ID"] = df_o["order_id"].apply(lambda oid: f"#{oid}")
    df_o["Status"] = df_o["status"]
    df_o["Shares"] = df_o["quantity"]
    df_o["Filled"] = df_o["filled_qty"]
    df_o["Remaining"] = df_o["remaining_qty"]
    df_o["Time"] = df_o["created_at"].apply(lambda t: t[:19].replace("T", " "))

    disp_cols = ["Order ID", "Time", "symbol", "Side", "Price", "Shares", "Filled", "Remaining", "Status"]
    df_o_disp = df_o[disp_cols].rename(columns={"symbol": "Stock"})
    st.dataframe(df_o_disp, use_container_width=True, hide_index=True)
else:
    st.info("No orders placed yet under this account.")

st.markdown("</div>", unsafe_allow_html=True)
