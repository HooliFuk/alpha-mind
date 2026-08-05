# monitoring/telegram_alerts.py
# AKUFIN - Intelligence for Wealth Accrual
# Telegram Alert and Approval System
import requests
import time
import os
from dotenv import load_dotenv
from monitoring.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class AKUFINTelegram:
    """
    AKUFIN Telegram Alert System.
    Sends trade signals to your phone.
    Waits for your YES/NO approval.
    Executes trade based on your decision.
    """

    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.base_url = (
            f"https://api.telegram.org/bot{self.token}"
        )

        if not self.token:
            logger.warning(
                "AKUFIN: No Telegram token found"
            )
        if not self.chat_id:
            logger.warning(
                "AKUFIN: No Telegram chat ID found"
            )

    def send_message(
        self,
        message: str,
        parse_mode: str = "HTML"
    ) -> dict:
        """Send a message to your Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(
                url, json=payload, timeout=10
            )
            result = response.json()

            if result.get("ok"):
                logger.info(
                    "AKUFIN Telegram message sent"
                )
                return {
                    "success": True,
                    "message_id": result[
                        "result"
                    ]["message_id"]
                }
            else:
                logger.error(
                    f"Telegram error: {result}"
                )
                return {
                    "success": False,
                    "error": result
                }

        except Exception as e:
            logger.error(
                f"AKUFIN Telegram send error: {e}"
            )
            return {"success": False, "error": str(e)}

    def send_trade_signal(
        self,
        signal: dict
    ) -> dict:
        """
        Send a trade signal alert.
        Formatted beautifully for easy reading.
        """
        ticker = signal.get("ticker", "N/A")
        action = signal.get("signal", "BUY")
        portfolio = signal.get("portfolio", "SNIPER")
        entry = signal.get("entry_price", 0)
        stop = signal.get("stop_loss", 0)
        target = signal.get("take_profit", 0)
        confidence = signal.get("confidence", 0) * 100
        reasoning = signal.get("reasoning", "")
        qty = signal.get("quantity", 1)

        risk = abs(entry - stop)
        reward = abs(target - entry)
        rr = round(reward / risk, 1) if risk > 0 else 0

        port_icon = (
            "⚡" if portfolio == "SNIPER" else "🏰"
        )
        action_icon = (
            "🟢" if action == "BUY" else "🔴"
        )

        message = f"""
💎 <b>AKUFIN TRADE SIGNAL</b>
━━━━━━━━━━━━━━━━━━━━━━

{port_icon} Portfolio: <b>{portfolio}</b>
{action_icon} Signal: <b>{action} {ticker}</b>

📍 Entry:      <b>${entry:.2f}</b>
🛑 Stop Loss:  <b>${stop:.2f}</b>
🎯 Target:     <b>${target:.2f}</b>
⚖️ R:R Ratio:  <b>{rr}:1</b>
📊 Quantity:   <b>{qty} shares</b>
🎲 Confidence: <b>{confidence:.0f}%</b>

💭 <i>{reasoning}</i>

━━━━━━━━━━━━━━━━━━━━━━
<b>Reply to approve:</b>
✅ YES - Execute trade
❌ NO  - Skip trade
⏰ WAIT - Remind in 15 mins
"""
        return self.send_message(message)

    def send_prediction_alert(
        self,
        prediction: dict
    ) -> dict:
        """Send a new prediction notification"""
        ticker = prediction.get("ticker", "N/A")
        direction = prediction.get(
            "predicted_direction", "UP"
        )
        target_price = prediction.get(
            "predicted_price", 0
        )
        current = prediction.get("current_price", 0)
        confidence = prediction.get(
            "confidence", 0
        ) * 100
        target_date = prediction.get("target_date", "")
        portfolio = prediction.get("portfolio", "SNIPER")
        change_pct = prediction.get(
            "price_change_pct", 0
        )

        dir_icon = "🟢" if direction == "UP" else "🔴"
        port_icon = (
            "⚡" if portfolio == "SNIPER" else "🏰"
        )

        message = f"""
