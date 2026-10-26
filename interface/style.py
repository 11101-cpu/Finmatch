"""
style.py - Groww-inspired Premium Light Theme for FinMatch Trading Simulator.
Provides clean light UI aesthetics, white/light-gray surfaces, emerald green & coral red accents,
accessible typography, and custom CSS for Streamlit components.
"""

import streamlit as st

GROWW_GREEN = "#00D09C"
GROWW_RED = "#EB5B3C"
GROWW_TEXT_DARK = "#0F172A"
GROWW_MUTED = "#64748B"
GROWW_BORDER = "#E5E7EB"

GROWW_LIGHT_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global App Container */
    .stApp {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    /* Streamlit top header: transparent and non-blocking */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: none !important;
        height: 2.75rem !important;
        z-index: 99 !important;
    }

    /* Sidebar Toggle Button always accessible */
    button[data-testid="collapsedControl"],
    button[data-testid="stSidebarCollapseButton"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
        top: 0.5rem !important;
        left: 0.5rem !important;
        z-index: 1000 !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    p, span, label, div {
        color: #334155;
    }

    /* Streamlit Main Block Padding across all Streamlit versions */
    .block-container, div[data-testid="stMainBlockContainer"] {
        padding-top: 3.5rem !important;
        padding-bottom: 4rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1400px !important;
    }

    /* Groww Page Link Navigation Pills */
    div[data-testid="stPageLink-NavLink"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.85rem !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: #1E293B !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.15s ease !important;
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    div[data-testid="stPageLink-NavLink"]:hover {
        background-color: #F8FAFC !important;
        border-color: #00D09C !important;
        color: #00875A !important;
        transform: translateY(-1px);
    }
    div[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background-color: #E8FAF4 !important;
        border-color: #00D09C !important;
        color: #00875A !important;
        font-weight: 700 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB !important;
        box-shadow: 1px 0 3px rgba(0, 0, 0, 0.02) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #0F172A !important;
    }
    [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] p {
        color: #475569 !important;
    }

    /* Form Inputs (Groww Style: subtle border, rounded-lg, crisp focus) */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding: 0.5rem 0.75rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #00D09C !important;
        box-shadow: 0 0 0 3px rgba(0, 208, 156, 0.18) !important;
        outline: none !important;
    }

    /* Labels */
    .stTextInput > label, .stNumberInput > label, .stSelectbox > label, .stRadio > label {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        margin-bottom: 4px !important;
    }

    /* Standard Buttons */
    .stButton > button {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
    }
    .stButton > button:active {
        background-color: #F1F5F9 !important;
        transform: translateY(1px);
    }

    /* Form Primary Submit Button (Emerald Green Buy Button) */
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #00D09C !important;
        color: #FFFFFF !important;
        border: 1px solid #00B386 !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.25rem !important;
        box-shadow: 0 2px 4px rgba(0, 208, 156, 0.25) !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #00B386 !important;
        border-color: #009973 !important;
        box-shadow: 0 4px 8px rgba(0, 208, 156, 0.35) !important;
    }

    /* Custom Classes for Groww UI Cards */
    .groww-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
        margin-bottom: 1rem;
    }

    .groww-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 0.9rem 1.5rem;
        margin-top: 0.5rem !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        margin-bottom: 1.25rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        position: relative;
        z-index: 1;
    }

    .brand-logo {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-weight: 800;
        font-size: 1.35rem;
        color: #0F172A !important;
        letter-spacing: -0.03em;
    }

    .brand-badge {
        background: #E8FAF4;
        color: #00875A;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid rgba(0, 208, 156, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .sim-banner {
        background-color: #FEF3C7;
        border: 1px solid #F59E0B;
        color: #92400E;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1.2rem;
    }

    /* Stock Quote Hero Area */
    .stock-hero {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 1rem;
    }

    .stock-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 2px;
    }

    .stock-subtitle {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 10px;
    }

    .stock-price-main {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }

    .badge-positive {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        color: #00D09C;
        font-weight: 700;
        font-size: 0.95rem;
        background: #E8FAF4;
        padding: 4px 10px;
        border-radius: 6px;
    }

    .badge-negative {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        color: #EB5B3C;
        font-weight: 700;
        font-size: 0.95rem;
        background: #FDF2F0;
        padding: 4px 10px;
        border-radius: 6px;
    }

    /* Metric Stat Box */
    .stat-box {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 12px 14px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    .stat-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .stat-val {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
    }
    .stat-green {
        color: #00D09C !important;
    }
    .stat-red {
        color: #EB5B3C !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 4px;
        border-radius: 8px;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: #64748B !important;
        padding: 6px 16px !important;
        border: none !important;
        background-color: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    /* Streamlit DataFrame styling */
    [data-testid="stDataFrame"] {
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    /* Badges & Tags */
    .status-open {
        background-color: #EFF6FF;
        color: #2563EB;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .status-filled {
        background-color: #E8FAF4;
        color: #00875A;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .status-partial {
        background-color: #FEF3C7;
        color: #D97706;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .status-cancelled {
        background-color: #FEE2E2;
        color: #DC2626;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
    }
</style>
"""


def apply_custom_style():
    """Injects the Groww-inspired light theme CSS into the current Streamlit page."""
    st.markdown(GROWW_LIGHT_CSS, unsafe_allow_html=True)


def render_top_navbar(user: dict = None, active_page: str = "Dashboard"):
    """Renders a polished Groww-inspired top navigation bar."""
    name_display = user.get("full_name", "Demo User") if user else "Guest Trader"
    initials = "".join([part[0] for part in name_display.split()[:2]]).upper() if name_display else "GT"
    balance = user.get("cash_balance", 0.0) if user else 0.0

    st.markdown(
        f"""
        <div class="groww-header">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div class="brand-logo">
                    <span style="color:#00D09C; font-size:1.6rem;">●</span> FinMatch
                </div>
                <span class="brand-badge">Simulated Trading</span>
                <span style="font-size: 0.82rem; color: #64748B; font-weight: 500;">
                    NSE • <span style="color:#00D09C; font-weight:700;">Simulated Open</span>
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 18px;">
                <div style="text-align: right;">
                    <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">SIMULATED CASH</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: #0F172A;">₹{balance:,.2f}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px; background: #F1F5F9; padding: 4px 12px 4px 6px; border-radius: 20px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background: #00D09C; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.78rem;">
                        {initials}
                    </div>
                    <span style="font-size: 0.85rem; font-weight: 600; color: #1E293B;">{name_display}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_navigation_bar(active_page: str = "Dashboard"):
    """Renders prominent Groww top navigation pill tabs at the top of every page."""
    nav_cols = st.columns(6)
    pages = [
        ("Dashboard", "app.py", "📈"),
        ("Order Book", "pages/1_Order_Book.py", "📖"),
        ("Portfolio", "pages/4_Portfolio.py", "💼"),
        ("Trade History", "pages/2_Trade_History.py", "📜"),
        ("Performance", "pages/3_Performance.py", "⚡"),
        ("Profile", "pages/5_Profile.py", "⚙️"),
    ]
    for col, (name, path, icon) in zip(nav_cols, pages):
        with col:
            is_active = (active_page.lower() == name.lower())
            st.page_link(
                path,
                label=name,
                icon=icon,
                disabled=is_active,
                use_container_width=True
            )
    st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)


def render_disclaimer():
    """Renders a clear simulation disclaimer required by financial simulation apps."""
    st.markdown(
        """
        <div class="sim-banner">
            <span>⚠️</span>
            <span><b>Educational Simulation Environment:</b> FinMatch is a paper-trading simulator powered by a high-performance C11 matching engine. No real capital or actual market execution is involved.</span>
        </div>
        """,
        unsafe_allow_html=True
    )
