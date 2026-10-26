"""
market_data.py - Simulated Real-time Market Data Feed & Interactive Charting for FinMatch.
Provides consistent synthetic price histories across 1D, 1W, 1M, 3M, 1Y timeframes,
realistic market tick generation, and Groww-styled Plotly charts.
All prices are explicitly labelled as simulated.
"""

import time
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Catalog of Indian Stocks with realistic baseline anchors
STOCKS_CATALOG = {
    "RELIANCE": {
        "name": "Reliance Industries Ltd.",
        "sector": "Energy & Retail",
        "base_price": 2520.00,
        "lot_size": 1,
        "volatility": 0.0035,
    },
    "TCS": {
        "name": "Tata Consultancy Services Ltd.",
        "sector": "IT Services & Consulting",
        "base_price": 3865.00,
        "lot_size": 1,
        "volatility": 0.0028,
    },
    "INFY": {
        "name": "Infosys Ltd.",
        "sector": "IT & Cloud Services",
        "base_price": 1625.00,
        "lot_size": 1,
        "volatility": 0.0032,
    },
    "HDFCBANK": {
        "name": "HDFC Bank Ltd.",
        "sector": "Banking & Financial Services",
        "base_price": 1660.00,
        "lot_size": 1,
        "volatility": 0.0025,
    },
    "ICICIBANK": {
        "name": "ICICI Bank Ltd.",
        "sector": "Banking & Financial Services",
        "base_price": 1055.00,
        "lot_size": 1,
        "volatility": 0.0030,
    },
    "TATAMOTORS": {
        "name": "Tata Motors Ltd.",
        "sector": "Automotive & EV",
        "base_price": 965.00,
        "lot_size": 1,
        "volatility": 0.0045,
    },
    "SBIN": {
        "name": "State Bank of India",
        "sector": "Public Sector Banking",
        "base_price": 815.00,
        "lot_size": 1,
        "volatility": 0.0038,
    },
}

# Theme Colors inspired by Groww
GROWW_GREEN = "#00D09C"
GROWW_GREEN_FILL = "rgba(0, 208, 156, 0.12)"
GROWW_RED = "#EB5B3C"
GROWW_RED_FILL = "rgba(235, 91, 60, 0.12)"
GROWW_GRAY_TEXT = "#44475B"
GROWW_MUTED = "#8B95A5"
GROWW_BORDER = "#E5E7EB"
GROWW_BG_WHITE = "#FFFFFF"