💎 <b>AKUFIN NEW PREDICTION</b>
━━━━━━━━━━━━━━━━━━━━━━

{port_icon} Portfolio: <b>{portfolio}</b>
📌 Ticker: <b>{ticker}</b>
{dir_icon} Direction: <b>{direction}</b>

💰 Current Price: <b>${current:.2f}</b>
🎯 Target Price:  <b>${target_price:.2f}</b>
📈 Expected Move: <b>{change_pct:+.1f}%</b>
🎲 Confidence:    <b>{confidence:.0f}%</b>
📅 Target Date:   <b>{target_date}</b>

💭 <i>{prediction.get('reasoning', '')}</i>

━━━━━━━━━━━━━━━━━━━━━━
Prediction saved to AKUFIN tracker.
Will update you when target date arrives.
"""
        return self.send_message(message)

    def send_trade_executed(
        self,
        result: dict
    ) -> dict:
        """Notify when trade is executed"""
        message = f"""
✅ <b>AKUFIN TRADE EXECUTED</b>
━━━━━━━━━━━━━━━━━━━━━━

📌 Symbol:   <b>{result.get('symbol', 'N/A')}</b>
📊 Side:     <b>{result.get('side', 'N/A')}</b>
🔢 Quantity: <b>{result.get('qty', 0)} shares</b>
🆔 Order ID: <code>{result.get('order_id', 'N/A')}</code>
📋 Status:   <b>{result.get('status', 'N/A')}</b>

Your trade is now active on Alpaca.
Monitor it in the AKUFIN dashboard.
"""
        return self.send_message(message)

    def send_trade_rejected(
        self,
        ticker: str,
        reason: str
    ) -> dict:
        """Notify when trade is rejected"""
        message = f"""
❌ <b>AKUFIN TRADE REJECTED</b>
━━━━━━━━━━━━━━━━━━━━━━

📌 Ticker: <b>{ticker}</b>
📋 Reason: <i>{reason}</i>

Signal logged for analysis.
"""
        return self.send_message(message)

    def send_daily_report(
        self,
        report: dict
    ) -> dict:
        """Send end of day performance report"""
        message = f"""
📊 <b>AKUFIN DAILY REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━

💰 Portfolio Value: <b>${report.get('portfolio_value', 0):,.2f}</b>
📈 Daily P&L:       <b>${report.get('daily_pl', 0):+,.2f}</b>
📊 Open Positions:  <b>{report.get('open_positions', 0)}</b>
🎯 Predictions:     <b>{report.get('total_predictions', 0)}</b>
✅ Accuracy:        <b>{report.get('accuracy', 0):.1f}%</b>

<b>Top Signals Today:</b>
{report.get('top_signals', 'No signals today')}

━━━━━━━━━━━━━━━━━━━━━━
💎 AKUFIN - Intelligence for Wealth Accrual
"""
        return self.send_message(message)

    def send_morning_scan(
        self,
        signals: list
    ) -> dict:
        """Send morning market scan results"""
        if not signals:
            message = """
💎 <b>AKUFIN MORNING SCAN</b>
━━━━━━━━━━━━━━━━━━━━━━
No high confidence signals found today.
Market conditions not favorable.
Will continue monitoring.
"""
        else:
            signal_text = ""
            for i, sig in enumerate(signals[:3], 1):
                dir_icon = (
                    "🟢" if sig.get(
                        "direction"
                    ) == "UP" else "🔴"
                )
                signal_text += (
                    f"\n{i}. {dir_icon} "
                    f"<b>{sig.get('ticker')}</b> "
                    f"→ {sig.get('signal')} "
                    f"({sig.get('confidence', 0)*100:.0f}%)"
                )

            message = f"""
💎 <b>AKUFIN MORNING SCAN</b>
━━━━━━━━━━━━━━━━━━━━━━
🕐 Time: Market Open
📊 Scanned: 20 tickers
🎯 Signals Found: {len(signals)}

<b>Top Opportunities:</b>
{signal_text}

