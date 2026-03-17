import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "execution" / "portfolio.db"

# Create persistence directories if not exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DB_PATH.parent, exist_ok=True)

# Portfolio & Risk Management Rules
INITIAL_CAPITAL = 500000.0  # INR
MAX_RISK_PER_TRADE_PCT = 0.02  # 2%
MAX_PORTFOLIO_EXPOSURE_PCT = 0.20  # 20%
MAX_FUTURES_EXPOSURE_PCT = 0.30  # 30%
MAX_OPTIONS_PREMIUM_RISK_PCT = 0.10  # 10%
DAILY_LOSS_LIMIT_PCT = 0.05  # 5%
MAX_DRAWDOWN_PCT = 0.10  # 10%

# Trading Window Settings
MARKET_OPEN_TIME = "09:15:00"
MARKET_CLOSE_TIME = "15:30:00"
SQUARE_OFF_TIME = "15:20:00"

# Target Metrics
TARGET_WIN_RATE = 0.60
TARGET_PROFIT_FACTOR = 1.5
