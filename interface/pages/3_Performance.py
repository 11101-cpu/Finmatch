"""
3_Performance.py - C Engine Performance & Hardware Benchmarks (Groww Light Theme)
Quantitative performance metrics of the core C11 matching engine measured with hardware high-resolution timers.
"""

import os
import sys
import json
import subprocess
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import FinMatchEngine
from style import apply_custom_style, render_top_navbar, render_disclaimer, GROWW_GREEN, GROWW_RED
import auth

st.set_page_config(page_title="Performance & Benchmarks | FinMatch", page_icon="⚡", layout="wide")
apply_custom_style()

if "engine" not in st.session_state:
    st.session_state.engine = FinMatchEngine()

if "user" not in st.session_state:
    st.session_state.user = auth.get_user_by_id(1)

engine: FinMatchEngine = st.session_state.engine
user = st.session_state.user

render_top_navbar(user, active_page="Performance")
render_disclaimer()

st.markdown("""
<div style='margin-bottom: 1.25rem;'>
    <div style='font-size: 1.6rem; font-weight: 800; color: #0F172A;'>⚡ Engine Performance & Hardware Benchmarks</div>
    <div style='font-size: 0.88rem; color: #64748B;'>
        Quantitative throughput and sub-microsecond latency measurements of the compiled C11 matching engine using hardware monotonic timers.
    </div>
</div>
""", unsafe_allow_html=True)

# Benchmark trigger controls
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown("#### 🚀 Standalone C Engine Benchmark")
st.markdown("Run a synthetic high-throughput benchmark directly on the compiled C binary without Python interpreter overhead.")

col_orders, col_btn = st.columns([2, 1])

with col_orders:
    order_count = st.select_slider(
        "Benchmark Workload Size (Synthetic Orders)",
        options=[10000, 25000, 50000, 100000, 250000],
        value=50000
    )

with col_btn:
    st.write("")
    st.write("")
    run_bench = st.button("▶️ Run Real-Time C Benchmark", use_container_width=True, help="Executes benchmarks/benchmark.exe and records hardware timings")

bench_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "benchmarks", "last_benchmark.json")

if run_bench:
    bench_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "benchmarks", "benchmark.exe")
    if not os.path.exists(bench_exe):
        st.error(f"Benchmark executable `{bench_exe}` not found. Please compile it first.")
    else:
        with st.spinner(f"Executing {order_count:,} orders in C matching engine..."):
            proc = subprocess.run([bench_exe, str(order_count)], capture_output=True, text=True)
            if proc.returncode == 0:
                st.success("Benchmark completed successfully!")
            else:
                st.error(f"Benchmark execution failed: {proc.stderr}")

st.markdown("</div>", unsafe_allow_html=True)

# Read and display benchmark results
bench_data = None
if os.path.exists(bench_json_path):
    try:
        with open(bench_json_path, "r") as f:
            bench_data = json.load(f)
    except Exception as e:
        st.warning(f"Could not read benchmark results: {e}")

if bench_data:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("#### 🏆 Measured Benchmark Results")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Throughput", f"{bench_data['orders_per_sec']:,.0f} ops/sec", "C Engine Execution")
    m2.metric("Total Duration", f"{bench_data['total_duration_sec']:.4f} sec", f"{bench_data['total_orders']:,} operations")
    m3.metric("Average Latency", f"{bench_data['avg_latency_us']:.2f} µs", "Per Operation")
    m4.metric("95th Percentile (p95)", f"{bench_data['p95_latency_us']:.2f} µs", "Latency Bound")
    st.markdown("</div>", unsafe_allow_html=True)

    col_chart, col_details = st.columns([1.5, 1])

    with col_chart:
        st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
        st.markdown("#### ⏱️ Latency Distribution (Microseconds)")
        percentiles = ["Min", "Median (p50)", "Average", "95th %ile (p95)", "99th %ile (p99)"]
        values = [
            bench_data.get("min_latency_us", 0.0),
            bench_data["median_latency_us"],
            bench_data["avg_latency_us"],
            bench_data["p95_latency_us"],
            bench_data["p99_latency_us"]
        ]

        fig = go.Figure(data=[
            go.Bar(
                x=percentiles,
                y=values,
                text=[f"{v:.2f} µs" for v in values],
                textposition='auto',
                marker=dict(color=['#00D09C', '#3B82F6', '#10B981', '#F59E0B', '#EF4444']),
                textfont=dict(color='#FFFFFF', size=11, family='Inter, sans-serif')
            )
        ])
        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", tickfont=dict(color="#64748B", size=11)),
            yaxis=dict(title="Latency (µs)", showgrid=True, gridcolor="#F1F5F9", tickfont=dict(color="#64748B", size=11))
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_details:
        st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
        st.markdown("#### 📊 Execution Breakdown")
        st.markdown(f"""
        - **Total Operations:** `{bench_data['total_orders']:,}`
        - **Matches Triggered:** `{bench_data.get('trades_executed', 0):,}`
        - **Shares Matched:** `{bench_data.get('total_shares_traded', 0):,}`
        - **Total Turnover:** `₹{bench_data.get('total_turnover', 0.0):,.2f}`
        - **Cancellations:** `{bench_data.get('successful_cancellations', 0):,}`
        - **Remaining Active Orders:** `{bench_data.get('remaining_orders', 0):,}`
        """)
        st.markdown("</div>", unsafe_allow_html=True)

# Data Structures Architecture Explanation
st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
st.markdown("#### 🧠 Core Algorithmic Architecture (DSA Implementation)")
col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.markdown(r"""
    ##### 1. Dual Heaps (Order Priority)
    - **Max-Heap for Bids:** Highest buy orders receive priority.
    - **Min-Heap for Asks:** Lowest sell orders receive priority.
    - Peek Best Bid/Ask in **$O(1)$** time.
    - Insert / Remove price levels in **$O(\log k)$** time.
    """)

with col_d2:
    st.markdown("""
    ##### 2. Doubly-Linked Lists (FIFO)
    - Orders resting at the exact same limit price form a FIFO queue.
    - Strict price-time priority guarantees fairness.
    - Append incoming order in **$O(1)$** time.
    - Instant node removal in **$O(1)$** on match or cancellation.
    """)

with col_d3:
    st.markdown("""
    ##### 3. Hash Table (Order Lookup)
    - Maps 64-bit `order_id` directly to its in-memory order pointer.
    - Average **$O(1)$** lookup time.
    - Enables instantaneous cancellation without linear book scanning.
    - Automatic collision resolution via chained buckets.
    """)

st.markdown("</div>", unsafe_allow_html=True)
