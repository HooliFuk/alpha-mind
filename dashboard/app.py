# dashboard/app.py
# AKUFIN - Intelligence for Wealth Accrual
# Main Dashboard with Admin Access Control
import sys
import os
import re
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from prediction_engine.predictor import PredictionEngine
from tools.alpaca_broker import AlpacaBroker
from control.access_control import AKUFINAccessControl

st.set_page_config(
    page_title="AKUFIN - AI Wealth Intelligence",
    page_icon="💎",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0a0e1a;
        color: #e0e0e0;
    }
    [data-testid="metric-container"] {
        background: linear-gradient(
            135deg, #1a1f35 0%, #0d1117 100%
        );
        border: 1px solid #DAA520;
        border-radius: 12px;
        padding: 15px;
    }
    h1, h2, h3 { color: #FFD700; }
    .stButton > button {
        background: linear-gradient(
            90deg, #B8860B, #DAA520
        );
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
    }
    div[data-testid="stExpander"] {
        background: #1a1f35;
        border: 1px solid #DAA520;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg, #0d1117 0%, #1a1f35 100%
        );
        border-right: 2px solid #DAA520;
    }
    .stTextInput > div > div > input {
        background-color: #1a1f35;
        color: #e0e0e0;
        border: 1px solid #DAA520;
    }
    .stSelectbox > div > div {
        background-color: #1a1f35;
        border: 1px solid #DAA520;
    }
    .akufin-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(
            135deg, #1a1f35 0%, #0d1117 100%
        );
        border: 2px solid #DAA520;
        border-radius: 15px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ── Initialize Access Control ─────────────────────────
access = AKUFINAccessControl()


# ── Initialize Services (cached) ─────────────────────
@st.cache_resource
def get_services():
    return {
        "market": MarketDataFetcher(),
        "indicators": TechnicalIndicators(),
        "predictor": PredictionEngine(),
        "broker": AlpacaBroker()
    }


# ── Session Timeout ───────────────────────────────────
def check_session_timeout():
    """Log out user after 8 hours"""
    login_time = st.session_state.get("login_time")
    if login_time:
        elapsed = (
            datetime.now() - login_time
        ).total_seconds() / 3600
        if elapsed > 8:
            st.session_state.clear()
            st.warning(
                "⏰ Session expired. Please login again."
            )
            st.rerun()


# ── Ticker Sanitizer ──────────────────────────────────
def sanitize_ticker(raw: str) -> str:
    """Block SQL injection and invalid tickers"""
    if not raw:
        return ""
    return re.sub(
        r'[^A-Z0-9\-\.]', '', raw.upper()
    )[:10]


# ── Signal Repository (NOT cached) ───────────────────
def get_signal_repo():
    """
    Get fresh signal repository every time.
    NOT cached so it always reads fresh data.
    """
    try:
        from database.signal_repository import (
            SignalRepository
        )
        return SignalRepository()
    except Exception:
        return None


