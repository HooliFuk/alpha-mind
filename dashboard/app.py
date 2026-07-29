# dashboard/app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from tools.market_data import MarketDataFetcher
from tools.indicators import TechnicalIndicators
from prediction_engine.predictor import PredictionEngine

st.set_page_config(
    page_title="Alpha Mind - AI Trading Intelligence",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; color: #e0e0e0; }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%);
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 15px;
    }
    h1, h2, h3 { color: #4fc3f7; }
    .stButton > button {
        background: linear-gradient(90deg, #1565C0, #0D47A1);
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


@st.cache_resource
def get_services():
    return {
        "market": MarketDataFetcher(),
        "indicators": TechnicalIndicators(),
        "predictor": PredictionEngine()
    }


services = get_services()

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Alpha Mind")
    st.markdown("**AI Portfolio Intelligence Platform**")
    st.divider()

    page = st.selectbox(
        "Navigation",
        [
            "🎯 AI Predictions",
            "💼 Portfolio Overview",
            "⏳ Pending Approvals",
            "📊 Live Analysis",
            "📈 Agent Activity"
        ]
    )

    st.divider()
    status = services["market"].get_market_status()
    if status["is_open"]:
        st.success("🟢 Market is Open")
    else:
        st.error("🔴 Market is Closed")
    st.caption(f"Session: {status['session']}")
    st.divider()
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Refresh"):
        st.cache_resource.clear()
        st.rerun()

# ══════════════════════════════════════════════
# PAGE 1: AI PREDICTIONS
# ══════════════════════════════════════════════
if page == "🎯 AI Predictions":
    st.title("🎯 AI Market Predictions")
    st.markdown(
        "*Real AI-generated predictions tracked against actual outcomes*"
    )
    st.divider()

    # ── Generate Section ──────────────────────
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
            "Portfolio Type",
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

    # Store result in session state so it persists
    if gen_btn and ticker:
        with st.spinner(f"🤖 AI analyzing {ticker}... Please wait"):
            result = services["predictor"].generate_prediction(
                ticker=ticker,
                portfolio=portfolio,
                days_ahead=days
            )
        st.session_state["last_prediction"] = result

    # Show result if exists in session
    if "last_prediction" in st.session_state:
        result = st.session_state["last_prediction"]

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            direction = result.get("predicted_direction", "UP")
            dir_icon = "🟢" if direction == "UP" else "🔴"
            conf = result.get("confidence", 0) * 100
            change = result.get("price_change_pct", 0)

            st.success(
                f"✅ AI Prediction Generated for "
                f"**{result['ticker']}**"
            )

            st.markdown("---")

            # Main metrics row
            m1, m2, m3, m4, m5 = st.columns(5)

            m1.metric(
                label="📍 Current Price",
                value=f"${result['current_price']:.2f}"
            )
            m2.metric(
                label="🎯 Predicted Price",
                value=f"${result['predicted_price']:.2f}",
                delta=f"{change:+.1f}%"
            )
            m3.metric(
                label="📈 Direction",
                value=f"{dir_icon} {direction}"
            )
            m4.metric(
                label="🎲 Confidence",
                value=f"{conf:.0f}%"
            )
            m5.metric(
                label="📅 Target Date",
                value=result.get("target_date", "N/A")
            )

            st.markdown("---")

            # Reasoning section
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("### 💭 AI Reasoning")
                st.info(result.get("reasoning", "N/A"))

                st.markdown("### 📊 Technical Summary")
                st.write(result.get("technical_summary", "N/A"))

            with col_b:
                st.markdown("### 🚀 Catalysts")
                st.success(result.get("catalysts", "N/A"))

                st.markdown("### ⚠️ Risk Factors")
                st.warning(result.get("risk_factors", "N/A"))

            st.markdown("---")
            st.caption(
                f"Portfolio: **{result.get('portfolio')}** | "
                f"Conviction: **{result.get('conviction', 'MEDIUM')}** | "
                f"Generated: {result.get('created_at', '')}"
            )

    st.divider()

    # ── All Predictions ───────────────────────
    st.subheader("📋 All Predictions & Accuracy Tracking")

    predictions = services["predictor"].get_all_predictions()

    if not predictions:
        st.info(
            "No predictions yet. "
            "Generate your first one above."
        )
    else:
        # Scorecard
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

        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("📊 Total", total)
        s2.metric("🟢 Active", active)
        s3.metric("✅ Resolved", resolved)
        s4.metric("🎯 Correct", correct)
        s5.metric(
            "🏆 Accuracy",
            f"{accuracy}%"
        )

        st.divider()

        # Individual cards
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
            current = pred.get("current_price_now", 0)
            entry = pred.get("current_price_at_prediction", 0)
            target = pred.get("predicted_price", 0)
            change_so_far = pred.get("price_change_so_far_pct", 0)
            progress = pred.get("progress_to_target_pct", 0)

            with st.container():
                # Header row
                h1, h2, h3 = st.columns([3, 2, 1])
                with h1:
                    st.markdown(
                        f"### {port_icon} **{pred['ticker']}** "
                        f"→ {dir_icon} → "
                        f"**${target:.2f}**"
                    )
                with h2:
                    st.caption(
                        f"Target: {pred.get('target_date', 'N/A')}"
                    )
                with h3:
                    if conf_pct >= 75:
                        st.success(f"{conf_pct:.0f}%")
                    elif conf_pct >= 60:
                        st.warning(f"{conf_pct:.0f}%")
                    else:
                        st.error(f"{conf_pct:.0f}%")

                # Metrics row
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(
                    "Entry Price",
                    f"${entry:.2f}"
                )
                c2.metric(
                    "Current Price",
                    f"${current:.2f}",
                    f"{change_so_far:+.1f}%"
                )
                c3.metric(
                    "Target Price",
                    f"${target:.2f}"
                )
                c4.metric(
                    "Portfolio",
                    pred.get("portfolio", "N/A")
                )

                # Progress bar
                st.progress(
                    min(progress / 100, 1.0),
                    text=(
                        f"Progress to target: {progress:.1f}%"
                    )
                )

                # Expandable reasoning
                with st.expander(
                    f"🧠 View Full AI Analysis"
                ):
                    r1, r2 = st.columns(2)
                    with r1:
                        st.markdown("**💭 Reasoning:**")
                        st.write(pred.get("reasoning", "N/A"))
                        st.markdown("**📊 Technical:**")
                        st.write(
                            pred.get("technical_summary", "N/A")
                        )
                    with r2:
                        st.markdown("**🚀 Catalysts:**")
                        st.write(pred.get("catalysts", "N/A"))
                        st.markdown("**⚠️ Risks:**")
                        st.write(pred.get("risk_factors", "N/A"))
                    st.caption(
                        f"Created: {pred.get('created_at', '')}"
                    )

                st.divider()

# ══════════════════════════════════════════════
# PAGE 2: PORTFOLIO OVERVIEW
# ══════════════════════════════════════════════
elif page == "💼 Portfolio Overview":
    st.title("💼 Portfolio Overview")
    st.markdown("*Two portfolio strategy - SNIPER + FORTRESS*")
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "## ⚡ SNIPER Portfolio"
        )
        st.caption("Short-term leverage trades")
        st.metric("Portfolio Value", "$30,000", "+$842 today")
        st.metric("Win Rate", "68%", "+3% this week")
        st.metric("Open Trades", "3")
        st.metric("Today P&L", "+$842", "+2.8%")
        st.markdown("---")
        st.markdown("**Strategy:**")
        st.markdown("""
        - ⚡ Momentum plays
        - 🐋 Institutional flow following
        - 📊 Technical breakouts
        - ⏱️ Hold: Minutes to 3 days
        - 📈 Leverage: 2x-5x allowed
        """)

    with col2:
        st.markdown(
            "## 🏰 FORTRESS Portfolio"
        )
        st.caption("Long-term safe investments")
        st.metric(
            "Portfolio Value",
            "$70,000",
            "+$2,100 this month"
        )
        st.metric("Win Rate", "82%", "+1% this month")
        st.metric("Open Positions", "5")
        st.metric("Month P&L", "+$2,100", "+3.0%")
        st.markdown("---")
        st.markdown("**Strategy:**")
        st.markdown("""
        - 📈 High ROI growth stocks
        - 🛡️ Blue chip safe positions
        - 💰 Dividend compounders
        - ⏱️ Hold: Weeks to months
        - 🔒 No leverage
        """)

    st.divider()
    st.subheader("📈 Live Price Chart")

    tc1, tc2 = st.columns([1, 3])
    with tc1:
        chart_ticker = st.text_input(
            "Symbol", "SPY"
        ).upper()
        chart_period = st.selectbox(
            "Period",
            ["1mo", "3mo", "6mo", "1y"],
            index=1
        )
        show_ema = st.checkbox("EMAs", value=True)
        show_bb = st.checkbox(
            "Bollinger Bands", value=False
        )

    with tc2:
        df = services["market"].get_historical_bars(
            chart_ticker, period=chart_period
        )
        if not df.empty:
            ind = services["indicators"]
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=chart_ticker,
                increasing_line_color='#00e676',
                decreasing_line_color='#ff5252'
            ))
            if show_ema and len(df) >= 20:
                e20 = ind.ema(df, 20)
                e50 = ind.ema(df, 50)
                fig.add_trace(go.Scatter(
                    x=df.index, y=e20,
                    name="EMA 20",
                    line=dict(color='#4fc3f7', width=1.5)
                ))
                fig.add_trace(go.Scatter(
                    x=df.index, y=e50,
                    name="EMA 50",
                    line=dict(color='#ffd740', width=1.5)
                ))
            if show_bb:
                up, mid, lo = ind.bollinger_bands(df)
                fig.add_trace(go.Scatter(
                    x=df.index, y=up,
                    name="BB Upper",
                    line=dict(
                        color='#ff80ab',
                        width=1,
                        dash='dash'
                    )
                ))
                fig.add_trace(go.Scatter(
                    x=df.index, y=lo,
                    name="BB Lower",
                    line=dict(
                        color='#ff80ab',
                        width=1,
                        dash='dash'
                    ),
                    fill='tonexty',
                    fillcolor='rgba(255,128,171,0.05)'
                ))
            fig.update_layout(
                title=f"{chart_ticker} Chart",
                template="plotly_dark",
                paper_bgcolor='#0a0e1a',
                plot_bgcolor='#0a0e1a',
                xaxis_rangeslider_visible=False,
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"No data for {chart_ticker}")