def generate_synthetic_history(symbol: str, base_price: float, volatility: float) -> Dict[str, pd.DataFrame]:
    """
    Generates synthetic price series for 1D, 1W, 1M, 3M, 1Y views.
    Uses seeded pseudo-random walks ensuring smooth continuity up to base_price.
    """
    # Deterministic seed per symbol for consistency across sessions
    seed_val = sum(ord(c) for c in symbol) + 42
    rnd = random.Random(seed_val)

    now = datetime.now()
    histories = {}

    # --- 1D: Today's 5-minute intervals (09:15 AM to 15:30 PM, or up to 75 bars) ---
    today_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    num_1d_bars = 75
    times_1d = [today_start + timedelta(minutes=5 * i) for i in range(num_1d_bars)]
    
    # Random walk leading to base_price
    prices_1d = [base_price * (1.0 + rnd.uniform(-0.015, -0.005))]
    for _ in range(num_1d_bars - 1):
        step = rnd.gauss(0, volatility * base_price * 0.4)
        next_p = max(prices_1d[-1] + step, base_price * 0.5)
        prices_1d.append(next_p)
    # Anchor the last price to base_price
    prices_1d[-1] = base_price

    df_1d = pd.DataFrame({
        "timestamp": times_1d,
        "price": prices_1d,
        "open": [p - rnd.uniform(0.1, 1.0) for p in prices_1d],
        "high": [p + rnd.uniform(0.5, 2.5) for p in prices_1d],
        "low": [p - rnd.uniform(0.5, 2.5) for p in prices_1d],
        "close": prices_1d,
        "volume": [int(rnd.randint(500, 15000)) for _ in range(num_1d_bars)]
    })
    histories["1D"] = df_1d

    # --- 1W: 5 trading days with 15-minute bars (125 bars) ---
    num_1w_bars = 125
    times_1w = [now - timedelta(minutes=15 * (num_1w_bars - 1 - i)) for i in range(num_1w_bars)]
    p = base_price * (1.0 + rnd.uniform(-0.025, 0.025))
    prices_1w = [p]
    for _ in range(num_1w_bars - 1):
        step = rnd.gauss(0, volatility * base_price * 0.6)
        p = max(p + step, base_price * 0.5)
        prices_1w.append(p)
    prices_1w[-1] = base_price

    df_1w = pd.DataFrame({
        "timestamp": times_1w,
        "price": prices_1w,
        "open": [px - rnd.uniform(0.2, 1.5) for px in prices_1w],
        "high": [px + rnd.uniform(1.0, 4.0) for px in prices_1w],
        "low": [px - rnd.uniform(1.0, 4.0) for px in prices_1w],
        "close": prices_1w,
        "volume": [int(rnd.randint(1500, 35000)) for _ in range(num_1w_bars)]
    })
    histories["1W"] = df_1w

    # --- 1M: 30 days (daily bars) ---
    num_1m_bars = 30
    times_1m = [now - timedelta(days=num_1m_bars - 1 - i) for i in range(num_1m_bars)]
    p = base_price * (1.0 + rnd.uniform(-0.04, 0.04))
    prices_1m = [p]
    for _ in range(num_1m_bars - 1):
        step = rnd.gauss(0, volatility * base_price * 1.5)
        p = max(p + step, base_price * 0.5)
        prices_1m.append(p)
    prices_1m[-1] = base_price

    df_1m = pd.DataFrame({
        "timestamp": times_1m,
        "price": prices_1m,
        "open": [px - rnd.uniform(1.0, 5.0) for px in prices_1m],
        "high": [px + rnd.uniform(3.0, 15.0) for px in prices_1m],
        "low": [px - rnd.uniform(3.0, 15.0) for px in prices_1m],
        "close": prices_1m,
        "volume": [int(rnd.randint(10000, 150000)) for _ in range(num_1m_bars)]
    })
    histories["1M"] = df_1m

    # --- 3M: 90 days (daily bars) ---
    num_3m_bars = 90
    times_3m = [now - timedelta(days=num_3m_bars - 1 - i) for i in range(num_3m_bars)]
    p = base_price * (1.0 + rnd.uniform(-0.08, 0.08))
    prices_3m = [p]
    for _ in range(num_3m_bars - 1):
        step = rnd.gauss(0, volatility * base_price * 1.8)
        p = max(p + step, base_price * 0.5)
        prices_3m.append(p)
    prices_3m[-1] = base_price

    df_3m = pd.DataFrame({
        "timestamp": times_3m,
        "price": prices_3m,
        "open": [px - rnd.uniform(2.0, 8.0) for px in prices_3m],
        "high": [px + rnd.uniform(5.0, 25.0) for px in prices_3m],
        "low": [px - rnd.uniform(5.0, 25.0) for px in prices_3m],
        "close": prices_3m,
        "volume": [int(rnd.randint(20000, 250000)) for _ in range(num_3m_bars)]
    })
    histories["3M"] = df_3m

    # --- 1Y: 250 days (daily bars) ---
    num_1y_bars = 250
    times_1y = [now - timedelta(days=num_1y_bars - 1 - i) for i in range(num_1y_bars)]
    p = base_price * (1.0 + rnd.uniform(-0.15, 0.15))
    prices_1y = [p]
    for _ in range(num_1y_bars - 1):
        step = rnd.gauss(0, volatility * base_price * 2.2)
        p = max(p + step, base_price * 0.5)
        prices_1y.append(p)
    prices_1y[-1] = base_price

    df_1y = pd.DataFrame({
        "timestamp": times_1y,
        "price": prices_1y,
        "open": [px - rnd.uniform(3.0, 12.0) for px in prices_1y],
        "high": [px + rnd.uniform(8.0, 35.0) for px in prices_1y],
        "low": [px - rnd.uniform(8.0, 35.0) for px in prices_1y],
        "close": prices_1y,
        "volume": [int(rnd.randint(30000, 400000)) for _ in range(num_1y_bars)]
    })
    histories["1Y"] = df_1y

    return histories