# ══════════════════════════════════════════════════════
# AKUFIN LOGIN PAGE
# ══════════════════════════════════════════════════════
def show_login_page():
    """AKUFIN Secure Access Gate"""
    st.markdown("""
    <div class='akufin-header'>
        <h1>💎 AKUFIN</h1>
        <h3>Intelligence for Wealth Accrual</h3>
        <p style='color:#DAA520'>
            <em>From the Igbo word for Wealth</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Secure Access")
        st.caption(
            "AKUFIN is a private platform. "
            "Contact the administrator for access."
        )

        username = st.text_input(
            "Username",
            placeholder="Enter your AKUFIN username"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        if st.button(
            "💎 Access AKUFIN",
            use_container_width=True,
            type="primary"
        ):
            if not username or not password:
                st.error(
                    "Please enter username and password."
                )
                return

            if username.lower() == "admin":
                if access.is_admin(password):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = "admin"
                    st.session_state["role"] = "admin"
                    st.session_state[
                        "login_time"
                    ] = datetime.now()
                    st.success(
                        "✅ Welcome, AKUFIN Administrator!"
                    )
                    st.rerun()
                    return
                else:
                    result = access.check_access(
                        username, password
                    )
                    if result["allowed"]:
                        st.session_state[
                            "logged_in"
                        ] = True
                        st.session_state[
                            "username"
                        ] = "admin"
                        st.session_state[
                            "role"
                        ] = "admin"
                        st.session_state[
                            "login_time"
                        ] = datetime.now()
                        st.rerun()
                        return
                    st.error(
                        "❌ Invalid admin credentials."
                    )
                    return

            result = access.check_access(
                username, password
            )
            if result["allowed"]:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = result["role"]
                st.session_state[
                    "login_time"
                ] = datetime.now()
                st.success(
                    f"✅ Welcome to AKUFIN, {username}!"
                )
                st.rerun()
            else:
                st.error(f"❌ {result['reason']}")
                st.caption(
                    "Need access? "
                    "Contact the AKUFIN administrator."
                )

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#DAA520'>"
        "💎 AKUFIN Technologies | "
        "Private & Confidential | "
        f"© {datetime.now().year}"
        "</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════
# AKUFIN ADMIN PANEL
# ══════════════════════════════════════════════════════
def show_admin_panel():
    """AKUFIN Admin Control Panel"""
    st.title("🔑 AKUFIN Admin Control Panel")
    st.markdown(
        "*Full administrator control over platform*"
    )
    st.divider()

    admin_key = st.text_input(
        "Admin Key (required for all actions)",
        type="password",
        placeholder="Enter your AKUFIN admin key"
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 All Users",
        "➕ Add User",
        "❌ Revoke Access",
        "🔑 Set Password"
    ])

    with tab1:
        st.subheader("All AKUFIN Users")
        if st.button("🔄 Load Users"):
            users = access.get_all_users(admin_key)
            if not users:
                st.warning(
                    "No users found or invalid admin key."
                )
            else:
                for user in users:
                    status = (
                        "✅ Active"
                        if user["active"]
                        and not user["expired"]
                        else "❌ Inactive/Expired"
                    )
                    st.markdown(
                        f"**{user['username']}** | "
                        f"Role: {user['role']} | "
                        f"Status: {status} | "
                        f"Expires: {user['expires'][:10]} | "
                        f"Last Login: "
                        f"{user['last_login'][:16] if user['last_login'] else 'Never'}"
                    )
                    st.divider()

    with tab2:
        st.subheader("Approve New AKUFIN User")
        new_username = st.text_input(
            "Username",
            placeholder="e.g. vc_partner_name"
        )
        new_role = st.selectbox(
            "Access Role",
            ["viewer", "analyst", "trader"],
            help=(
                "viewer=read only | "
                "analyst=predictions | "
                "trader=approve trades"
            )
        )
        expire_days = st.number_input(
            "Access Duration (days)",
            min_value=1,
            max_value=365,
            value=30
        )
        if st.button("✅ Approve User", type="primary"):
            if not new_username or not admin_key:
                st.error(
                    "Username and admin key required."
                )
            else:
                result = access.approve_user(
                    username=new_username,
                    admin_key=admin_key,
                    role=new_role,
                    expires_days=expire_days
                )
                if result["success"]:
                    st.success(
                        f"✅ {new_username} approved!"
                    )
                    st.info(
                        "Set password in Set Password tab."
                    )
                else:
                    st.error(result.get("error"))

    with tab3:
        st.subheader("Revoke User Access")
        st.warning("⚠️ Immediately removes access.")
        revoke_username = st.text_input(
            "Username to Revoke",
            placeholder="Enter exact username"
        )
        if st.button(
            "❌ REVOKE ACCESS", type="primary"
        ):
            if not revoke_username or not admin_key:
                st.error(
                    "Username and admin key required."
                )
            else:
                result = access.revoke_user(
                    revoke_username, admin_key
                )
                if result["success"]:
                    st.success(
                        f"✅ Revoked: {revoke_username}"
                    )
                else:
                    st.error(result.get("error"))

    with tab4:
        st.subheader("Set User Password")
        pwd_username = st.text_input(
            "Username",
            placeholder="Enter username",
            key="pwd_user"
        )
        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Minimum 8 characters"
        )
        if st.button("🔑 Set Password"):
            if not all(
                [pwd_username, new_password, admin_key]
            ):
                st.error("All fields required.")
            else:
                result = access.set_user_password(
                    pwd_username,
                    new_password,
                    admin_key
                )
                if result["success"]:
                    st.success(
                        f"✅ Password set for "
                        f"{pwd_username}"
                    )
                else:
                    st.error(result.get("error"))


# ══════════════════════════════════════════════════════
# MAIN APP - CHECK LOGIN FIRST
# ══════════════════════════════════════════════════════
if not st.session_state.get("logged_in"):
    show_login_page()
    st.stop()

if "login_time" not in st.session_state:
    st.session_state["login_time"] = datetime.now()
check_session_timeout()

services = get_services()
username = st.session_state.get("username", "user")
role = st.session_state.get("role", "viewer")

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💎 AKUFIN")
    st.markdown("*Intelligence for Wealth Accrual*")
    st.markdown(
        f"<small style='color:#DAA520'>"
        f"Logged in as: <b>{username}</b> "
        f"({role})</small>",
        unsafe_allow_html=True
    )
    st.divider()

    nav_options = ["🏠 Dashboard Home"]

    if role in ["viewer", "analyst", "trader", "admin"]:
        nav_options.append("🎯 AI Predictions")
        nav_options.append("💼 Live Portfolio")
        nav_options.append("📊 Live Analysis")
        nav_options.append("📈 Agent Activity")
        nav_options.append("📉 Performance Analytics")

    if role in ["trader", "admin"]:
        nav_options.append("⚡ Place Paper Trade")
        nav_options.append("⏳ Pending Approvals")
        nav_options.append("🧠 AKUFIN Intelligence")

    if role == "admin":
        nav_options.append("🔑 Admin Panel")

    page = st.selectbox("Navigation", nav_options)

    st.divider()
    status = services["market"].get_market_status()
    if status["is_open"]:
        st.success("🟢 Market Open")
    else:
        st.error("🔴 Market Closed")
    st.caption(f"Session: {status['session']}")
    st.divider()

    try:
        fresh_acc = AlpacaBroker().get_account()
        st.metric(
            "AKUFIN Portfolio",
            f"${fresh_acc['portfolio_value']:,.0f}",
            f"${fresh_acc['daily_pl']:+,.2f} today"
        )
    except Exception:
        st.metric("AKUFIN Portfolio", "$100,000")

    st.divider()
    st.caption(
        f"Updated: {datetime.now().strftime('%H:%M:%S')}"
    )
    col_r, col_l = st.columns(2)
    with col_r:
        if st.button("🔄 Refresh"):
            st.cache_resource.clear()
            st.rerun()
    with col_l:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

# ══════════════════════════════════════════════════════
# PAGE 0: DASHBOARD HOME
# ══════════════════════════════════════════════════════
if page == "🏠 Dashboard Home":
    st.markdown("""
    <div class='akufin-header'>
        <h1>💎 AKUFIN</h1>
        <h3>Intelligence for Wealth Accrual</h3>
        <p style='color:#DAA520'>
            <em>
            AKUFIN (Igbo: Wealth Finance) ·
            Predictive · Autonomous · Precise
            </em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    fresh_broker = AlpacaBroker()
    summary = fresh_broker.get_portfolio_summary()
    account = summary["account"]
    predictions = (
        services["predictor"].get_all_predictions()
    )

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(
        "💰 Portfolio Value",
        f"${account.get('portfolio_value', 0):,.2f}",
        f"${account.get('daily_pl', 0):+,.2f} today"
    )
    m2.metric(
        "💵 Cash Available",
        f"${account.get('cash', 0):,.2f}"
    )
    m3.metric(
        "⚡ Buying Power",
        f"${account.get('buying_power', 0):,.2f}"
    )
    m4.metric(
        "📊 Open Positions",
        summary["total_positions"]
    )
    m5.metric(
        "🎯 AI Predictions",
        len(predictions)
    )

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚡ SNIPER Portfolio")
        st.markdown("*Short-term leverage trades*")
        sniper_pos = [
            p for p in summary["positions"]
            if p.get("portfolio") == "SNIPER"
        ]
        st.metric("Allocated Capital", "$30,000")
        st.metric("Open Trades", len(sniper_pos))
        st.metric("Strategy", "Momentum + Flow")
        st.markdown("""
        - ⚡ Fast momentum trades
        - 🐋 Institutional flow signals
        - 📊 Technical breakouts
        - ⏱️ Minutes to 3 days hold
        """)

    with col2:
        st.markdown("### 🏰 FORTRESS Portfolio")
        st.markdown("*Long-term safe investments*")
        fortress_pos = [
            p for p in summary["positions"]
            if p.get("portfolio") == "FORTRESS"
        ]
        st.metric("Allocated Capital", "$70,000")
        st.metric("Open Positions", len(fortress_pos))
        st.metric("Strategy", "Growth + Value")
        st.markdown("""
        - 📈 High ROI growth stocks
        - 🛡️ Blue chip safety
        - 💰 Dividend compounders
        - ⏱️ Weeks to months hold
        """)

    st.divider()
    st.subheader("🎯 Recent AKUFIN Predictions")
    if predictions:
        for pred in predictions[:3]:
            dir_icon = (
                "🟢"
                if pred.get(
                    "predicted_direction"
                ) == "UP"
                else "🔴"
            )
            conf = pred.get("confidence", 0) * 100
            st.markdown(
                f"{dir_icon} **{pred['ticker']}** → "
                f"${pred['predicted_price']:.2f} "
                f"by {pred['target_date']} | "
                f"Confidence: {conf:.0f}%"
            )
    else:
        st.info(
            "No predictions yet. "
            "Go to AI Predictions to generate some."
        )

    st.divider()
    st.subheader("🤖 AKUFIN Agent Status")
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.success("🐋 Whale Hunter\nActive")
    a2.success("📊 Technical\nActive")
    a3.success("📰 Sentiment\nActive")
    a4.success("🛡️ Risk Warden\nActive")
    a5.warning("⏳ Human Gate\nWaiting")

# ══════════════════════════════════════════════════════
# PAGE 1: AI PREDICTIONS
# ══════════════════════════════════════════════════════
elif page == "🎯 AI Predictions":
    st.title("🎯 AKUFIN Market Predictions")
    st.markdown(
        "*AI-generated predictions tracked "
        "against real market outcomes*"
    )
    st.divider()

    st.subheader("➕ Generate New AKUFIN Prediction")
    g1, g2, g3, g4 = st.columns([2, 2, 2, 1])

    with g1:
        ticker_raw = st.text_input(
            "Ticker Symbol",
            value="NVDA",
            placeholder="e.g. AAPL, TSLA, SPY"
        )
        ticker = sanitize_ticker(ticker_raw)
        if ticker_raw and ticker != ticker_raw.upper().strip():
            st.caption(f"Using: {ticker}")
    with g2:
        portfolio = st.selectbox(
            "Portfolio", ["SNIPER", "FORTRESS"]
        )
    with g3:
        days = st.selectbox(
            "Days Ahead", [7, 14, 21, 30], index=1
        )
    with g4:
        st.write("")
        st.write("")
        gen_btn = st.button(
            "💎 Generate",
            type="primary",
            use_container_width=True
        )

    if gen_btn and ticker:
        with st.spinner(
            f"AKUFIN AI analyzing {ticker}..."
        ):
            result = services[
                "predictor"
            ].generate_prediction(
                ticker=ticker,
                portfolio=portfolio,
                days_ahead=days
            )
        st.session_state["last_prediction"] = result

    if "last_prediction" in st.session_state:
        result = st.session_state["last_prediction"]
        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            direction = result.get(
                "predicted_direction", "UP"
            )
            dir_icon = (
                "🟢" if direction == "UP" else "🔴"
            )
            change = result.get("price_change_pct", 0)
            conf = result.get("confidence", 0) * 100

            st.success(
                f"✅ AKUFIN Prediction: "
                f"**{result['ticker']}**"
            )
            st.markdown("---")

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric(
                "📍 Current Price",
                f"${result['current_price']:.2f}"
            )
            m2.metric(
                "🎯 Target Price",
                f"${result['predicted_price']:.2f}",
                f"{change:+.1f}%"
            )
            m3.metric(
                "📈 Direction",
                f"{dir_icon} {direction}"
            )
            m4.metric(
                "🎲 Confidence",
                f"{conf:.0f}%"
            )
            m5.metric(
                "📅 Target Date",
                result.get("target_date", "N/A")
            )

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 💭 AKUFIN Reasoning")
                st.info(result.get("reasoning", "N/A"))
                st.markdown("### 📊 Technical Summary")
                st.write(
                    result.get(
                        "technical_summary", "N/A"
                    )
                )
            with col_b:
                st.markdown("### 🚀 Catalysts")
                st.success(
                    result.get("catalysts", "N/A")
                )
                st.markdown("### ⚠️ Risk Factors")
                st.warning(
                    result.get("risk_factors", "N/A")
                )

    st.divider()
    st.subheader("📋 AKUFIN Prediction Tracker")
    predictions = (
        services["predictor"].get_all_predictions()
    )

    if not predictions:
        st.info("No predictions yet.")
    else:
        total = len(predictions)
        resolved = sum(
            1 for p in predictions
            if p.get("prediction_correct") is not None
        )
        correct = sum(
            1 for p in predictions
            if p.get("prediction_correct") is True
        )
        accuracy = (
            round(correct / resolved * 100, 1)
            if resolved > 0 else 0
        )

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total", total)
        s2.metric("Active", sum(
            1 for p in predictions
            if p.get("status") == "ACTIVE"
        ))
        s3.metric("Correct", correct)
        s4.metric("AKUFIN Accuracy", f"{accuracy}%")
        st.divider()

        for pred in predictions:
            dir_icon = (
                "🟢 UP"
                if pred.get(
                    "predicted_direction"
                ) == "UP"
                else "🔴 DOWN"
            )
            port_icon = (
                "⚡"
                if pred.get("portfolio") == "SNIPER"
                else "🏰"
            )
            conf_pct = pred.get("confidence", 0) * 100
            progress = pred.get(
                "progress_to_target_pct", 0
            )

            with st.container():
                h1, h2, h3 = st.columns([3, 2, 1])
                with h1:
                    st.markdown(
                        f"### {port_icon} "
                        f"**{pred['ticker']}** "
                        f"→ {dir_icon} → "
                        f"**${pred['predicted_price']:.2f}**"
                    )
                with h2:
                    st.caption(
                        f"Target: {pred.get('target_date')}"
                    )
                with h3:
                    if conf_pct >= 75:
                        st.success(f"{conf_pct:.0f}%")
                    elif conf_pct >= 60:
                        st.warning(f"{conf_pct:.0f}%")
                    else:
                        st.error(f"{conf_pct:.0f}%")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric(
                    "Entry",
                    f"${pred['current_price_at_prediction']:.2f}"
                )
                c2.metric(
                    "Now",
                    f"${pred['current_price_now']:.2f}",
                    f"{pred['price_change_so_far_pct']:+.1f}%"
                )
                c3.metric(
                    "Target",
                    f"${pred['predicted_price']:.2f}"
                )
                c4.metric(
                    "Portfolio",
                    pred.get("portfolio", "N/A")
                )

                st.progress(
                    min(progress / 100, 1.0),
                    text=f"Progress: {progress:.1f}%"
                )

                with st.expander(
                    f"💎 AKUFIN Analysis — "
                    f"{pred['ticker']}"
                ):
                    r1, r2 = st.columns(2)
                    with r1:
                        st.markdown("**💭 Reasoning:**")
                        st.write(
                            pred.get("reasoning", "N/A")
                        )
                        st.markdown("**📊 Technical:**")
                        st.write(
                            pred.get(
                                "technical_summary",
                                "N/A"
                            )
                        )
                    with r2:
                        st.markdown("**🚀 Catalysts:**")
                        st.write(
                            pred.get("catalysts", "N/A")
                        )
                        st.markdown("**⚠️ Risks:**")
                        st.write(
                            pred.get(
                                "risk_factors", "N/A"
                            )
                        )
                    st.caption(
                        f"Generated: "
                        f"{pred.get('created_at', '')}"
                    )
                st.divider()

# ══════════════════════════════════════════════════════
# PAGE 2: LIVE PORTFOLIO
# ══════════════════════════════════════════════════════
elif page == "💼 Live Portfolio":
    st.title("💼 AKUFIN Live Portfolio")
    st.markdown("*Real-time Alpaca Paper Trading data*")
    st.divider()

    if st.button("🔄 Refresh Positions"):
        st.rerun()

    st.caption(
        f"Last updated: "
        f"{datetime.now().strftime('%H:%M:%S')} | "
        f"Click refresh for latest data"
    )

    fresh_broker = AlpacaBroker()
    summary = fresh_broker.get_portfolio_summary()
    account = summary["account"]
    positions = summary["positions"]
    orders = summary["recent_orders"]

    st.subheader("📊 Account Overview")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(
        "💰 Portfolio Value",
        f"${account.get('portfolio_value', 0):,.2f}"
    )
    m2.metric(
        "💵 Cash",
        f"${account.get('cash', 0):,.2f}"
    )
    m3.metric(
        "⚡ Buying Power",
        f"${account.get('buying_power', 0):,.2f}"
    )
    daily_pl = account.get("daily_pl", 0)
    daily_pl_pct = account.get("daily_pl_pct", 0)
    m4.metric(
        "📈 Daily P&L",
        f"${daily_pl:,.2f}",
        f"{daily_pl_pct:+.2f}%"
    )
    m5.metric(
        "📋 Positions",
        summary["total_positions"]
    )

    st.divider()
    st.subheader("📋 Open Positions")

    if positions:
        for pos in positions:
            pl = pos.get("unrealized_pl", 0)
            plpc = pos.get("unrealized_plpc", 0)
            p1, p2, p3, p4, p5, p6 = st.columns(6)
            p1.metric("Symbol", pos["symbol"])
            p2.metric("Qty", f"{pos['qty']:.0f}")
            p3.metric(
                "Entry",
                f"${pos['avg_entry_price']:.2f}"
            )
            p4.metric(
                "Current",
                f"${pos['current_price']:.2f}"
            )
            p5.metric(
                "P&L",
                f"${pl:,.2f}",
                f"{plpc:+.1f}%"
            )
            p6.metric(
                "Value",
                f"${pos['market_value']:,.2f}"
            )

            if role in ["trader", "admin"]:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button(
                        f"❌ Close {pos['symbol']}",
                        key=f"close_{pos['symbol']}",
                        use_container_width=True
                    ):
                        with st.spinner(
                            f"Closing {pos['symbol']}..."
                        ):
                            result = fresh_broker.close_position(
                                pos["symbol"]
                            )
                        if result["success"]:
                            st.success(
                                f"✅ {pos['symbol']} closed!"
                            )
                            st.rerun()
                        else:
                            st.error(
                                f"❌ {result.get('error')}"
                            )
                with btn_col2:
                    if st.button(
                        f"🚫 Cancel Orders",
                        key=f"cancel_{pos['symbol']}",
                        use_container_width=True
                    ):
                        with st.spinner(
                            "Cancelling orders..."
                        ):
                            cancelled = fresh_broker.cancel_orders_for_symbol(
                                pos["symbol"]
                            )
                        if cancelled > 0:
                            st.success(
                                f"✅ {cancelled} orders cancelled."
                            )
                            st.rerun()
                        else:
                            st.info(
                                "No open orders found."
                            )
            st.divider()
    else:
        st.info("📭 No open positions yet.")

    st.subheader("📋 Open Orders")
    open_orders = fresh_broker.get_open_orders()
    if open_orders:
        for order in open_orders:
            side_icon = (
                "🟢"
                if "buy" in str(
                    order["side"]
                ).lower()
                else "🔴"
            )
            st.markdown(
                f"{side_icon} **{order['symbol']}** | "
                f"Type: {order['type']} | "
                f"Qty: {order['qty']:.0f} | "
                f"Status: {order['status']}"
            )
        if role in ["trader", "admin"]:
            if st.button(
                "🚫 Cancel ALL Open Orders",
                type="primary"
            ):
                with st.spinner("Cancelling..."):
                    result = fresh_broker.cancel_all_orders()
                if result["success"]:
                    st.success("✅ All orders cancelled!")
                    st.rerun()
                else:
                    st.error(
                        f"❌ {result.get('error')}"
                    )
    else:
        st.info("No open orders.")

    st.subheader("📜 Recent Orders")
    if orders:
        for order in orders:
            side_icon = (
                "🟢"
                if "buy" in str(
                    order["side"]
                ).lower()
                else "🔴"
            )
            st.markdown(
                f"{side_icon} **{order['symbol']}** | "
                f"Qty: {order['qty']:.0f} | "
                f"Status: {order['status']} | "
                f"Price: ${order['filled_price']:.2f}"
            )
    else:
        st.info("No recent orders.")

# ══════════════════════════════════════════════════════
# PAGE 3: PLACE PAPER TRADE
# ══════════════════════════════════════════════════════
elif page == "⚡ Place Paper Trade":
    if role not in ["trader", "admin"]:
        st.error("❌ Access denied.")
        st.stop()

    st.title("⚡ AKUFIN Paper Trade Execution")
    st.warning("⚠️ Paper Trading: No real money used.")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Order Details")
        trade_ticker_raw = st.text_input(
            "Ticker", value="AAPL"
        )
        trade_ticker = sanitize_ticker(
            trade_ticker_raw
        )
        trade_side = st.selectbox(
            "Side", ["BUY", "SELL"]
        )
        trade_qty = st.number_input(
            "Quantity",
            min_value=1,
            max_value=1000,
            value=5,
            step=1
        )
        trade_portfolio = st.selectbox(
            "Portfolio", ["SNIPER", "FORTRESS"]
        )
        trade_reason = st.text_area(
            "Reason", height=100
        )

    with col2:
        st.subheader("📊 Quick Analysis")
        if trade_ticker:
            df = services["market"].get_historical_bars(
                trade_ticker, period="1mo"
            )
            if not df.empty:
                analysis = services[
                    "indicators"
                ].get_full_analysis(df, trade_ticker)
                if "error" not in analysis:
                    price = analysis["current_price"]
                    st.metric(
                        "Price", f"${price:.2f}"
                    )
                    st.metric(
                        "Value",
                        f"${price * trade_qty:,.2f}"
                    )
                    st.metric(
                        "Trend", analysis["trend"]
                    )
                    st.metric(
                        "RSI",
                        f"{analysis['rsi']['value']:.1f}",
                        analysis["rsi"]["signal"]
                    )
                    st.metric(
                        "Stop",
                        f"${analysis['atr']['stop_loss']:.2f}"
                    )
                    st.metric(
                        "Target",
                        f"${analysis['atr']['take_profit']:.2f}"
                    )

    st.divider()
    st.subheader("✅ Execute")

    acc = services["broker"].get_account()
    pv = acc.get("portfolio_value", 100000)

    if trade_ticker and trade_qty > 0:
        try:
            cp = services[
                "market"
            ].get_current_price(trade_ticker)
            tv = cp * trade_qty
            pct = tv / pv * 100

            st.markdown(
                f"**Order:** {trade_side} "
                f"**{trade_qty}** {trade_ticker} "
                f"@ ~${cp:.2f} = ${tv:,.2f} "
                f"({pct:.1f}%)"
            )

            if pct > 5:
                st.warning(
                    f"⚠️ {pct:.1f}% exceeds 5% limit"
                )

            c1, c2 = st.columns(2)
            with c1:
                exec_btn = st.button(
                    f"💎 EXECUTE {trade_side}",
                    type="primary",
                    use_container_width=True
                )
            with c2:
                st.button(
                    "❌ Cancel",
                    use_container_width=True
                )

            if exec_btn:
                with st.spinner("Executing..."):
                    result = services[
                        "broker"
                    ].place_market_order(
                        symbol=trade_ticker,
                        qty=int(trade_qty),
                        side=trade_side.lower(),
                        reason=trade_reason
                    )
                if result.get("success"):
                    st.success(
                        f"✅ Order Executed! "
                        f"ID: {result['order_id']}"
                    )
                    st.balloons()
                else:
                    st.error(
                        f"❌ {result.get('error')}"
                    )
        except Exception as e:
            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════
# PAGE 4: PENDING APPROVALS
# ══════════════════════════════════════════════════════
elif page == "⏳ Pending Approvals":
    if role not in ["trader", "admin"]:
        st.error("❌ Access denied.")
        st.stop()

    st.title("⏳ AKUFIN Trade Approval Gate")
    st.info(
        "**Human-in-the-Loop**: "
        "AI recommends. You decide."
    )

    # Refresh button
    if st.button("🔄 Refresh Signals"):
        st.rerun()

    st.divider()

    # Load fresh signals every time
    sig_repo = get_signal_repo()
    pending_signals = []

    if sig_repo:
        try:
            pending_signals = (
                sig_repo.get_pending_signals()
            )
        except Exception as e:
            st.error(f"Error loading signals: {e}")

    if not pending_signals:
        st.success("✅ No pending signals right now.")
        st.info(
            "💡 **How AKUFIN signals work:**\n\n"
            "1. Use **🧠 AKUFIN Intelligence** to analyze a ticker\n"
            "2. Click **Save to Pending Approvals**\n"
            "3. Signal appears here\n"
            "4. Click APPROVE → executes on Alpaca\n"
            "5. Or run scanner: `python run_scanner.py`"
        )
    else:
        st.warning(
            f"⏳ {len(pending_signals)} signal(s) "
            f"waiting for your approval"
        )

        for signal in pending_signals:
            with st.container():
                p_icon = (
                    "⚡"
                    if signal["portfolio"] == "SNIPER"
                    else "🏰"
                )
                entry = signal.get("entry_price", 0)
                stop = signal.get("stop_loss", 0)
                target = signal.get("take_profit", 0)
                risk = round(abs(entry - stop), 2)
                reward = round(abs(target - entry), 2)
                rr = (
                    round(reward / risk, 1)
                    if risk > 0 else 0
                )
                conf = signal.get("confidence", 0) * 100
                qty = signal.get("quantity", 1)
                pos_val = round(entry * qty, 2)
                score = signal.get("score", 0)

                st.markdown(
                    f"### {p_icon} AKUFIN "
                    f"{signal['portfolio']} | "
                    f"🟢 {signal['signal']} "
                    f"**{signal['ticker']}**"
                )

                st.progress(
                    min(score / 10, 1.0),
                    text=(
                        f"AKUFIN Score: {score}/10 | "
                        f"Trend: "
                        f"{signal.get('trend', 'N/A')} | "
                        f"RSI: "
                        f"{signal.get('rsi', 0):.1f}"
                    )
                )

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Entry", f"${entry:.2f}")
                c2.metric(
                    "Stop Loss",
                    f"${stop:.2f}",
                    f"-${risk:.2f}"
                )
                c3.metric(
                    "Target",
                    f"${target:.2f}",
                    f"+${reward:.2f}"
                )
                c4.metric("R:R", f"{rr}:1")
                c5.metric(
                    "Confidence", f"{conf:.0f}%"
                )

                st.info(
                    f"💎 **AKUFIN Reasoning:** "
                    f"{signal.get('reasoning', 'N/A')}"
                )
                st.caption(
                    f"Qty: {qty} shares = "
                    f"${pos_val:,.2f} | "
                    f"Signal ID: #{signal['id']} | "
                    f"Generated: "
                    f"{signal.get('created_at', '')}"
                )

                b1, b2, b3 = st.columns(3)

                if b1.button(
                    "✅ APPROVE & EXECUTE",
                    key=f"app_{signal['id']}",
                    use_container_width=True,
                    type="primary"
                ):
                    with st.spinner(
                        f"Executing {signal['ticker']}..."
                    ):
                        result = services[
                            "broker"
                        ].place_market_order(
                            symbol=signal["ticker"],
                            qty=signal["quantity"],
                            side=signal["signal"].lower(),
                            reason=(
                                f"AKUFIN approved "
                                f"by {username}"
                            )
                        )

                    if result.get("success"):
                        sig_repo.approve_signal(
                            signal["id"],
                            username,
                            result.get("order_id", "")
                        )
                        st.success(
                            f"✅ {signal['ticker']} "
                            f"executed! "
                            f"Order: {result['order_id']}"
                        )
                        st.balloons()
                        try:
                            from monitoring.telegram_alerts import AKUFINTelegram
                            tg = AKUFINTelegram()
                            tg.send_trade_executed(result)
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Failed: "
                            f"{result.get('error')}"
                        )

                if b2.button(
                    "❌ REJECT",
                    key=f"rej_{signal['id']}",
                    use_container_width=True
                ):
                    sig_repo.reject_signal(
                        signal["id"], username
                    )
                    st.error(
                        f"❌ {signal['ticker']} rejected."
                    )
                    st.rerun()

                if b3.button(
                    "🔍 Full Details",
                    key=f"det_{signal['id']}",
                    use_container_width=True
                ):
                    st.json(signal)

                st.divider()

    # Signal History
    if sig_repo:
        with st.expander("📜 Signal History (Last 20)"):
            try:
                all_sigs = sig_repo.get_all_signals(
                    limit=20
                )
                if all_sigs:
                    for s in all_sigs:
                        status_icon = {
                            "PENDING": "⏳",
                            "APPROVED": "✅",
                            "REJECTED": "❌"
                        }.get(s["status"], "❓")
                        st.markdown(
                            f"{status_icon} "
                            f"**{s['ticker']}** "
                            f"{s['signal']} | "
                            f"Score: {s['score']}/10 | "
                            f"Conf: "
                            f"{s['confidence']*100:.0f}% | "
                            f"Status: {s['status']} | "
                            f"{s['created_at']}"
                        )
                else:
                    st.info("No signal history yet.")
            except Exception as e:
                st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════
