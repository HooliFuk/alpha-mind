# config/risk_parameters.py
# AKUFIN - Intelligence for Wealth Accrual
# Risk Parameters for ALL Three Sessions

RISK_RULES = {
    # Position Sizing
    "max_position_pct": 0.05,
    "max_daily_loss_pct": 0.02,
    "max_drawdown_pct": 0.10,

    # Trade Quality
    "min_risk_reward_ratio": 2.0,
    "min_confidence_score": 0.65,
    "max_open_positions": 5,

    # Session Based Trading Windows
    "allowed_sessions": {
        "SNIPER": [
            "MORNING_SESSION",
            "AFTERNOON_SESSION"
        ],
        "FORTRESS": [
            "MORNING_SESSION",
            "LUNCH_LULL",
            "AFTERNOON_SESSION",
            "AFTER_HOURS"
        ],
        "PRE_MARKET_SCAN": [
            "PRE_MARKET"
        ],
        "EARNINGS": [
            "AFTER_HOURS"
        ]
    },

    # Safe execution window
    "safe_trade_hours": {
        "start": "09:35",
        "end": "15:55"
    },

    # Extended hours (higher risk)
    "extended_hours": {
        "pre_market_start": "04:00",
        "pre_market_end": "09:30",
        "after_hours_start": "16:00",
        "after_hours_end": "20:00"
    },

    # Never trade these
    "blacklisted_tickers": [
        "AMC", "GME", "BBBY"
    ],

    # Session risk multipliers
    "session_risk_multiplier": {
        "PRE_MARKET": 0.5,
        "MORNING_SESSION": 1.0,
        "LUNCH_LULL": 0.5,
        "AFTERNOON_SESSION": 1.0,
        "AFTER_HOURS": 0.5,
        "OPENING_BELL": 0.0
    }
}