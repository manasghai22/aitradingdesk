import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from execution.portfolio import PortfolioLedger

class RiskManager:
    def __init__(self, ledger: PortfolioLedger):
        self.ledger = ledger

    def check_trade_validity(self, trade_data: dict, current_price: float) -> tuple[bool, str]:
        """
        Validates if a proposed trade meets all risk requirements.
        Returns (is_valid, reason)
        """
        total_value, cash, invested = self.ledger.get_latest_portfolio_state()
        
        # Check Max Drawdown
        metrics = self.ledger.get_performance_metrics()
        
        if metrics.get("max_drawdown", 0) > config.MAX_DRAWDOWN_PCT:
            return False, f"Max drawdown limit reached: {metrics['max_drawdown']:.2%}"
            
        position_size = trade_data.get('position_size', 0)
        proposed_notional = position_size * current_price
        
        # Check maximum portfolio exposure (20%)
        current_exposure = invested + proposed_notional
        max_allowed_exposure = total_value * config.MAX_PORTFOLIO_EXPOSURE_PCT
        if current_exposure > max_allowed_exposure:
            return False, f"Portfolio exposure limits exceeded. Required exposure: {current_exposure:,.2f}, Allowed: {max_allowed_exposure:,.2f}"

        # Check max risk per trade (2%)
        stop_loss = trade_data.get('stop_loss', 0)
        direction = trade_data.get('direction', 'LONG').upper()
        
        if position_size <= 0:
            return False, "Position size must be greater than 0"
            
        if direction == 'LONG':
            if stop_loss >= current_price:
                return False, "Stop loss must be below current price for LONG trades"
            risk_amount = (current_price - stop_loss) * position_size
        else:
            if stop_loss <= current_price:
                return False, "Stop loss must be above current price for SHORT trades"
            risk_amount = (stop_loss - current_price) * position_size
            
        max_allowed_risk = total_value * config.MAX_RISK_PER_TRADE_PCT
        
        if risk_amount > max_allowed_risk:
            return False, f"Trade risk ({risk_amount:,.2f}) exceeds max allowed per trade ({max_allowed_risk:,.2f})"
            
        # Ensure we have enough cash for margin
        if proposed_notional > cash:
            return False, f"Insufficient cash for trade. Required: {proposed_notional:,.2f}, Available: {cash:,.2f}"
            
        return True, "Trade within risk parameters"