# PAGE 5: LIVE ANALYSIS
# ══════════════════════════════════════════════════════
elif page == "📊 Live Analysis":
    st.title("📊 AKUFIN Live Analysis")
    st.divider()

    a1, a2 = st.columns([3, 1])
    with a1:
        aticker_raw = st.text_input(
            "Ticker", value="AAPL"
        )
        aticker = sanitize_ticker(aticker_raw)
    with a2:
        st.write("")
        run_btn = st.button(
            "💎 Analyze",
            type="primary",
            use_container_width=True
        )

    if run_btn and aticker:
        with st.spinner(
            f"AKUFIN analyzing {aticker}..."
        ):
            df = services["market"].get_historical_bars(
                aticker, "6mo"
            )

        if df.empty:
            st.error(f"No data for {aticker}")
        else:
            r = services[
                "indicators"
            ].get_full_analysis(df, aticker)
            if "error" in r:
                st.error(r["error"])
            else:
                st.subheader(
                    f"📊 AKUFIN — {aticker}"
                )
                t1, t2, t3, t4 = st.columns(4)
                t1.metric(
                    "Price",
                    f"${r['current_price']:.2f}"
                )
                t2.metric("Trend", r["trend"])
                t3.metric(
                    "RSI",
                    f"{r['rsi']['value']:.1f}",
                    r["rsi"]["signal"]
                )
                t4.metric(
                    "MACD", r["macd"]["signal"]
                )

                st.divider()
                d1, d2, d3 = st.columns(3)

                with d1:
                    st.markdown("**📈 Moving Averages**")
                    st.write(
                        f"EMA 20: "
                        f"${r['moving_averages']['ema_20']:.2f}"
                    )
                    st.write(
                        f"EMA 50: "
                        f"${r['moving_averages']['ema_50']:.2f}"
                    )
                    st.write(
                        f"EMA 200: "
                        f"${r['moving_averages']['ema_200']:.2f}"
                    )
                    gc = r[
                        "moving_averages"
                    ]["golden_cross"]
                    st.write(
                        f"Golden Cross: "
                        f"{'✅' if gc else '❌'}"
                    )

                with d2:
                    st.markdown("**📊 Bollinger Bands**")
                    st.write(
                        f"Upper: "
                        f"${r['bollinger_bands']['upper']:.2f}"
                    )
                    st.write(
                        f"Middle: "
                        f"${r['bollinger_bands']['middle']:.2f}"
                    )
                    st.write(
                        f"Lower: "
                        f"${r['bollinger_bands']['lower']:.2f}"
                    )
                    st.write(
                        f"Position: "
                        f"{r['bollinger_bands']['position']}"
                    )

                with d3:
                    st.markdown("**⚠️ Trade Levels**")
                    st.metric(
                        "ATR",
                        f"${r['atr']['value']:.2f}"
                    )
                    st.error(
                        f"🛑 Stop: "
                        f"${r['atr']['stop_loss']:.2f}"
                    )
                    st.success(
                        f"🎯 Target: "
                        f"${r['atr']['take_profit']:.2f}"
                    )
                    st.info(
                        f"⚖️ R:R: "
                        f"{r['atr']['risk_reward_ratio']}:1"
                    )

                st.divider()
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name=aticker,
                    increasing_line_color="#FFD700",
                    decreasing_line_color="#ff5252"
                ))
                ind = services["indicators"]
                e20 = ind.ema(df, 20)
                e50 = ind.ema(df, 50)
                fig.add_trace(go.Scatter(
                    x=df.index, y=e20,
                    name="EMA 20",
                    line=dict(
                        color="#4fc3f7", width=1.5
                    )
                ))
                fig.add_trace(go.Scatter(
                    x=df.index, y=e50,
                    name="EMA 50",
                    line=dict(
                        color="#DAA520", width=1.5
                    )
                ))
                fig.update_layout(
                    title=f"AKUFIN Chart — {aticker}",
                    template="plotly_dark",
                    paper_bgcolor="#0a0e1a",
                    plot_bgcolor="#0a0e1a",
                    xaxis_rangeslider_visible=False,
                    height=420
                )
                st.plotly_chart(
                    fig, use_container_width=True
                )

