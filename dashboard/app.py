# dashboard/app.py
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

st.set_page_config(
    page_title="AkuFi - AI Wealth Intelligence",
    page_icon="💎",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; color: #e0e0e0; }
    [data-testid="metric-container"] {
        background: linear-gradient(
            135deg, #1a1f35 0%, #0d1117 100%
        );
        border: 1px solid #2d3561;
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
    }
    div[data-testid="stExpander"] {
        background: #1a1f35;
        border: 1px solid #2d3561;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg, #0d1117 0%, #1a1f35 100%
        );
        border-right: 1px solid #DAA520;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_services():
    return {
        "market": MarketDataFetcher(),
        "indicators": TechnicalIndicators(),
        "predictor": PredictionEngine(),
        "broker": AlpacaBroker()
    }


services = get_services()

# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💎 AkuFi")
    st.markdown("*Intelligence for Wealth Accrual*")
    st.markdown(
        "<small style='color:#DAA520'>"
        "From the Igbo word for Wealth"
        "</small>",
        unsafe_allow_html=True
    )
    st.divider()

    page = st.selectbox(
        "Navigation",
        [
            "🏠 Dashboard Home",
            "🎯 AI Predictions",
            "💼 Live Portfolio",
            "⚡ Place Paper Trade",
            "⏳ Pending Approvals",
            "📊 Live Analysis",
            "📈 Agent Activity"
        ]
    )

    st.divider()
    status = services["market"].get_market_status()
    if status["is_open"]:
        st.success("🟢 Market Open")
    else:
        st.error("🔴 Market Closed")
    st.caption(f"Session: {status['session']}")
    st.divider()

    try:
        acc = services["broker"].get_account()
        st.metric(
            "AkuFi Portfolio",
            f"${acc['portfolio_value']:,.0f}",
            f"${acc['daily_pl']:+,.2f} today"
        )
    except:
        st.metric("AkuFi Portfolio", "$100,000")

    st.divider()
    st.caption(
        f"Updated: {datetime.now().strftime('%H:%M:%S')}"
    )
    if st.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()

# ══════════════════════════════════════════════════════
# PAGE 0: DASHBOARD HOME
# ══════════════════════════════════════════════════════
if page == "🏠 Dashboard Home":
    st.title("💎 AkuFi")
    st.markdown(
        "### AI-Powered Wealth Intelligence Platform"
    )
    st.markdown(
        "*Aku (Igbo: Wealth) · Predictive · Autonomous · Precise*"
    )
    st.divider()

    summary = services["broker"].get_portfolio_summary()
    account = summary["account"]
    predictions = services["predictor"].get_all_predictions()

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
    st.subheader("🎯 Recent AkuFi Predictions")
    if predictions:
        for pred in predictions[:3]:
            dir_icon = (
                "🟢" if pred.get(
                    "predicted_direction"
                ) == "UP" else "🔴"
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
    st.subheader("🤖 AkuFi Agent Status")
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
    st.title("🎯 AkuFi Market Predictions")
    st.markdown(
        "*AI-generated price predictions tracked "
        "against real market outcomes*"
    )
    st.divider()

    st.subheader("➕ Generate New AkuFi Prediction")
    g1, g2, g3, g4 = st.columns([2, 2, 2, 1])

    with g1:
        ticker = st.text_input(
            "Ticker Symbol", value="NVDA",
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
            f"AkuFi AI analyzing {ticker}..."
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
            dir_icon = "🟢" if direction == "UP" else "🔴"
            change = result.get("price_change_pct", 0)
            conf = result.get("confidence", 0) * 100

            st.success(
                f"✅ AkuFi Prediction Generated for "
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
                st.markdown("### 💭 AkuFi AI Reasoning")
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
    st.subheader("📋 AkuFi Prediction Tracker")
    predictions = services["predictor"].get_all_predictions()

    if not predictions:
        st.info(
            "No predictions yet. "
            "Generate your first AkuFi prediction above."
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
        s4.metric("AkuFi Accuracy", f"{accuracy}%")
        st.divider()

        for pred in predictions:
            dir_icon = (
                "🟢 UP"
                if pred.get("predicted_direction") == "UP"
                else "🔴 DOWN"
            )
            port_icon = (
                "⚡" if pred.get("portfolio") == "SNIPER"
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
                    text=f"Progress to target: {progress:.1f}%"
                )

                with st.expander(
                    f"💎 Full AkuFi Analysis — {pred['ticker']}"
                ):
                    r1, r2 = st.columns(2)
                    with r1:
                        st.markdown("**💭 Reasoning:**")
                        st.write(pred.get("reasoning", "N/A"))
                        st.markdown("**📊 Technical:**")
                        st.write(
                            pred.get(
                                "technical_summary", "N/A"
                            )
                        )
                    with r2:
                        st.markdown("**🚀 Catalysts:**")
                        st.write(pred.get("catalysts", "N/A"))
                        st.markdown("**⚠️ Risks:**")
                        st.write(
                            pred.get("risk_factors", "N/A")
                        )
                    st.caption(
                        f"Generated: {pred.get('created_at', '')}"
                    )
                st.divider()

# ══════════════════════════════════════════════════════
# PAGE 2: LIVE PORTFOLIO
# ══════════════════════════════════════════════════════
elif page == "💼 Live Portfolio":
    st.title("💼 AkuFi Live Portfolio")
    st.markdown(
        "*Real-time data from your Alpaca "
        "Paper Trading account*"
    )
    st.divider()

    summary = services["broker"].get_portfolio_summary()
    account = summary["account"]
    positions = summary["positions"]
    orders = summary["recent_orders"]

    st.subheader("📊 AkuFi Account Overview")
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
                "Entry Price",
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
                "Market Value",
                f"${pos['market_value']:,.2f}"
            )

            if st.button(
                f"❌ Close {pos['symbol']}",
                key=f"close_{pos['symbol']}"
            ):
                result = services["broker"].close_position(
                    pos["symbol"]
                )
                if result["success"]:
                    st.success(
                        f"✅ {pos['symbol']} position closed!"
                    )
                    st.rerun()
                else:
                    st.error(
                        f"❌ Failed: {result.get('error')}"
                    )
            st.divider()
    else:
        st.info(
            "📭 No open positions yet. "
            "Use 'Place Paper Trade' to open your first trade."
        )

    st.subheader("📜 Recent Orders")
    if orders:
        for order in orders:
            side_icon = (
                "🟢" if "buy" in str(
                    order["side"]
                ).lower() else "🔴"
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
# PAGE 3: PLACE PAPER TRADE
# ══════════════════════════════════════════════════════
elif page == "⚡ Place Paper Trade":
    st.title("⚡ AkuFi Paper Trade Execution")
    st.markdown(
        "*Test the AkuFi execution engine with paper money*"
    )
    st.warning(
        "⚠️ **Paper Trading Mode**: "
        "No real money is used. "
        "All trades are simulated on live market prices."
    )
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Order Details")
        trade_ticker = st.text_input(
            "Ticker Symbol", value="AAPL",
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
            "Reason for Trade",
            placeholder=(
                "e.g. AkuFi detected strong momentum "
                "breakout with RSI oversold bounce..."
            ),
            height=100
        )

    with col2:
        st.subheader("📊 AkuFi Quick Analysis")
        if trade_ticker:
            df = services["market"].get_historical_bars(
                trade_ticker, period="1mo"
            )
            if not df.empty:
                analysis = services[
                    "indicators"
                ].get_full_analysis(df, trade_ticker)
                if "error" not in analysis:
                    current_price = analysis["current_price"]
                    est_value = current_price * trade_qty
                    st.metric(
                        "Current Price",
                        f"${current_price:.2f}"
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
                        "Suggested Stop",
                        f"${analysis['atr']['stop_loss']:.2f}"
                    )
                    st.metric(
                        "Suggested Target",
                        f"${analysis['atr']['take_profit']:.2f}"
                    )

    st.divider()
    st.subheader("✅ AkuFi Execution Gate")

    
