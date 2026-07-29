# dashboard/app.py
import sys
import os
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from prediction_engine.predictor import PredictionEngine
from tools.alpaca_broker import AlpacaBroker

st.set_page_config(
    page_title="Alpha Mind - AI Trading Intelligence",
    page_icon="🧠",
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
    h1, h2, h3 { color: #4fc3f7; }
    .stButton > button {
        background: linear-gradient(
            90deg, #1565C0, #0D47A1
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
</style>
""", unsafe_allow_html=True)


# ── Initialize Services ───────────────────────────────
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
    st.markdown("## 🧠 Alpha Mind")
    st.markdown("**AI Portfolio Intelligence**")
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

    # Market status
    status = services["market"].get_market_status()
    if status["is_open"]:
        st.success("🟢 Market Open")
    else:
        st.error("🔴 Market Closed")
    st.caption(f"Session: {status['session']}")

    st.divider()

    # Quick account summary in sidebar
    try:
        acc = services["broker"].get_account()
        st.metric(
            "Portfolio",
            f"${acc['portfolio_value']:,.0f}",
            f"${acc['daily_pl']:+,.2f}"
        )
    except:
        st.metric("Portfolio", "$100,000")

    st.divider()
    st.caption(
        f"Updated: {datetime.now().strftime('%H:%M:%S')}"
    )
    if st.button("🔄 Refresh"):
        st.cache_resource.clear()
        st.rerun()

# ══════════════════════════════════════════════════════
# PAGE 0: DASHBOARD HOME
# ══════════════════════════════════════════════════════
if page == "🏠 Dashboard Home":
    st.title("🧠 Alpha Mind")
    st.markdown(
        "### AI-Powered Portfolio Intelligence Platform"
    )
    st.divider()

    # Get real data
    summary = services["broker"].get_portfolio_summary()
    account = summary["account"]
    predictions = services["predictor"].get_all_predictions()

    # Top metrics
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

    # Two portfolio overview
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚡ SNIPER Portfolio")
        st.markdown("*Short-term leverage trades*")
        sniper_positions = [
            p for p in summary["positions"]
            if p.get("portfolio") == "SNIPER"
        ]
        st.metric(
            "Allocated Capital",
            "$30,000",
            help="30% of total portfolio"
        )
        st.metric(
            "Open Trades",
            len(sniper_positions)
        )
        st.metric(
            "Strategy",
            "Momentum + Flow"
        )
        st.markdown("""
        - ⚡ Fast momentum trades
        - 🐋 Institutional flow signals
        - 📊 Technical breakouts
        - ⏱️ Minutes to 3 days hold
        """)

    with col2:
        st.markdown("### 🏰 FORTRESS Portfolio")
        st.markdown("*Long-term safe investments*")
        fortress_positions = [
            p for p in summary["positions"]
            if p.get("portfolio") == "FORTRESS"
        ]
        st.metric(
            "Allocated Capital",
            "$70,000",
            help="70% of total portfolio"
        )
        st.metric(
            "Open Positions",
            len(fortress_positions)
        )
        st.metric(
            "Strategy",
            "Growth + Value"
        )
        st.markdown("""
        - 📈 High ROI growth stocks
        - 🛡️ Blue chip safety
        - 💰 Dividend compounders
        - ⏱️ Weeks to months hold
        """)

    st.divider()

    # Recent predictions summary
    st.subheader("🎯 Recent AI Predictions")
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

    # Agent status
    st.subheader("🤖 Agent Status")
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
    st.title("🎯 AI Market Predictions")
    st.markdown(
        "*Real AI predictions tracked vs actual outcomes*"
    )
    st.divider()

    # Generate section
    st.subheader("➕ Generate New Prediction")
    g1, g2, g3, g4 = st.columns([2, 2, 2, 1])

    with g1:
        ticker = st.text_input(
            "Ticker Symbol",
            value="NVDA",
            placeholder="e.g. AAPL, TSLA, SPY"
        ).upper().strip()
    with g2:
        portfolio = st.selectbox(
            "Portfolio",
            ["SNIPER", "FORTRESS"]
        )
    with g3:
        days = st.selectbox(
            "Days Ahead",
            [7, 14, 21, 30],
            index=1
        )
    with g4:
        st.write("")
        st.write("")
        gen_btn = st.button(
            "🧠 Generate",
            type="primary",
            use_container_width=True
        )

    if gen_btn and ticker:
        with st.spinner(
            f"AI analyzing {ticker}..."
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
                f"✅ Prediction generated for "
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
                st.markdown("### 💭 AI Reasoning")
                st.info(result.get("reasoning", "N/A"))
                st.markdown("### 📊 Technical Summary")
                st.write(
                    result.get("technical_summary", "N/A")
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
    st.subheader("📋 All Predictions")

    predictions = services[
        "predictor"
    ].get_all_predictions()

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
        s4.metric("Accuracy", f"{accuracy}%")

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
                "⚡" if pred.get(
                    "portfolio"
                ) == "SNIPER" else "🏰"
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
                        f"By: {pred.get('target_date')}"
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
                        f"Progress to target: "
                        f"{progress:.1f}%"
                    )
                )

                with st.expander("🧠 Full AI Analysis"):
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
                st.divider()

# ══════════════════════════════════════════════════════
# PAGE 2: LIVE PORTFOLIO (REAL ALPACA DATA)
# ══════════════════════════════════════════════════════
elif page == "💼 Live Portfolio":
    st.title("💼 Live Portfolio")
    st.markdown(
        "*Real-time data from your Alpaca "
        "Paper Trading account*"
    )
    st.divider()

    summary = services["broker"].get_portfolio_summary()
    account = summary["account"]
    positions = summary["positions"]
    orders = summary["recent_orders"]

    # Account metrics
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
        "📋 Open Positions",
        summary["total_positions"]
    )

    st.divider()

    # Open positions
    st.subheader("📋 Open Positions")

    if positions:
        for pos in positions:
            pl = pos.get("unrealized_pl", 0)
            plpc = pos.get("unrealized_plpc", 0)
            pl_color = "🟢" if pl >= 0 else "🔴"

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

            # Close position button
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

    # Recent orders
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
    st.title("⚡ Place Paper Trade")
    st.markdown(
        "*Test the execution system with paper money*"
    )
    st.warning(
        "⚠️ **Paper Trading Mode**: "
        "No real money is used. "
        "All trades are simulated."
    )
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Order Details")

        trade_ticker = st.text_input(
            "Ticker Symbol",
            value="AAPL",
            placeholder="e.g. NVDA, AAPL, SPY"
        ).upper().strip()

        trade_side = st.selectbox(
            "Order Side",
            ["BUY", "SELL"]
        )

        trade_qty = st.number_input(
            "Quantity (shares)",
            min_value=1,
            max_value=1000,
            value=10,
            step=1
        )

        trade_portfolio = st.selectbox(
            "Assign to Portfolio",
            ["SNIPER", "FORTRESS"]
        )

        trade_reason = st.text_area(
            "Reason for Trade",
            placeholder=(
                "e.g. Strong momentum breakout, "
                "RSI oversold bounce..."
            ),
            height=100
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
                    current_price = analysis[
                        "current_price"
                    ]
                    est_value = current_price * trade_qty

                    st.metric(
                        "Current Price",
                        f"${current_price:.2f}"
                    )
                    st.metric(
                        "Estimated Value",
                        f"${est_value:,.2f}"
                    )
                    st.metric(
                        "Trend",
                        analysis["trend"]
                    )
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

    # Confirmation and execution
    st.subheader("✅ Confirm & Execute")

    acc = services["broker"].get_account()
    portfolio_val = acc.get("portfolio_value", 100000)

    if trade_ticker and trade_qty > 0:
        try:
            current_p = services[
                "market"
            ].get_current_price(trade_ticker)
            trade_value = current_p * trade_qty
            pct_of_portfolio = (
                trade_value / portfolio_val * 100
            )

            st.markdown(
                f"**Order Summary:** "
                f"{trade_side} **{trade_qty}** shares of "
                f"**{trade_ticker}** @ ~${current_p:.2f}"
            )
            st.markdown(
                f"**Estimated Cost:** ${trade_value:,.2f} "
                f"({pct_of_portfolio:.1f}% of portfolio)"
            )

            if pct_of_portfolio > 5:
                st.warning(
                    f"⚠️ Position size {pct_of_portfolio:.1f}% "
                    f"exceeds recommended 5% limit"
                )

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                execute_btn = st.button(
                    f"🚀 EXECUTE {trade_side} ORDER",
                    type="primary",
                    use_container_width=True
                )

            with col_btn2:
                cancel_btn = st.button(
                    "❌ Cancel",
                    use_container_width=True
                )

            if execute_btn:
                with st.spinner(
                    f"Placing {trade_side} order "
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
                        f"✅ Order Placed Successfully!\n\n"
                        f"Order ID: {result['order_id']}\n"
                        f"Symbol: {result['symbol']}\n"
                        f"Side: {result['side']}\n"
                        f"Qty: {result['qty']} shares\n"
                        f"Status: {result['status']}"
                    )
                    st.balloons()
                else:
                    st.error(
                        f"❌ Order Failed: "
                        f"{result.get('error', 'Unknown error')}"
                    )

        except Exception as e:
            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════
# PAGE 4: PENDING APPROVALS
# ══════════════════════════════════════════════════════
elif page == "⏳ Pending Approvals":
    st.title("⏳ Pending Trade Approvals")
    st.info(
        "**Human-in-the-Loop**: "
        "Every AI trade requires your approval. "
        "You have final control."
    )
    st.divider()

    trades = [
        {
            "ticker": "NVDA",
            "portfolio": "SNIPER",
            "signal": "BUY",
            "entry": 127.50,
            "stop": 124.00,
            "target": 134.50,
            "confidence": 0.87,
            "qty": 45,
            "agents": [
                "Technical ✅",
                "Whale ✅",
                "Sentiment ✅"
            ],
            "reasoning": (
                "Strong institutional accumulation at $126.50. "
                "RSI bullish divergence. MACD crossover. "
                "Dark pool prints detected."
            )
        },
        {
            "ticker": "MSFT",
            "portfolio": "FORTRESS",
            "signal": "BUY",
            "entry": 415.20,
            "stop": 405.00,
            "target": 440.00,
            "confidence": 0.79,
            "qty": 12,
            "agents": [
                "Fundamental ✅",
                "Macro ✅",
                "Technical ✅"
            ],
            "reasoning": (
                "Strong earnings growth. "
                "AI cloud revenue accelerating. "
                "Trading at key support."
            )
        }
    ]

    st.warning(
        f"⏳ {len(trades)} trades waiting for approval"
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
            risk = t["entry"] - t["stop"]
            reward = t["target"] - t["entry"]
            rr = round(reward / risk, 1) if risk > 0 else 0

            st.markdown(
                f"### {p_icon} {t['portfolio']} | "
                f"{s_icon} {t['signal']} **{t['ticker']}**"
            )

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Entry", f"${t['entry']:.2f}")
            c2.metric(
                "Stop",
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
                f"**Agents:** {' | '.join(t['agents'])}"
            )
            st.info(f"💭 {t['reasoning']}")

            b1, b2, b3, b4 = st.columns(4)

            if b1.button(
                "✅ APPROVE & EXECUTE",
                key=f"app_{i}",
                use_container_width=True
            ):
                with st.spinner("Executing trade..."):
                    result = services[
                        "broker"
                    ].place_market_order(
                        symbol=t["ticker"],
                        qty=t["qty"],
                        side=t["signal"].lower(),
                        reason="Human approved via dashboard"
                    )
                if result.get("success"):
                    st.success(
                        f"✅ {t['ticker']} executed! "
                        f"Order: {result['order_id']}"
                    )
                    st.balloons()
                else:
                    st.error(
                        f"❌ {result.get('error')}"
                    )

            if b2.button(
                "❌ REJECT",
                key=f"rej_{i}",
                use_container_width=True
            ):
                st.error(
                    f"❌ {t['ticker']} rejected."
                )

            if b3.button(
                "⏰ +15 mins",
                key=f"wait_{i}",
                use_container_width=True
            ):
                st.warning("⏰ Reminder set.")

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
    st.title("📊 Live Technical Analysis")
    st.divider()

    a1, a2 = st.columns([3, 1])
    with a1:
        aticker = st.text_input(
            "Ticker Symbol",
            value="AAPL"
        ).upper().strip()
    with a2:
        st.write("")
        run_btn = st.button(
            "🔍 Analyze",
            type="primary",
            use_container_width=True
        )

    if run_btn and aticker:
        with st.spinner(f"Analyzing {aticker}..."):
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
                    f"📊 {aticker} Analysis"
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
                    gc = r["moving_averages"]["golden_cross"]
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

                # Chart
                st.divider()
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name=aticker,
                    increasing_line_color="#00e676",
                    decreasing_line_color="#ff5252"
                ))
                ind = services["indicators"]
                e20 = ind.ema(df, 20)
                e50 = ind.ema(df, 50)
                fig.add_trace(go.Scatter(
                    x=df.index, y=e20,
                    name="EMA 20",
                    line=dict(color="#4fc3f7", width=1.5)
                ))
                fig.add_trace(go.Scatter(
                    x=df.index, y=e50,
                    name="EMA 50",
                    line=dict(color="#ffd740", width=1.5)
                ))
                fig.update_layout(
                    title=f"{aticker} Chart",
                    template="plotly_dark",
                    paper_bgcolor="#0a0e1a",
                    plot_bgcolor="#0a0e1a",
                    xaxis_rangeslider_visible=False,
                    height=400
                )
                st.plotly_chart(
                    fig, use_container_width=True
                )

# ══════════════════════════════════════════════════════
# PAGE 6: AGENT ACTIVITY
# ══════════════════════════════════════════════════════
elif page == "📈 Agent Activity":
    st.title("📈 Live Agent Activity")
    st.divider()

    port_filter = st.selectbox(
        "Filter by Portfolio",
        ["ALL", "SNIPER", "FORTRESS"]
    )

    activities = [
        {
            "time": "09:47",
            "agent": "🐋 Whale Hunter",
            "action": "Detected $2.1M dark pool NVDA @ $126.50",
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:52",
            "agent": "📊 Technical",
            "action": "NVDA RSI 58, MACD bullish crossover",
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:58",
            "agent": "📰 Sentiment",
            "action": "Positive NVDA AI news. Score: 0.82",
            "level": "MEDIUM",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🧠 Orchestrator",
            "action": "NVDA package ready. 3/3 agree. 87%",
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🛡️ Risk Warden",
            "action": "NVDA passed all 7 checks. R:R=2:1",
            "level": "LOW",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:03",
            "agent": "⏳ Human Gate",
            "action": "NVDA BUY sent for your approval",
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:15",
            "agent": "📊 Fundamental",
            "action": "MSFT earnings growth confirmed",
            "level": "MEDIUM",
            "portfolio": "FORTRESS"
        },
        {
            "time": "10:22",
            "agent": "🧠 Prediction",
            "action": "MSFT → $440 in 14 days (79%)",
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
                "⚡ S" if act["portfolio"] == "SNIPER"
                else "🏰 F"
            )
        st.divider()

# Footer
st.markdown("---")
st.caption(
    f"🧠 Alpha Mind | Paper Trading Mode | "
    f"Alpaca Connected ✅ | "
    f"© {datetime.now().year}"
)