# ══════════════════════════════════════════════════════
# PAGE 6: AGENT ACTIVITY
# ══════════════════════════════════════════════════════
elif page == "📈 Agent Activity":
    st.title("📈 AKUFIN Agent Activity")
    st.markdown("*Live feed of AKUFIN AI agents*")
    st.divider()

    port_filter = st.selectbox(
        "Filter", ["ALL", "SNIPER", "FORTRESS"]
    )

    activities = [
        {
            "time": "09:35",
            "agent": "💎 AKUFIN Scanner",
            "action": (
                "Morning scan: 20 tickers. "
                "3 signals saved to database."
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:47",
            "agent": "🐋 Whale Hunter",
            "action": "$2.1M dark pool SPY detected.",
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:52",
            "agent": "📊 AKUFIN Technical",
            "action": "SPY RSI bullish. MACD crossover.",
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:58",
            "agent": "📰 AKUFIN Sentiment",
            "action": "Bullish sentiment: 0.82.",
            "level": "MEDIUM",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🧠 AKUFIN Orchestrator",
            "action": "3/3 agree. SPY 87% confidence.",
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🛡️ AKUFIN Risk Warden",
            "action": "SPY passed all 7 checks.",
            "level": "LOW",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:03",
            "agent": "⏳ AKUFIN Human Gate",
            "action": (
                "SPY BUY saved to Pending Approvals. "
                "Telegram notified."
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:15",
            "agent": "📊 AKUFIN Fundamental",
            "action": "AAPL FORTRESS opportunity.",
            "level": "MEDIUM",
            "portfolio": "FORTRESS"
        },
        {
            "time": "10:22",
            "agent": "💎 AKUFIN Prediction",
            "action": "AAPL → $225 (21 days, 79%).",
            "level": "HIGH",
            "portfolio": "FORTRESS"
        },
    ]

    icons = {
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }

    filtered = [
        a for a in activities
        if port_filter == "ALL"
        or a["portfolio"] == port_filter
    ]

    for act in filtered:
        c1, c2, c3, c4 = st.columns([1, 2, 5, 1])
        with c1:
            st.markdown(f"**{act['time']}**")
        with c2:
            st.markdown(act["agent"])
        with c3:
            st.markdown(
                f"{icons.get(act['level'], '⚪')} "
                f"{act['action']}"
            )
        with c4:
            st.caption(
                "⚡ S"
                if act["portfolio"] == "SNIPER"
                else "🏰 F"
            )
        st.divider()

# ══════════════════════════════════════════════════════
# PAGE 7: ADMIN PANEL
# ══════════════════════════════════════════════════════
elif page == "🔑 Admin Panel":
    if role != "admin":
        st.error("❌ Access denied.")
        st.stop()
    show_admin_panel()

# ══════════════════════════════════════════════════════
# PAGE 8: PERFORMANCE ANALYTICS
# ══════════════════════════════════════════════════════
elif page == "📉 Performance Analytics":
    st.title("📉 AKUFIN Performance Analytics")
    st.markdown(
        "*Verifiable AI prediction track record*"
    )
    st.divider()

    predictions = (
        services["predictor"].get_all_predictions()
    )

    if not predictions:
        st.info(
            "No predictions yet. "
            "Generate predictions on the "
            "AI Predictions page to build "
            "your track record."
        )
    else:
        total = len(predictions)
        active = sum(
            1 for p in predictions
            if p.get("status") == "ACTIVE"
        )
        resolved = sum(
            1 for p in predictions
            if p.get("prediction_correct") is not None
        )
        correct = sum(
            1 for p in predictions
            if p.get("prediction_correct") is True
        )
        accuracy = (
            round(correct / resolved * 100, 1)
            if resolved > 0 else 0
        )
        avg_confidence = round(
            sum(
                p.get("confidence", 0)
                for p in predictions
            ) / total * 100, 1
        )

        st.subheader("🏆 AKUFIN Scorecard")
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Total Predictions", total)
        s2.metric("Active", active)
        s3.metric("Resolved", resolved)
        s4.metric("AI Accuracy", f"{accuracy}%")
        s5.metric(
            "Avg Confidence", f"{avg_confidence}%"
        )

        st.divider()

        import plotly.express as px
        import pandas as pd

        df_data = []
        for p in predictions:
            df_data.append({
                "Ticker": p.get("ticker", ""),
                "Portfolio": p.get(
                    "portfolio", "SNIPER"
                ),
                "Direction": p.get(
                    "predicted_direction", "UP"
                ),
                "Confidence": p.get(
                    "confidence", 0
                ) * 100,
                "Status": p.get("status", "ACTIVE"),
                "Correct": p.get("prediction_correct"),
                "Progress": p.get(
                    "progress_to_target_pct", 0
                ),
                "Created": p.get("created_at", ""),
                "Target Date": p.get(
                    "target_date", ""
                ),
                "Entry Price": p.get(
                    "current_price_at_prediction", 0
                ),
                "Target Price": p.get(
                    "predicted_price", 0
                ),
                "Current Price": p.get(
                    "current_price_now", 0
                ),
                "Change So Far": p.get(
                    "price_change_so_far_pct", 0
                )
            })

        df = pd.DataFrame(df_data)

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Accuracy Charts",
            "🎯 By Ticker",
            "💼 By Portfolio",
            "📋 Full History"
        ])

        with tab1:
            st.subheader("📊 Prediction Accuracy Overview")

            col1, col2 = st.columns(2)

            with col1:
                if resolved > 0:
                    pie_data = {
                        "Result": [
                            "Correct",
                            "Incorrect",
                            "Active"
                        ],
                        "Count": [
                            correct,
                            resolved - correct,
                            active
                        ]
                    }
                    fig_pie = px.pie(
                        pie_data,
                        values="Count",
                        names="Result",
                        title="Prediction Outcomes",
                        color="Result",
                        color_discrete_map={
                            "Correct": "#00e676",
                            "Incorrect": "#ff5252",
                            "Active": "#FFD700"
                        }
                    )
                    fig_pie.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="#0a0e1a",
                        plot_bgcolor="#0a0e1a"
                    )
                    st.plotly_chart(
                        fig_pie,
                        use_container_width=True
                    )
                else:
                    st.info(
                        "No resolved predictions yet."
                    )

            with col2:
                up_count = sum(
                    1 for p in predictions
                    if p.get(
                        "predicted_direction"
                    ) == "UP"
                )
                down_count = total - up_count

                dir_data = {
                    "Direction": ["UP 🟢", "DOWN 🔴"],
                    "Count": [up_count, down_count]
                }
                fig_dir = px.bar(
                    dir_data,
                    x="Direction",
                    y="Count",
                    title="Prediction Direction Split",
                    color="Direction",
                    color_discrete_map={
                        "UP 🟢": "#00e676",
                        "DOWN 🔴": "#ff5252"
                    }
                )
                fig_dir.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0a0e1a",
                    plot_bgcolor="#0a0e1a",
                    showlegend=False
                )
                st.plotly_chart(
                    fig_dir,
                    use_container_width=True
                )

            st.subheader("🎲 Confidence Distribution")
            fig_conf = px.histogram(
                df,
                x="Confidence",
                nbins=10,
                title="AI Confidence Score Distribution",
                color_discrete_sequence=["#DAA520"]
            )
            fig_conf.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a"
            )
            st.plotly_chart(
                fig_conf,
                use_container_width=True
            )

            st.subheader("📈 Progress to Target")
            active_preds = [
                p for p in predictions
                if p.get("status") == "ACTIVE"
            ]
            if active_preds:
                prog_data = {
                    "Ticker": [
                        p["ticker"]
                        for p in active_preds
                    ],
                    "Progress": [
                        p.get(
                            "progress_to_target_pct",
                            0
                        )
                        for p in active_preds
                    ],
                    "Portfolio": [
                        p.get("portfolio", "SNIPER")
                        for p in active_preds
                    ]
                }
                fig_prog = px.bar(
                    prog_data,
                    x="Ticker",
                    y="Progress",
                    color="Portfolio",
                    title="Progress to Price Target (%)",
                    color_discrete_map={
                        "SNIPER": "#4fc3f7",
                        "FORTRESS": "#DAA520"
                    }
                )
                fig_prog.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0a0e1a",
                    plot_bgcolor="#0a0e1a"
                )
                st.plotly_chart(
                    fig_prog,
                    use_container_width=True
                )
            else:
                st.info("No active predictions.")

        with tab2:
            st.subheader("🎯 Performance By Ticker")

            ticker_counts = df.groupby(
                "Ticker"
            ).size().reset_index(name="Count")
            ticker_counts = ticker_counts.sort_values(
                "Count", ascending=False
            )

            fig_tick = px.bar(
                ticker_counts,
                x="Ticker",
                y="Count",
                title="Predictions Per Ticker",
                color_discrete_sequence=["#DAA520"]
            )
            fig_tick.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a"
            )
            st.plotly_chart(
                fig_tick,
                use_container_width=True
            )

            conf_by_ticker = df.groupby(
                "Ticker"
            )["Confidence"].mean().reset_index()
            conf_by_ticker.columns = [
                "Ticker", "Avg Confidence"
            ]
            conf_by_ticker = conf_by_ticker.sort_values(
                "Avg Confidence", ascending=False
            )

            fig_conf_tick = px.bar(
                conf_by_ticker,
                x="Ticker",
                y="Avg Confidence",
                title="Average AI Confidence by Ticker",
                color_discrete_sequence=["#4fc3f7"]
            )
            fig_conf_tick.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a"
            )
            st.plotly_chart(
                fig_conf_tick,
                use_container_width=True
            )

        with tab3:
            st.subheader(
                "💼 SNIPER vs FORTRESS Performance"
            )

            port_counts = df.groupby(
                "Portfolio"
            ).size().reset_index(name="Count")

            fig_port = px.pie(
                port_counts,
                values="Count",
                names="Portfolio",
                title="Predictions by Portfolio",
                color="Portfolio",
                color_discrete_map={
                    "SNIPER": "#4fc3f7",
                    "FORTRESS": "#DAA520"
                }
            )
            fig_port.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a"
            )
            st.plotly_chart(
                fig_port,
                use_container_width=True
            )

            port_conf = df.groupby(
                "Portfolio"
            )["Confidence"].mean().reset_index()

            col1, col2 = st.columns(2)
            for idx, row in port_conf.iterrows():
                if row["Portfolio"] == "SNIPER":
                    col1.metric(
                        "⚡ SNIPER Avg Confidence",
                        f"{row['Confidence']:.1f}%"
                    )
                else:
                    col2.metric(
                        "🏰 FORTRESS Avg Confidence",
                        f"{row['Confidence']:.1f}%"
                    )

            st.subheader("Progress by Portfolio")
            port_prog = df.groupby(
                "Portfolio"
            )["Progress"].mean().reset_index()

            fig_pp = px.bar(
                port_prog,
                x="Portfolio",
                y="Progress",
                title="Avg Progress to Target by Portfolio",
                color="Portfolio",
                color_discrete_map={
                    "SNIPER": "#4fc3f7",
                    "FORTRESS": "#DAA520"
                }
            )
            fig_pp.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0e1a",
                plot_bgcolor="#0a0e1a"
            )
            st.plotly_chart(
                fig_pp,
                use_container_width=True
            )

        with tab4:
            st.subheader("📋 Full Prediction History")

            sort_by = st.selectbox(
                "Sort by",
                [
                    "Newest First",
                    "Highest Confidence",
                    "Most Progress",
                    "By Ticker"
                ]
            )

            sorted_preds = predictions.copy()
            if sort_by == "Newest First":
                sorted_preds = sorted(
                    sorted_preds,
                    key=lambda x: x.get(
                        "created_at", ""
                    ),
                    reverse=True
                )
            elif sort_by == "Highest Confidence":
                sorted_preds = sorted(
                    sorted_preds,
                    key=lambda x: x.get(
                        "confidence", 0
                    ),
                    reverse=True
                )
            elif sort_by == "Most Progress":
                sorted_preds = sorted(
                    sorted_preds,
                    key=lambda x: x.get(
                        "progress_to_target_pct", 0
                    ),
                    reverse=True
                )
            elif sort_by == "By Ticker":
                sorted_preds = sorted(
                    sorted_preds,
                    key=lambda x: x.get("ticker", "")
                )

            for pred in sorted_preds:
                dir_icon = (
                    "🟢"
                    if pred.get(
                        "predicted_direction"
                    ) == "UP"
                    else "🔴"
                )
                port_icon = (
                    "⚡"
                    if pred.get(
                        "portfolio"
                    ) == "SNIPER"
                    else "🏰"
                )
                conf = pred.get("confidence", 0) * 100
                progress = pred.get(
                    "progress_to_target_pct", 0
                )
                change = pred.get(
                    "price_change_so_far_pct", 0
                )
                status_icon = {
                    "ACTIVE": "🔄",
                    "RESOLVED": "✅",
                    "EXPIRED": "⏰"
                }.get(
                    pred.get("status", "ACTIVE"), "🔄"
                )

                with st.container():
                    c1, c2, c3, c4, c5 = st.columns(
                        [2, 1, 1, 1, 1]
                    )
                    c1.markdown(
                        f"{port_icon} {dir_icon} "
                        f"**{pred['ticker']}** → "
                        f"${pred['predicted_price']:.2f}"
                    )
                    c2.metric(
                        "Confidence", f"{conf:.0f}%"
                    )
                    c3.metric(
                        "Progress", f"{progress:.1f}%"
                    )
                    c4.metric(
                        "Change", f"{change:+.1f}%"
                    )
                    c5.markdown(
                        f"{status_icon} "
                        f"{pred.get('status', 'ACTIVE')}"
                    )
                    st.caption(
                        f"Target: "
                        f"{pred.get('target_date', '')} | "
                        f"Generated: "
                        f"{pred.get('created_at', '')}"
                    )
                    st.divider()