class MarketDataFeed:
    """Singleton market data manager holding persistent simulated pricing states."""

    def __init__(self):
        self.stocks: Dict[str, Dict[str, Any]] = {}
        self._initialize_catalog()

    def _initialize_catalog(self):
        for sym, meta in STOCKS_CATALOG.items():
            base_p = meta["base_price"]
            histories = generate_synthetic_history(sym, base_p, meta["volatility"])
            # Derive previous close from 1D start or 1D first bar
            prev_close = round(histories["1D"]["price"].iloc[0], 2)
            curr_price = round(base_p, 2)
            abs_chg = round(curr_price - prev_close, 2)
            pct_chg = round((abs_chg / prev_close) * 100, 2) if prev_close else 0.0

            self.stocks[sym] = {
                "symbol": sym,
                "name": meta["name"],
                "sector": meta["sector"],
                "current_price": curr_price,
                "previous_close": prev_close,
                "open_price": round(histories["1D"]["open"].iloc[0], 2),
                "day_high": round(max(histories["1D"]["high"].max(), curr_price), 2),
                "day_low": round(min(histories["1D"]["low"].min(), curr_price), 2),
                "change_absolute": abs_chg,
                "change_percent": pct_chg,
                "is_positive": abs_chg >= 0,
                "volume": int(histories["1D"]["volume"].sum()),
                "histories": histories,
                "last_tick_time": time.time(),
            }

    def get_stock(self, symbol: str) -> Dict[str, Any]:
        """Returns stock pricing state, generating default state for custom symbols."""
        sym = symbol.upper()
        if sym not in self.stocks:
            base_p = 1000.00
            hist = generate_synthetic_history(sym, base_p, 0.003)
            self.stocks[sym] = {
                "symbol": sym,
                "name": f"{sym} Corporation",
                "sector": "Simulated Equities",
                "current_price": base_p,
                "previous_close": round(hist["1D"]["price"].iloc[0], 2),
                "open_price": base_p,
                "day_high": base_p * 1.01,
                "day_low": base_p * 0.99,
                "change_absolute": round(base_p - hist["1D"]["price"].iloc[0], 2),
                "change_percent": 0.0,
                "is_positive": True,
                "volume": 10000,
                "histories": hist,
                "last_tick_time": time.time(),
            }
        return self.stocks[sym]

    def update_from_engine_trade(self, symbol: str, trade_price: float, trade_qty: int):
        """Called whenever the C matching engine records a trade to keep charts in lockstep."""
        sym = symbol.upper()
        stock = self.get_stock(sym)
        stock["current_price"] = round(trade_price, 2)
        stock["day_high"] = round(max(stock["day_high"], trade_price), 2)
        stock["day_low"] = round(min(stock["day_low"], trade_price), 2)
        stock["volume"] += trade_qty

        abs_chg = round(trade_price - stock["previous_close"], 2)
        stock["change_absolute"] = abs_chg
        stock["change_percent"] = round((abs_chg / stock["previous_close"]) * 100, 2) if stock["previous_close"] else 0.0
        stock["is_positive"] = abs_chg >= 0

        # Append tick to 1D history
        df_1d = stock["histories"]["1D"]
        new_row = pd.DataFrame([{
            "timestamp": datetime.now(),
            "price": trade_price,
            "open": trade_price,
            "high": trade_price,
            "low": trade_price,
            "close": trade_price,
            "volume": trade_qty
        }])
        stock["histories"]["1D"] = pd.concat([df_1d, new_row], ignore_index=True)

    def simulate_tick(self, symbol: str, max_drift_pct: float = 0.0015):
        """Simulates an organic tick fluctuation."""
        sym = symbol.upper()
        stock = self.get_stock(sym)
        curr = stock["current_price"]
        delta = curr * random.gauss(0, max_drift_pct)
        new_price = round(max(1.0, curr + delta), 2)

        stock["current_price"] = new_price
        stock["day_high"] = round(max(stock["day_high"], new_price), 2)
        stock["day_low"] = round(min(stock["day_low"], new_price), 2)

        abs_chg = round(new_price - stock["previous_close"], 2)
        stock["change_absolute"] = abs_chg
        stock["change_percent"] = round((abs_chg / stock["previous_close"]) * 100, 2) if stock["previous_close"] else 0.0
        stock["is_positive"] = abs_chg >= 0

        df_1d = stock["histories"]["1D"]
        # Update last candle or append
        if not df_1d.empty:
            df_1d.loc[df_1d.index[-1], "close"] = new_price
            df_1d.loc[df_1d.index[-1], "price"] = new_price
            if new_price > df_1d.loc[df_1d.index[-1], "high"]:
                df_1d.loc[df_1d.index[-1], "high"] = new_price
            if new_price < df_1d.loc[df_1d.index[-1], "low"]:
                df_1d.loc[df_1d.index[-1], "low"] = new_price