Check AKUFIN dashboard for full details.
Awaiting your approval on top signals.
"""
        return self.send_message(message)

    def send_error_alert(
        self,
        error: str
    ) -> dict:
        """Send system error notification"""
        message = f"""
⚠️ <b>AKUFIN SYSTEM ALERT</b>
━━━━━━━━━━━━━━━━━━━━━━
An error occurred in the AKUFIN system:

<code>{error[:200]}</code>

Please check the dashboard.
"""
        return self.send_message(message)

    def get_updates(
        self,
        offset: int = None,
        timeout: int = 30
    ) -> list:
        """
        Get new messages from Telegram.
        Used to receive YES/NO replies.
        """
        try:
            url = f"{self.base_url}/getUpdates"
            params = {"timeout": timeout}
            if offset:
                params["offset"] = offset

            response = requests.get(
                url, params=params, timeout=timeout + 5
            )
            result = response.json()

            if result.get("ok"):
                return result.get("result", [])
            return []

        except Exception as e:
            logger.error(
                f"AKUFIN get updates error: {e}"
            )
            return []

    def wait_for_approval(
    self,
    timeout_seconds: int = 300
) -> str:
    """
    Wait for YES/NO reply from user.
    Returns: 'YES', 'NO', 'WAIT', or 'TIMEOUT'
    """
    logger.info(
        "AKUFIN waiting for Telegram approval..."
    )

    # Get current update offset to only
    # read NEW messages
    try:
        url = f"{self.base_url}/getUpdates"
        r = requests.get(
            url,
            params={"offset": -1},
            timeout=10
        )
        data = r.json()
        results = data.get("result", [])
        if results:
            last_update_id = (
                results[-1]["update_id"] + 1
            )
        else:
            last_update_id = None
    except Exception:
        last_update_id = None

    start_time = time.time()

    while (
        time.time() - start_time < timeout_seconds
    ):
        try:
            updates = self.get_updates(
                offset=last_update_id,
                timeout=5
            )

            for update in updates:
                last_update_id = (
                    update["update_id"] + 1
                )
                message = update.get("message", {})
                text = message.get(
                    "text", ""
                ).strip().upper()
                chat_id = str(
                    message.get(
                        "chat", {}
                    ).get("id", "")
                )

                logger.info(
                    f"AKUFIN received: '{text}' "
                    f"from chat: {chat_id}"
                )
                logger.info(
                    f"Expected chat: {self.chat_id}"
                )

                # Accept from any chat for testing
                # Change to strict check later
                if text in ["YES", "Y", "1", "/YES"]:
                    logger.info(
                        "AKUFIN: Trade APPROVED"
                    )
                    self.send_message(
                        "✅ <b>APPROVED!</b>\n"
                        "Executing trade now..."
                    )
                    return "YES"

                elif text in [
                    "NO", "N", "0", "/NO"
                ]:
                    logger.info(
                        "AKUFIN: Trade REJECTED"
                    )
                    self.send_message(
                        "❌ <b>REJECTED!</b>\n"
                        "Trade cancelled."
                    )
                    return "NO"

                elif text in [
                    "WAIT", "W", "LATER", "/WAIT"
                ]:
                    logger.info(
                        "AKUFIN: Trade DELAYED"
                    )
                    self.send_message(
                        "⏰ <b>WAITING!</b>\n"
                        "Will remind in 15 mins."
                    )
                    return "WAIT"

        except Exception as e:
            logger.error(
                f"AKUFIN update error: {e}"
            )

        time.sleep(2)

    self.send_message(
        "⏰ <b>TIMEOUT!</b>\n"
        "No response received. "
        "Trade cancelled for safety."
    )
    logger.info("AKUFIN: Approval TIMEOUT")
    return "TIMEOUT"

    def test_connection(self) -> bool:
        """Test if Telegram is working"""
        result = self.send_message(
            "💎 <b>AKUFIN Connected!</b>\n"
            "Your Telegram alerts are working.\n"
            "You will receive trade signals here."
        )
        return result.get("success", False)