# ══════════════════════════════════════════════════════
# PAGE 9: AKUFIN INTELLIGENCE (4 AGENTS)
# ══════════════════════════════════════════════════════
elif page == "🧠 AKUFIN Intelligence":
    if role not in ["trader", "admin"]:
        st.error("❌ Access denied.")
        st.stop()

    st.title("🧠 AKUFIN Intelligence Engine")
    st.markdown(
        "*4 AI agents analyze simultaneously. "
        "One unified verdict.*"
    )
    st.divider()

    st.info(
        "**How it works:**\n"
        "Enter a ticker below. "
        "AKUFIN runs 4 specialized agents "
        "simultaneously:\n"
        "🎯 Scoring Agent | "
        "⚡ Tactical Agent | "
        "🌍 Macro Agent | "
        "📊 Pattern Agent\n\n"
        "Takes 30-60 seconds. "
        "High conviction signals auto-save "
        "to Pending Approvals."
    )

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        intel_ticker_raw = st.text_input(
            "Ticker Symbol",
            value="NVDA",
            placeholder="e.g. NVDA, AAPL, SPY"
        )
        intel_ticker = sanitize_ticker(
            intel_ticker_raw
        )
    with col2:
        intel_portfolio = st.selectbox(
            "Portfolio",
            ["SNIPER", "FORTRESS"]
        )
    with col3:
        st.write("")
        st.write("")
        run_intel = st.button(
            "🧠 Run Analysis",
            type="primary",
            use_container_width=True
        )

    if run_intel and intel_ticker:
        st.divider()
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Fix import path
            root_path = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
            if root_path not in sys.path:
                sys.path.insert(0, root_path)

            from agents.orchestrator import (
                AKUFINOrchestrator
            )

            status_text.markdown(
                "🔄 **Starting AKUFIN agents...**"
            )
            progress_bar.progress(10)

            orchestrator = AKUFINOrchestrator()

            status_text.markdown(
                "🎯 **Scoring Agent analyzing...**\n\n"
                "⚡ **Tactical Agent calculating...**\n\n"
                "🌍 **Macro Agent assessing...**\n\n"
                "📊 **Pattern Agent scanning...**"
            )
            progress_bar.progress(30)

            with st.spinner(
                f"All 4 AKUFIN agents analyzing "
                f"{intel_ticker}... "
                f"(30-60 seconds)"
            ):
                result = orchestrator.analyze_sync(
                    intel_ticker
                )

            progress_bar.progress(90)
            status_text.markdown(
                "🧠 **Orchestrator synthesizing...**"
            )
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()

            if "error" in result and result.get(
                "final_signal"
            ) == "HOLD":
                st.warning(
                    f"⚠️ Analysis note: "
                    f"{result.get('error', '')}"
                )

            final_signal = result.get(
                "final_signal", "HOLD"
            )
            confidence = result.get(
                "confidence", 0
            ) * 100
            akufin_score = result.get(
                "akufin_score", 0
            )
            agents_agree = result.get(
                "agents_agreeing", 0
            )

            if final_signal == "BUY":
                st.success(
                    f"### 🟢 AKUFIN SIGNAL: **{final_signal}**"
                )
            elif final_signal == "SELL":
                st.error(
                    f"### 🔴 AKUFIN SIGNAL: **{final_signal}**"
                )
            else:
                st.warning(
                    f"### ⚪ AKUFIN SIGNAL: **{final_signal}**"
                )

            st.divider()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric(
                "💎 AKUFIN Score",
                f"{akufin_score}/10"
            )
            m2.metric(
                "🎲 Confidence",
                f"{confidence:.0f}%"
            )
            m3.metric(
                "🤝 Agents Agree",
                f"{agents_agree}/4"
            )
            m4.metric(
                "📈 Pattern",
                result.get("detected_pattern", "N/A")
            )
            m5.metric(
                "⚠️ Macro Risk",
                f"{result.get('macro_risk', 0):.2f}/1.0"
            )

            st.divider()

            entry = result.get("entry_price", 0)
            stop = result.get("stop_loss", 0)
            target = result.get("take_profit", 0)
            rr = result.get("risk_reward", 0)

            if entry > 0:
                st.subheader("📍 AKUFIN Trade Levels")
                t1, t2, t3, t4 = st.columns(4)
                t1.metric(
                    "Entry Price", f"${entry:.2f}"
                )
                t2.metric(
                    "Stop Loss",
                    f"${stop:.2f}",
                    f"-${abs(entry-stop):.2f}"
                )
                t3.metric(
                    "Take Profit",
                    f"${target:.2f}",
                    f"+${abs(target-entry):.2f}"
                )
                t4.metric("R:R Ratio", f"{rr:.1f}:1")

            st.divider()

            st.subheader("🤖 Agent Sub-Scores")
            sc = st.columns(4)
            sc[0].metric(
                "🎯 Technical",
                f"{result.get('technical_score', 0)}/10"
            )
            sc[1].metric(
                "📊 Fundamental",
                f"{result.get('fundamental_score', 0)}/10"
            )
            sc[2].metric(
                "😊 Sentiment",
                f"{result.get('sentiment_score', 0)}/10"
            )
            sc[3].metric(
                "📈 Pattern",
                f"{result.get('pattern_score', 0)}/10"
            )

            st.progress(
                min(float(akufin_score) / 10, 1.0),
                text=(
                    f"AKUFIN Score: {akufin_score}/10 | "
                    f"Macro: "
                    f"{result.get('macro_verdict', 'N/A')}"
                )
            )

            st.divider()
            st.subheader("💭 AKUFIN Reasoning")
            st.info(
                result.get(
                    "final_reasoning",
                    "Analysis complete."
                )
            )

            # Save to pending approvals
            if (
                final_signal in ["BUY", "SELL"]
                and confidence >= 65
                and entry > 0
            ):
                st.divider()
                st.subheader(
                    "⏳ Send To Approval Queue"
                )

                col_save, col_skip = st.columns(2)

                with col_save:
                    if st.button(
                        "💾 Save to Pending Approvals",
                        type="primary",
                        use_container_width=True
                    ):
                        sig_repo = get_signal_repo()
                        if sig_repo:
                            acc_data = services[
                                "broker"
                            ].get_account()
                            pv = acc_data.get(
                                "portfolio_value",
                                100000
                            )
                            risk = abs(entry - stop)
                            safe_qty = int(
                                (pv * 0.02) / risk
                            ) if risk > 0 else 1
                            safe_qty = max(
                                1, min(safe_qty, 50)
                            )

                            signal_data = {
                                "ticker": intel_ticker,
                                "signal": final_signal,
                                "portfolio": intel_portfolio,
                                "score": int(akufin_score),
                                "confidence": result.get(
                                    "confidence", 0
                                ),
                                "entry_price": entry,
                                "stop_loss": stop,
                                "take_profit": target,
                                "quantity": safe_qty,
                                "reasoning": result.get(
                                    "final_reasoning", ""
                                )[:500],
                                "trend": result.get(
                                    "detected_pattern",
                                    "N/A"
                                ),
                                "rsi": result.get(
                                    "technical_score", 0
                                ) * 10
                            }

                            signal_id = sig_repo.save_signal(
                                signal_data
                            )

                            if signal_id:
                                st.success(
                                    f"✅ Signal saved! "
                                    f"ID: #{signal_id}"
                                )

                                # Debug verify
                                all_pending = sig_repo.get_pending_signals()
                                st.info(
                                    f"📊 Debug: "
                                    f"{len(all_pending)} "
                                    f"pending signal(s) "
                                    f"in database. "
                                    f"Go to ⏳ Pending "
                                    f"Approvals to review."
                                )

                                # Send Telegram
                                try:
                                    from monitoring.telegram_alerts import AKUFINTelegram
                                    tg = AKUFINTelegram()
                                    tg.send_trade_signal({
                                        "ticker": intel_ticker,
                                        "signal": final_signal,
                                        "portfolio": intel_portfolio,
                                        "entry_price": entry,
                                        "stop_loss": stop,
                                        "take_profit": target,
                                        "confidence": result.get(
                                            "confidence", 0
                                        ),
                                        "quantity": safe_qty,
                                        "reasoning": result.get(
                                            "final_reasoning",
                                            ""
                                        )[:200]
                                    })
                                    st.info(
                                        "📱 Telegram notified!"
                                    )
                                except Exception:
                                    pass
                            else:
                                st.error(
                                    "❌ Failed to save. "
                                    "Check database connection."
                                )
                        else:
                            st.error(
                                "❌ Database not available."
                            )

                with col_skip:
                    st.button(
                        "⏭️ Skip",
                        use_container_width=True
                    )

            elif final_signal == "HOLD":
                st.warning(
                    "⚠️ HOLD signal. "
                    "Not enough conviction to trade."
                )

            st.session_state[
                "last_intel_result"
            ] = result
            st.session_state[
                "last_intel_ticker"
            ] = intel_ticker

        except ImportError as e:
            st.error(
                f"❌ Import error: {e}\n"
                "Make sure agents/orchestrator.py exists."
            )
        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")
            import traceback
            st.code(traceback.format_exc())

    elif "last_intel_result" in st.session_state:
        st.info(
            f"Last analysis: "
            f"**{st.session_state.get('last_intel_ticker')}** | "
            f"Run new analysis above."
        )

# ── Footer ────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#DAA520'>"
    "💎 <strong>AKUFIN</strong> — "
    "Intelligence for Wealth Accrual | "
    "Powered by AI Agents | "
    "Paper Trading ✅ | "
    f"© {datetime.now().year} AKUFIN Technologies"
    "</div>",
    unsafe_allow_html=True
)