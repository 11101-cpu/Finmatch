"""
style.py - Shared styling and accessibility theme for FinMatch Trading Terminal.
Ensures WCAG AAA/AA contrast compliance, clear button states, readable charts, and dark trading aesthetics.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
    /* Global App Background & Text */
    .stApp {
        background-color: #0b0e14 !important;
        color: #f1f5f9 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    }

    /* Headings & Markdown */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }

    p, span, label {
        color: #e2e8f0 !important;
        font-size: 0.95rem;
    }

    /* Form Labels & Accessibility */
    .stTextInput>label, .stNumberInput>label, .stSelectbox>label, .stRadio>label {
        color: #f8fafc !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        margin-bottom: 4px !important;
    }

    /* Inputs Styling */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #151924 !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
    }

    /* Metric Cards */
    .metric-card {
        background: #151924;
        border: 1px solid #28334a;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    }
    .metric-title {
        font-size: 0.82rem;
        color: #cbd5e1 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    .metric-bid {
        color: #10b981 !important; /* High-contrast Emerald Green */
    }
    .metric-ask {
        color: #f43f5e !important; /* High-contrast Rose Red */
    }

    /* Standard & Form Buttons - Never Look Disabled */
    .stButton>button {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
        cursor: pointer !important;
        opacity: 1.0 !important;
        transition: all 0.15s ease-in-out !important;
    }
    .stButton>button:hover {
        background-color: #334155 !important;
        border-color: #64748b !important;
        color: #ffffff !important;
        transform: translateY(-1px);
    }
    .stButton>button:active {
        background-color: #0f172a !important;
        transform: translateY(0);
    }

    /* Primary Submit Button (Place Order) */
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        padding: 0.65rem 1.2rem !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35) !important;
        opacity: 1.0 !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        border-color: #60a5fa !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.5) !important;
    }

    /* Specific Danger Action (Cancel Order) */
    .cancel-btn-container button {
        background: #7f1d1d !important;
        color: #fee2e2 !important;
        border: 1px solid #ef4444 !important;
    }
    .cancel-btn-container button:hover {
        background: #991b1b !important;
        color: #ffffff !important;
        border-color: #f87171 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0f131c !important;
        border-right: 1px solid #1e2638 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: #cbd5e1 !important;
    }

    /* Simulation Badge */
    .badge-sim {
        background-color: #2e2105;
        color: #fde047;
        border: 1px solid #ca8a04;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    /* Table & Dataframe Contrast */
    .stDataFrame {
        border: 1px solid #232a3b !important;
        border-radius: 6px !important;
    }

    /* Captions with readable contrast */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
    }
</style>
"""

def apply_custom_style():
    """Injects high-contrast theme CSS into Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
