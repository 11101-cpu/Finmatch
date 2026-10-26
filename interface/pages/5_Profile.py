"""
5_Profile.py - User Profile & Account Settings (Groww Light Theme)
Manage user credentials, practice capital faucet, portfolio reset, and account security.
"""

import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import FinMatchEngine
from style import apply_custom_style, render_top_navbar, render_disclaimer, GROWW_GREEN, GROWW_RED
import auth

st.set_page_config(page_title="Profile & Settings | FinMatch", page_icon="⚙️", layout="wide")
apply_custom_style()

if "user" not in st.session_state:
    st.session_state.user = auth.get_user_by_id(1)

user = st.session_state.user

if not user:
    st.info("Please log in from the Dashboard to access profile settings.")
    st.stop()

# Refresh user
fresh_user = auth.get_user_by_id(user["id"])
if fresh_user:
    st.session_state.user = fresh_user
    user = fresh_user

render_top_navbar(user, active_page="Profile")
render_disclaimer()

st.markdown("""
<div style='margin-bottom: 1.25rem;'>
    <div style='font-size: 1.6rem; font-weight: 800; color: #0F172A;'>⚙️ Account Profile & Preferences</div>
    <div style='font-size: 0.88rem; color: #64748B;'>
        Manage your simulated trading identity, virtual funds, and authentication security.
    </div>
</div>
""", unsafe_allow_html=True)

col_info, col_actions = st.columns([1.2, 1])

with col_info:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("#### 👤 Trader Profile")
    st.markdown(f"""
    - **Trader Full Name:** `{user['full_name']}`
    - **Registered Email:** `{user['email']}`
    - **Simulated Account ID:** `FM-USR-{user['id']:04d}`
    - **Account Tier:** `Paper Trading Sandbox (Academic DSA)`
    - **Available Simulated Capital:** `₹{user['cash_balance']:,.2f}`
    - **Account Creation Date:** `{user.get('created_at', '2026-10-26')[:10]}`
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    # Change Password Card
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("#### 🔒 Security & Password")
    with st.form("change_password_form"):
        new_pw = st.text_input("New Password (min 6 characters)", type="password")
        new_pw_conf = st.text_input("Confirm New Password", type="password")
        submit_pw = st.form_submit_button("Update Password", use_container_width=True)

        if submit_pw:
            ok, msg = auth.reset_password(user["email"], new_pw, new_pw_conf)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    st.markdown("</div>", unsafe_allow_html=True)

with col_actions:
    st.markdown("<div class='groww-card'>", unsafe_allow_html=True)
    st.markdown("#### 💰 Simulated Capital Controls")
    st.caption("Need extra practice funds or want to start fresh? Use the simulation controls below.")

    st.markdown("##### 1. Virtual Funds Faucet")
    if st.button("➕ Deposit ₹1,00,000 Practice Cash", use_container_width=True):
        ok, msg = auth.add_simulated_funds(user["id"], 100000.0)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("---")
    st.markdown("##### 2. Factory Reset Account")
    st.caption("Clears all your holdings, deletes your order history, and resets your balance back to ₹10,00,000.")
    if st.button("🔄 Reset Portfolio to ₹10,00,000", use_container_width=True):
        ok, msg = auth.reset_user_account(user["id"])
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("---")
    st.markdown("##### 3. Session Management")
    if st.button("🚪 Log Out of Session", use_container_width=True):
        st.session_state.user = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