def build_groww_chart(
    df: pd.DataFrame,
    symbol: str,
    chart_type: str = "line",
    is_positive: bool = True,
    previous_close: Optional[float] = None,
    height: int = 420
) -> go.Figure:
    """
    Renders a clean Groww-styled Plotly chart.
    Uses emerald green for upward movements and vibrant red for downward movements.
    """
    accent_color = GROWW_GREEN if is_positive else GROWW_RED
    fill_color = GROWW_GREEN_FILL if is_positive else GROWW_RED_FILL

    if chart_type.lower() == "candlestick":
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.8, 0.2]
        )

        # Candlestick Trace
        fig.add_trace(
            go.Candlestick(
                x=df["timestamp"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name=f"{symbol} (Simulated)",
                increasing_line_color=GROWW_GREEN,
                decreasing_line_color=GROWW_RED,
                increasing_fillcolor=GROWW_GREEN,
                decreasing_fillcolor=GROWW_RED,
                showlegend=False
            ),
            row=1, col=1
        )

        # Volume Bar Trace
        colors = [GROWW_GREEN if c >= o else GROWW_RED for c, o in zip(df["close"], df["open"])]
        fig.add_trace(
            go.Bar(
                x=df["timestamp"],
                y=df["volume"],
                marker_color=colors,
                opacity=0.4,
                name="Volume",
                showlegend=False
            ),
            row=2, col=1
        )

        fig.update_yaxes(title_text="Volume", row=2, col=1, showgrid=True, gridcolor="#F1F5F9", tickfont=dict(color=GROWW_MUTED, size=10))
    else:
        # Groww signature smooth line chart with gradient fill
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["price"],
                mode="lines",
                name=f"{symbol} (Simulated)",
                line=dict(color=accent_color, width=2.4, shape="spline"),
                fill="tozeroy",
                fillcolor=fill_color,
                hovertemplate="<b>₹%{y:,.2f}</b><br>%{x|%b %d, %H:%M}<extra></extra>"
            )
        )

    # Add previous close benchmark line if available
    if previous_close:
        fig.add_hline(
            y=previous_close,
            line_dash="dot",
            line_color="#94A3B8",
            line_width=1,
            annotation_text=f"Prev Close: ₹{previous_close:,.2f}",
            annotation_position="bottom right",
            annotation_font=dict(color="#64748B", size=10)
        )

    # Clean, airy Groww Light layout
    fig.update_layout(
        paper_bgcolor=GROWW_BG_WHITE,
        plot_bgcolor=GROWW_BG_WHITE,
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=GROWW_BG_WHITE,
            bordercolor=GROWW_BORDER,
            font=dict(color=GROWW_GRAY_TEXT, size=12, family="Inter, -apple-system, Segoe UI, sans-serif")
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#F3F4F6",
            zeroline=False,
            showline=False,
            tickfont=dict(color=GROWW_MUTED, size=11, family="Inter, sans-serif"),
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            side="right",
            showgrid=True,
            gridcolor="#F3F4F6",
            zeroline=False,
            showline=False,
            tickformat=",.2f",
            tickprefix="₹",
            tickfont=dict(color=GROWW_MUTED, size=11, family="Inter, sans-serif"),
        ),
        showlegend=False
    )

    return fig


def auto_seed_book_if_empty(engine: Any, symbol: str, current_price: float):
    """
    Ensures that an order book is never dead or blank by default.
    Seeds realistic institutional & market maker price levels around current price.
    """
    if not engine or not hasattr(engine, "is_available") or not engine.is_available():
        return
    book = engine.get_order_book(symbol)
    if book.get("total_bid_vol", 0) == 0 and book.get("total_ask_vol", 0) == 0:
        p = current_price
        # 5 Bids (Buyers)
        engine.place_order("MM_Alpha", symbol, "BUY", round(p * 0.998, 2), 100)
        engine.place_order("MM_Beta", symbol, "BUY", round(p * 0.995, 2), 250)
        engine.place_order("Institutional", symbol, "BUY", round(p * 0.990, 2), 500)
        engine.place_order("HedgeFund", symbol, "BUY", round(p * 0.985, 2), 750)
        engine.place_order("RetailPool", symbol, "BUY", round(p * 0.980, 2), 1200)

        # 5 Asks (Sellers)
        engine.place_order("MM_Alpha", symbol, "SELL", round(p * 1.002, 2), 120)
        engine.place_order("MM_Beta", symbol, "SELL", round(p * 1.005, 2), 280)
        engine.place_order("Institutional", symbol, "SELL", round(p * 1.010, 2), 460)
        engine.place_order("HedgeFund", symbol, "SELL", round(p * 1.015, 2), 800)
        engine.place_order("RetailPool", symbol, "SELL", round(p * 1.020, 2), 1150)
