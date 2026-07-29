# config/risk_parameters.py
# HARD LIMITS. NO AI CAN CHANGE THESE.

RISK_RULES = {
    # Position Sizing
    "max_position_pct": 0.05,
    "max_daily_loss_pct": 0.02,
    "max_drawdown_pct": 0.10,

    # Trade Quality Filters
    "min_risk_reward_ratio": 2.0,
    "min_confidence_score": 0.65,
    "max_open_positions": 5,

    # Time Windows
    "allowed_trade_hours": {
        "start": "09:35",
        "end": "15:55"
    },

    # Never trade these
    "blacklisted_tickers": ["AMC", "GME", "BBBY"],
}