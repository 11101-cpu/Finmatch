"""
FinMatch - Page 3: Performance & Benchmarks
High-resolution metrics of the compiled C11 matching engine
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import subprocess
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import FinMatchEngine
from style import apply_custom_style

st.set_page_config(page_title="Performance & Benchmarks | FinMatch", page_icon="⚡", layout="wide")

apply_custom_style()

st.title("⚡ Engine Performance & Hardware Benchmarks")
st.caption("Quantitative performance metrics of the core C matching engine measured with hardware high-resolution timers.")

# Benchmark trigger controls
st.subheader("🚀 Standalone C Engine Benchmark")
st.markdown("Run a synthetic benchmark workload on the compiled C engine without GUI or Python interpreter overhead.")

col_orders, col_btn = st.columns([2, 1])

with col_orders:
    order_count = st.select_slider(
        "Benchmark Workload Size (Synthetic Operations)",
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

# Read and display benchmark results
bench_data = None
if os.path.exists(bench_json_path):
    try:
        with open(bench_json_path, "r") as f:
            bench_data = json.load(f)
    except Exception as e:
        st.warning(f"Could not read benchmark results: {e}")

if bench_data:
    st.markdown("### 🏆 Measured Benchmark Results")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Throughput", f"{bench_data['orders_per_sec']:,.0f} ops/sec", "C Engine Execution")
    m2.metric("Total Duration", f"{bench_data['total_duration_sec']:.4f} sec", f"{bench_data['total_orders']:,} operations")
    m3.metric("Average Latency", f"{bench_data['avg_latency_us']:.2f} µs", "Per Operation")
    m4.metric("95th Percentile (p95)", f"{bench_data['p95_latency_us']:.2f} µs", "Latency Bound")

    st.markdown("---")

    col_chart, col_details = st.columns([1.5, 1])

    with col_chart:
        st.subheader("⏱️ Latency Distribution (Microseconds)")
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
                textfont=dict(color="#ffffff", size=11, family="sans-serif"),
                marker=dict(color=['#38bdf8', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'])
            )
        ])
        fig.update_layout(
            paper_bgcolor="#151924",
            plot_bgcolor="#151924",
            font=dict(color="#f8fafc", size=12),
            height=320,
            yaxis=dict(
                title=dict(text="Latency (Microseconds µs)", font=dict(color="#f8fafc", size=12)),
                gridcolor="#28334a",
                tickfont=dict(color="#cbd5e1", size=11)
            ),
            xaxis=dict(
                gridcolor="#28334a",
                tickfont=dict(color="#cbd5e1", size=11)
            ),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_details:
        st.subheader("📊 Workload & Methodology")
        st.markdown(f"""
        <div class='benchmark-card'>
            <p><strong>Total Operations:</strong> {bench_data['total_orders']:,}</p>
            <p><strong>Trades Generated:</strong> {bench_data['trades_executed']:,}</p>
            <p><strong>Shares Matched:</strong> {bench_data['total_shares_traded']:,}</p>
            <p><strong>Active Orders Remaining:</strong> {bench_data['active_orders_remaining']:,}</p>
            <p><strong>Timing Methodology:</strong> Monotonic <code>QueryPerformanceCounter</code></p>
            <p><strong>Architecture:</strong> x86_64 C11 Native Windows</p>
            <p><strong>Optimization:</strong> GCC <code>-O3</code> Native Vectorization</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Run the benchmark using the button above to view latency metrics.")

st.markdown("---")

# Data Structures & Algorithms Complexity Analysis
st.subheader("📚 Data Structure Complexity Analysis")
st.markdown("Comparison of FinMatch's Hybrid Priority Queue architecture vs naive implementations:")

dsa_data = {
    "Operation": [
        "Peek Best Price (Bid/Ask)",
        "Insert New Price Level",
        "Insert Order at Existing Level",
        "Match Best Order (Head)",
        "Cancel Arbitrary Order",
        "Prune Empty Price Level"
    ],
    "FinMatch Architecture": [
        "O(1) - Heap Top",
        "O(log P) - Heap Push",
        "O(1) - Queue Push Tail",
        "O(1) - Queue Pop Head",
        "O(1) - Doubly Linked List Node Remove",
        "O(log P) - Heap Remove via Index"
    ],
    "Naive Flat Array": [
        "O(N) - Linear Scan",
        "O(N) - Shift Array",
        "O(N) - Scan or Append",
        "O(N) - Shift Array",
        "O(N) - Search and Shift",
        "O(N) - Rebuild Array"
    ],
    "Balanced BST (Red-Black / AVL)": [
        "O(log P) - Min/Max Search",
        "O(log P) - Tree Insert",
        "O(log P) - Tree Search + Append",
        "O(log P) - Delete Node",
        "O(log P) - Search & Delete",
        "O(log P) - Delete Node"
    ]
}

df_dsa = pd.DataFrame(dsa_data)
st.dataframe(df_dsa, use_container_width=True, hide_index=True)
st.caption("*Where N = total number of orders in book, P = number of distinct active price levels (typically P << N).*")