# ══════════════════════════════════════════════
# PAGE 3: PENDING APPROVALS
# ══════════════════════════════════════════════
elif page == "⏳ Pending Approvals":
    st.title("⏳ Pending Trade Approvals")
    st.info(
        "**Human-in-the-Loop**: "
        "You have FINAL say on every trade. "
        "The AI recommends. You decide."
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
            "agents": ["Technical ✅", "Whale ✅", "Sentiment ✅"],
            "reasoning": (
                "Strong institutional accumulation at $126.50. "
                "RSI bullish divergence. MACD crossover confirmed. "
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
                "Trading at key support level."
            )
        }
    ]

    st.warning(
        f"⏳ {len(trades)} trades waiting for your approval"
    )

    for i, t in enumerate(trades):
        with st.container():
            p_icon = "⚡" if t['portfolio'] == "SNIPER" else "🏰"
            s_icon = "🟢" if t['signal'] == "BUY" else "🔴"

            st.markdown(
                f"### {p_icon} {t['portfolio']} | "
                f"{s_icon} {t['signal']} **{t['ticker']}**"
            )

            risk = t['entry'] - t['stop']
            reward = t['target'] - t['entry']
            rr = round(reward / risk, 1) if risk > 0 else 0
            val = t['entry'] * t['qty']

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
                f"**Agents:** {' | '.join(t['agents'])}"
            )
            st.info(f"💭 {t['reasoning']}")
            st.caption(
                f"Position: {t['qty']} shares "
                f"= ${val:,.0f}"
            )

            b1, b2, b3, b4 = st.columns(4)
            if b1.button(
                "✅ APPROVE",
                key=f"a{i}",
                use_container_width=True
            ):
                st.success(
                    f"✅ {t['ticker']} approved! "
                    f"Sending to execution..."
                )
            if b2.button(
                "❌ REJECT",
                key=f"r{i}",
                use_container_width=True
            ):
                st.error(f"❌ {t['ticker']} rejected.")
            if b3.button(
                "⏰ +15 mins",
                key=f"w{i}",
                use_container_width=True
            ):
                st.warning("⏰ Reminder set.")
            if b4.button(
                "🔍 Details",
                key=f"d{i}",
                use_container_width=True
            ):
                st.json(t)

            st.divider()

