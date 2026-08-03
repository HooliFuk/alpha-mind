# dashboard/app.py
# AKUFIN - Intelligence for Wealth Accrual
# Main Dashboard with Admin Access Control
import sys
import os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

# ── AKUFIN Brand Colors ───────────────────────────────
# Gold: #FFD700, Dark Gold: #DAA520, Navy: #0a0e1a
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
    h1, h2, h3 {
        color: #FFD700;
    }
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


# ══════════════════════════════════════════════════════
# AKUFIN LOGIN / ACCESS GATE
# Nobody gets past this without your approval
# ══════════════════════════════════════════════════════
def show_login_page():
    """
    AKUFIN Access Gate.
    No one sees the dashboard without credentials.
    """
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
                st.error("Please enter username and password.")
                return

            # Check admin login
            # Check admin login
if username == "admin" and access.is_admin(password):
    st.session_state["logged_in"] = True
    st.session_state["username"] = "admin"
    st.session_state["role"] = "admin"
    st.success("✅ Welcome, AKUFIN Administrator!")
    st.rerun()
    return

# Also check if admin exists as regular user
result = access.check_access(username, password)
if result["allowed"] and result.get("role") == "admin":
    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    st.session_state["role"] = "admin"
    st.success(f"✅ Welcome, AKUFIN Administrator!")
    st.rerun()
    return
                st.session_state["logged_in"] = True
                st.session_state["username"] = "admin"
                st.session_state["role"] = "admin"
                st.success("✅ Welcome, AKUFIN Administrator!")
                st.rerun()
                return

            # Check regular user
            result = access.check_access(username, password)
            if result["allowed"]:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = result["role"]
                st.success(
                    f"✅ Welcome to AKUFIN, {username}!"
                )
                st.rerun()
            else:
                st.error(f"❌ {result['reason']}")
                st.caption(
                    "Need access? Contact the "
                    "AKUFIN administrator."
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


def show_admin_panel():
    """AKUFIN Admin Control Panel"""
    st.title("🔑 AKUFIN Admin Control Panel")
    st.markdown(
        "*Full administrator control over platform access*"
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
                        if user["active"] and not user["expired"]
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
        st.subheader("Approve New User")
        new_username = st.text_input(
            "Username",
            placeholder="e.g. vc_partner_name"
        )
        new_role = st.selectbox(
            "Access Role",
            [
                "viewer",
                "analyst",
                "trader"
            ],
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
                        f"✅ {new_username} approved! "
                        f"Role: {new_role} | "
                        f"Expires: {result['expires'][:10]}"
                    )
                    st.info(
                        "Now set their password "
                        "in the 'Set Password' tab."
                    )
                else:
                    st.error(result.get("error"))

    with tab3:
        st.subheader("Revoke User Access")
        st.warning(
            "⚠️ This immediately removes access. "
            "User will be logged out instantly."
        )
        revoke_username = st.text_input(
            "Username to Revoke",
            placeholder="Enter exact username"
        )
        if st.button(
            "❌ REVOKE ACCESS",
            type="primary"
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
                        f"✅ Access revoked: "
                        f"{revoke_username}"
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
            placeholder="Set their password"
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
# MAIN APP LOGIC
# ══════════════════════════════════════════════════════

# Check if logged in
if not st.session_state.get("logged_in"):
    show_login_page()
    st.stop()

# User is logged in. Load services.
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

    # Navigation based on role
    nav_options = ["🏠 Dashboard Home"]

    if role in ["viewer", "analyst", "trader", "admin"]:
        nav_options.append("🎯 AI Predictions")
        nav_options.append("💼 Live Portfolio")
        nav_options.append("📊 Live Analysis")
        nav_options.append("📈 Agent Activity")

    if role in ["trader", "admin"]:
        nav_options.append("⚡ Place Paper Trade")
        nav_options.append("⏳ Pending Approvals")

    if role == "admin":
        nav_options.append("🔑 Admin Panel")

    page = st.selectbox("Navigation", nav_options)

    st.divider()

    # Market status
    status = services["market"].get_market_status()
    if status["is_open"]:
        st.success("🟢 Market Open")
    else:
        st.error("🔴 Market Closed")
    st.caption(f"Session: {status['session']}")
    st.divider()

    # Portfolio value
    try:
        acc = services["broker"].get_account()
        st.metric(
            "AKUFIN Portfolio",
            f"${acc['portfolio_value']:,.0f}",
            f"${acc['daily_pl']:+,.2f} today"
        )
    except:
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
            AKUFIN (Igbo: Wealth Intelligence) ·
            Predictive · Autonomous · Precise
            </em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    summary = services["broker"].get_portfolio_summary()
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
                if pred.get("predicted_direction") == "UP"
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
        "*AI-generated price predictions tracked "
        "against real market outcomes*"
    )
    st.divider()

    st.subheader("➕ Generate New AKUFIN Prediction")
    g1, g2, g3, g4 = st.columns([2, 2, 2, 1])

    with g1:
        ticker = st.text_input(
            "Ticker Symbol",
            value="NVDA",
            placeholder="e.g. AAPL, TSLA, SPY"
        ).upper().strip()
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
                f"✅ AKUFIN Prediction Generated: "
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
                st.markdown("### 💭 AKUFIN AI Reasoning")
                st.info(result.get("reasoning", "N/A"))
                st.markdown("### 📊 Technical Summary")
                st.write(
                    result.get("technical_summary", "N/A")
                )
            with col_b:
                st.markdown("### 🚀 Market Catalysts")
                st.success(result.get("catalysts", "N/A"))
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
        st.info(
            "No predictions yet. "
            "Generate your first AKUFIN prediction above."
        )
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
        s1.metric("Total Predictions", total)
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
                    text=(
                        f"AKUFIN Progress to target: "
                        f"{progress:.1f}%"
                    )
                )

                with st.expander(
                    f"💎 AKUFIN Full Analysis — "
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
                                "technical_summary", "N/A"
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
    st.markdown(
        "*Real-time data from Alpaca Paper Trading*"
    )
    st.divider()

    summary = services["broker"].get_portfolio_summary()
    account = summary["account"]
    positions = summary["positions"]
    orders = summary["recent_orders"]

    st.subheader("📊 AKUFIN Account Overview")
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
        "📋 Open Positions",
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
            p2.metric(
                "Quantity",
                f"{pos['qty']:.0f} shares"
            )
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
                if st.button(
                    f"❌ Close {pos['symbol']}",
                    key=f"close_{pos['symbol']}"
                ):
                    result = services[
                        "broker"
                    ].close_position(pos["symbol"])
                    if result["success"]:
                        st.success(
                            f"✅ {pos['symbol']} closed!"
                        )
                        st.rerun()
                    else:
                        st.error(
                            f"❌ {result.get('error')}"
                        )
            st.divider()
    else:
        st.info(
            "📭 No open positions yet. "
            "Use Place Paper Trade to open first trade."
        )

    st.subheader("📜 Recent Orders")
    if orders:
        for order in orders:
            side_icon = (
                "🟢"
                if "buy" in str(order["side"]).lower()
                else "🔴"
            )
            st.markdown(
                f"{side_icon} **{order['symbol']}** | "
                f"Qty: {order['qty']:.0f} | "
                f"Status: {order['status']} | "
                f"Price: ${order['filled_price']:.2f} | "
                f"Time: {order['submitted_at']}"
            )
    else:
        st.info("No recent orders.")

# ══════════════════════════════════════════════════════
# PAGE 3: PLACE PAPER TRADE (Trader/Admin Only)
# ══════════════════════════════════════════════════════
elif page == "⚡ Place Paper Trade":
    if role not in ["trader", "admin"]:
        st.error(
            "❌ Access denied. "
            "Trade execution requires trader or admin role."
        )
        st.stop()

    st.title("⚡ AKUFIN Paper Trade Execution")
    st.warning(
        "⚠️ Paper Trading Mode: "
        "No real money. Live market prices."
    )
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 AKUFIN Order Details")
        trade_ticker = st.text_input(
            "Ticker Symbol",
            value="AAPL",
            placeholder="e.g. NVDA, AAPL, SPY"
        ).upper().strip()
        trade_side = st.selectbox(
            "Order Side", ["BUY", "SELL"]
        )
        trade_qty = st.number_input(
            "Quantity (shares)",
            min_value=1, max_value=1000,
            value=5, step=1
        )
        trade_portfolio = st.selectbox(
            "Assign to Portfolio",
            ["SNIPER", "FORTRESS"]
        )
        trade_reason = st.text_area(
            "AKUFIN Trade Reason",
            placeholder=(
                "e.g. AKUFIN detected strong "
                "momentum breakout..."
            ),
            height=100
        )

    with col2:
        st.subheader("📊 AKUFIN Quick Analysis")
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
                    est_value = price * trade_qty
                    st.metric(
                        "Current Price",
                        f"${price:.2f}"
                    )
                    st.metric(
                        "Estimated Value",
                        f"${est_value:,.2f}"
                    )
                    st.metric("Trend", analysis["trend"])
                    st.metric(
                        "RSI",
                        f"{analysis['rsi']['value']:.1f}",
                        analysis["rsi"]["signal"]
                    )
                    st.metric(
                        "MACD",
                        analysis["macd"]["signal"]
                    )
                    st.metric(
                        "AKUFIN Stop",
                        f"${analysis['atr']['stop_loss']:.2f}"
                    )
                    st.metric(
                        "AKUFIN Target",
                        f"${analysis['atr']['take_profit']:.2f}"
                    )

    st.divider()
    st.subheader("✅ AKUFIN Execution Gate")

    acc = services["broker"].get_account()
    portfolio_val = acc.get("portfolio_value", 100000)

    if trade_ticker and trade_qty > 0:
        try:
            current_p = services[
                "market"
            ].get_current_price(trade_ticker)
            trade_value = current_p * trade_qty
            pct = trade_value / portfolio_val * 100

            st.markdown(
                f"**AKUFIN Order:** "
                f"{trade_side} **{trade_qty}** shares of "
                f"**{trade_ticker}** @ ~${current_p:.2f}"
            )
            st.markdown(
                f"**Estimated Cost:** ${trade_value:,.2f} "
                f"({pct:.1f}% of portfolio)"
            )

            if pct > 5:
                st.warning(
                    f"⚠️ AKUFIN Risk Alert: "
                    f"{pct:.1f}% exceeds 5% limit"
                )

            c1, c2 = st.columns(2)
            with c1:
                execute_btn = st.button(
                    f"💎 EXECUTE {trade_side}",
                    type="primary",
                    use_container_width=True
                )
            with c2:
                st.button(
                    "❌ Cancel",
                    use_container_width=True
                )

            if execute_btn:
                with st.spinner(
                    f"AKUFIN executing {trade_side} "
                    f"for {trade_ticker}..."
                ):
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
                        f"✅ AKUFIN Order Executed!\n"
                        f"Order ID: {result['order_id']}\n"
                        f"Symbol: {result['symbol']}\n"
                        f"Side: {result['side']}\n"
                        f"Qty: {result['qty']} shares\n"
                        f"Status: {result['status']}"
                    )
                    st.balloons()
                else:
                    st.error(
                        f"❌ Failed: "
                        f"{result.get('error', 'Unknown')}"
                    )
        except Exception as e:
            st.error(f"AKUFIN Error: {e}")

# ══════════════════════════════════════════════════════
# PAGE 4: PENDING APPROVALS (Trader/Admin Only)
# ══════════════════════════════════════════════════════
elif page == "⏳ Pending Approvals":
    if role not in ["trader", "admin"]:
        st.error(
            "❌ Access denied. "
            "Trade approvals require trader or admin role."
        )
        st.stop()

    st.title("⏳ AKUFIN Trade Approval Gate")
    st.info(
        "**AKUFIN Human-in-the-Loop**: "
        "AI recommends. You decide. "
        "Every trade requires your personal approval."
    )
    st.divider()

    spy_price = services[
        "market"
    ].get_current_price("SPY")
    aapl_price = services[
        "market"
    ].get_current_price("AAPL")

    trades = [
        {
            "ticker": "SPY",
            "portfolio": "SNIPER",
            "signal": "BUY",
            "entry": spy_price,
            "stop": round(spy_price * 0.98, 2),
            "target": round(spy_price * 1.04, 2),
            "confidence": 0.87,
            "qty": 3,
            "agents": [
                "Technical ✅",
                "Whale ✅",
                "Sentiment ✅"
            ],
            "reasoning": (
                "AKUFIN detected strong SPY momentum. "
                "Price above VWAP, EMA20, EMA50. "
                "Volume confirming institutional buying. "
                "All 3 AKUFIN agents agree."
            )
        },
        {
            "ticker": "AAPL",
            "portfolio": "FORTRESS",
            "signal": "BUY",
            "entry": aapl_price,
            "stop": round(aapl_price * 0.97, 2),
            "target": round(aapl_price * 1.06, 2),
            "confidence": 0.79,
            "qty": 2,
            "agents": [
                "Fundamental ✅",
                "Macro ✅",
                "Technical ✅"
            ],
            "reasoning": (
                "AKUFIN FORTRESS signal: "
                "AAPL at key support level. "
                "Strong earnings growth. "
                "AI services revenue accelerating. "
                "Long term wealth accumulation."
            )
        }
    ]

    st.warning(
        f"⏳ {len(trades)} AKUFIN signals "
        f"awaiting your approval"
    )

    for i, t in enumerate(trades):
        with st.container():
            p_icon = (
                "⚡" if t["portfolio"] == "SNIPER"
                else "🏰"
            )
            s_icon = (
                "🟢" if t["signal"] == "BUY"
                else "🔴"
            )
            risk = round(t["entry"] - t["stop"], 2)
            reward = round(t["target"] - t["entry"], 2)
            rr = round(reward / risk, 1) if risk > 0 else 0
            pos_val = round(t["entry"] * t["qty"], 2)

            st.markdown(
                f"### {p_icon} AKUFIN {t['portfolio']} | "
                f"{s_icon} {t['signal']} **{t['ticker']}**"
            )

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Entry", f"${t['entry']:.2f}")
            c2.metric(
                "Stop Loss",
                f"${t['stop']:.2f}",
                f"-${risk:.2f}"
            )
            c3.metric(
                "Target",
                f"${t['target']:.2f}",
                f"+${reward:.2f}"
            )
            c4.metric("R:R", f"{rr}:1")
            c5.metric(
                "Confidence",
                f"{t['confidence']*100:.0f}%"
            )

            st.markdown(
                f"**AKUFIN Agents:** "
                f"{' | '.join(t['agents'])}"
            )
            st.info(f"💎 {t['reasoning']}")
            st.caption(
                f"Position: {t['qty']} shares "
                f"= ${pos_val:,.2f}"
            )

            b1, b2, b3, b4 = st.columns(4)
            if b1.button(
                "✅ APPROVE & EXECUTE",
                key=f"app_{i}",
                use_container_width=True
            ):
                with st.spinner(
                    f"AKUFIN executing {t['ticker']}..."
                ):
                    result = services[
                        "broker"
                    ].place_market_order(
                        symbol=t["ticker"],
                        qty=t["qty"],
                        side=t["signal"].lower(),
                        reason=(
                            f"AKUFIN approved by "
                            f"{username}"
                        )
                    )
                if result.get("success"):
                    st.success(
                        f"✅ AKUFIN executed "
                        f"{t['ticker']}! "
                        f"Order: {result['order_id']}"
                    )
                    st.balloons()
                else:
                    st.error(
                        f"❌ Failed: "
                        f"{result.get('error')}"
                    )

            if b2.button(
                "❌ REJECT",
                key=f"rej_{i}",
                use_container_width=True
            ):
                st.error(
                    f"❌ {t['ticker']} rejected "
                    f"by {username}."
                )

            if b3.button(
                "⏰ +15 mins",
                key=f"wait_{i}",
                use_container_width=True
            ):
                st.warning(
                    "⏰ AKUFIN will re-alert "
                    "in 15 minutes."
                )

            if b4.button(
                "🔍 Details",
                key=f"det_{i}",
                use_container_width=True
            ):
                st.json(t)
            st.divider()

# ══════════════════════════════════════════════════════
# PAGE 5: LIVE ANALYSIS
# ══════════════════════════════════════════════════════
elif page == "📊 Live Analysis":
    st.title("📊 AKUFIN Live Technical Analysis")
    st.markdown(
        "*Real-time AI-powered market analysis*"
    )
    st.divider()

    a1, a2 = st.columns([3, 1])
    with a1:
        aticker = st.text_input(
            "Enter Ticker Symbol",
            value="AAPL",
            placeholder="e.g. NVDA, TSLA, SPY"
        ).upper().strip()
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
                    f"📊 AKUFIN Analysis — {aticker}"
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
                    "MACD",
                    r["macd"]["signal"]
                )

                st.divider()
                d1, d2, d3 = st.columns(3)

                with d1:
                    st.markdown(
                        "**📈 Moving Averages**"
                    )
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
                        f"{'✅ Active' if gc else '❌ No'}"
                    )

                with d2:
                    st.markdown(
                        "**📊 Bollinger Bands**"
                    )
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
                    st.markdown(
                        "**⚠️ AKUFIN Trade Levels**"
                    )
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
    st.title("📈 AKUFIN Agent Activity Feed")
    st.markdown(
        "*Live feed of all AKUFIN AI agents "
        "working autonomously*"
    )
    st.divider()

    port_filter = st.selectbox(
        "Filter by Portfolio",
        ["ALL", "SNIPER", "FORTRESS"]
    )

    activities = [
        {
            "time": "09:35",
            "agent": "💎 AKUFIN Scanner",
            "action": (
                "Morning scan complete. "
                "20 tickers analyzed. 3 signals found."
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:47",
            "agent": "🐋 Whale Hunter",
            "action": (
                "Detected $2.1M dark pool SPY. "
                "Institutional accumulation confirmed."
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:52",
            "agent": "📊 AKUFIN Technical",
            "action": (
                "SPY RSI bullish divergence. "
                "MACD crossover above VWAP confirmed."
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:58",
            "agent": "📰 AKUFIN Sentiment",
            "action": (
                "Positive market sentiment. "
                "AKUFIN score: 0.82 Bullish."
            ),
            "level": "MEDIUM",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🧠 AKUFIN Orchestrator",
            "action": (
                "SPY package assembled. "
                "3/3 agents agree. Confidence: 87%."
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🛡️ AKUFIN Risk Warden",
            "action": (
                "SPY passed all 7 safety checks. "
                "R:R = 2.0:1. Approved."
            ),
            "level": "LOW",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:03",
            "agent": "⏳ AKUFIN Human Gate",
            "action": (
                "SPY BUY sent to approval queue. "
                "Awaiting administrator decision."
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:15",
            "agent": "📊 AKUFIN Fundamental",
            "action": (
                "AAPL earnings growth confirmed. "
                "FORTRESS opportunity identified."
            ),
            "level": "MEDIUM",
            "portfolio": "FORTRESS"
        },
        {
            "time": "10:22",
            "agent": "💎 AKUFIN Prediction",
            "action": (
                "AAPL → $225 in 21 days. "
                "Confidence: 79%. FORTRESS signal."
            ),
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
# PAGE 7: ADMIN PANEL (Admin Only)
# ══════════════════════════════════════════════════════
elif page == "🔑 Admin Panel":
    if role != "admin":
        st.error(
            "❌ Access denied. "
            "Admin panel requires administrator role."
        )
        st.stop()
    show_admin_panel()

# ── AKUFIN Footer ─────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#DAA520'>"
    "💎 <strong>AKUFIN</strong> — "
    "Intelligence for Wealth Accrual | "
    "Powered by AI Agents | "
    "Paper Trading Mode ✅ | "
    f"© {datetime.now().year} AKUFIN Technologies | "
    "Private & Confidential"
    "</div>",
    unsafe_allow_html=True
)