# ══════════════════════════════════════════════
# PAGE 4: LIVE ANALYSIS
# ══════════════════════════════════════════════
elif page == "📊 Live Analysis":
    st.title("📊 Live Technical Analysis")
    st.markdown(
        "*Real-time technical breakdown of any ticker*"
    )
    st.divider()

    a1, a2 = st.columns([3, 1])
    with a1:
        aticker = st.text_input(
            "Enter Ticker",
            value="AAPL"
        ).upper().strip()
    with a2:
        st.write("")
        run_btn = st.button(
            "🔍 Analyze",
            use_container_width=True,
            type="primary"
        )

    if run_btn and aticker:
        with st.spinner(f"Analyzing {aticker}..."):
            df = services["market"].get_historical_bars(
                aticker, "6mo"
            )

        if df.empty:
            st.error(f"No data found for {aticker}")
        else:
            r = services["indicators"].get_full_analysis(
                df, aticker
            )
            if "error" in r:
                st.error(r["error"])
            else:
                st.subheader(
                    f"📊 {aticker} Full Analysis"
                )

                t1, t2, t3, t4 = st.columns(4)
                t1.metric(
                    "Price",
                    f"${r['current_price']:.2f}"
                )
                t2.metric("Trend", r['trend'])
                t3.metric(
                    "RSI",
                    f"{r['rsi']['value']:.1f}",
                    r['rsi']['signal']
                )
                t4.metric(
                    "MACD",
                    r['macd']['signal']
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
                    gc = r['moving_averages']['golden_cross']
                    st.write(
                        f"Golden Cross: "
                        f"{'✅' if gc else '❌'}"
                    )
                    vwap_a = r['vwap']['price_above_vwap']
                    st.write(
                        f"VWAP: ${r['vwap']['value']:.2f} "
                        f"({'Above ✅' if vwap_a else 'Below ❌'})"
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
                    st.write(
                        f"Volume: "
                        f"{r['volume']['volume_ratio']:.1f}x avg"
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

# ══════════════════════════════════════════════
# PAGE 5: AGENT ACTIVITY
# ══════════════════════════════════════════════
elif page == "📈 Agent Activity":
    st.title("📈 Live Agent Activity Feed")
    st.markdown(
        "*Real-time feed of all AI agent actions*"
    )
    st.divider()

    port_filter = st.selectbox(
        "Filter",
        ["ALL", "SNIPER", "FORTRESS"]
    )

    activities = [
        {
            "time": "09:47",
            "agent": "🐋 Whale Hunter",
            "action": (
                "Detected $2.1M dark pool buy on "
                "NVDA at $126.50"
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:52",
            "agent": "📊 Technical Agent",
            "action": (
                "NVDA momentum signal. RSI 58, "
                "MACD bullish crossover"
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "09:58",
            "agent": "📰 Sentiment Agent",
            "action": (
                "Positive NVDA AI chip news. "
                "Sentiment: 0.82"
            ),
            "level": "MEDIUM",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🧠 Orchestrator",
            "action": (
                "NVDA package ready. "
                "3/3 agents agree. Confidence: 87%"
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:02",
            "agent": "🛡️ Risk Warden",
            "action": (
                "NVDA passed all 7 safety checks. "
                "R:R = 2.0:1"
            ),
            "level": "LOW",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:03",
            "agent": "⏳ Human Gate",
            "action": (
                "NVDA BUY sent to your approval queue"
            ),
            "level": "HIGH",
            "portfolio": "SNIPER"
        },
        {
            "time": "10:15",
            "agent": "📊 Fundamental Agent",
            "action": (
                "MSFT earnings growth confirmed. "
                "Long term buy identified"
            ),
            "level": "MEDIUM",
            "portfolio": "FORTRESS"
        },
        {
            "time": "10:22",
            "agent": "🧠 Prediction Engine",
            "action": (
                "New: MSFT → $440 in 14 days. "
                "Confidence: 79%"
            ),
            "level": "HIGH",
            "portfolio": "FORTRESS"
        },
    ]

    icons = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

    filtered = [
        a for a in activities
        if port_filter == "ALL"
        or a['portfolio'] == port_filter
    ]

    for act in filtered:
        c1, c2, c3, c4 = st.columns([1, 2, 5, 1])
        with c1:
            st.markdown(f"**{act['time']}**")
        with c2:
            st.markdown(act['agent'])
        with c3:
            st.markdown(
                f"{icons.get(act['level'], '⚪')} "
                f"{act['action']}"
            )
        with c4:
            badge = (
                "⚡ S" if act['portfolio'] == 'SNIPER'
                else "🏰 F"
            )
            st.caption(badge)
        st.divider()

# Footer
st.markdown("---")
st.caption(
    "🧠 Alpha Mind | AI Portfolio Intelligence | "
    "Paper Trading Mode | "
    f"© {datetime.now().year}"
)