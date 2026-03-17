import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from execution.portfolio import PortfolioLedger
from execution.risk_manager import RiskManager
import config

class PaperBroker:
    def __init__(self, ledger: PortfolioLedger, risk_manager: RiskManager):
        self.ledger = ledger
        self.risk_manager = risk_manager
        
    def execute_signal(self, signal: dict) -> bool:
        """
        Takes a trade signal, calculates position size, checks risk, and logs trade.
        """
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        direction = signal['direction']
        
        # Calculate Position Size based on Risk Config
        total_value, cash, invested = self.ledger.get_latest_portfolio_state()
        max_risk_amount = total_value * config.MAX_RISK_PER_TRADE_PCT
        
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share <= 0:
            print(f"[{signal['ticker']}] Invalid risk per share: {risk_per_share}")
            return False
            
        proposed_size = int(max_risk_amount / risk_per_share)
        
        # Cap size by max portfolio exposure (e.g. 20%)
        max_exposure_amount = total_value * config.MAX_PORTFOLIO_EXPOSURE_PCT
        max_size_by_exposure = int(max_exposure_amount / entry_price)
        
        # Cap size by available cash
        max_size_by_cash = int(cash / entry_price) if cash > 0 else 0
        
        actual_size = min(proposed_size, max_size_by_exposure, max_size_by_cash)
        
        if actual_size <= 0:
            print(f"[{signal['ticker']}] Calculated position size is 0 (Check cash or risk limits).")
            return False
            
        signal['position_size'] = actual_size
        signal['risk_pct'] = (risk_per_share * actual_size) / total_value
        
        # Check overall validity via RiskManager
        is_valid, reason = self.risk_manager.check_trade_validity(signal, entry_price)
        
        if is_valid:
            trade_id = self.ledger.add_trade(signal)
            print(f"[EXECUTED] {direction} | {signal['ticker']} | Size: {actual_size} | Entry: {entry_price:,.2f}")
            return True
        else:
            print(f"[REJECTED] {signal['ticker']} | Reason: {reason}")
            return False

    def manage_open_positions(self, live_prices: dict):
        """
        Iterates through open trades. Closes them if price hits SL or Target.
        live_prices: { 'RELIANCE.NS': 2500.0, ... }
        """
        open_trades = self.ledger.get_open_trades()
        if open_trades.empty:
            return
            
        for _, trade in open_trades.iterrows():
            trade_id = trade['trade_id']
            ticker = trade['ticker']
            direction = trade['direction']
            stop_loss = trade['stop_loss']
            target = trade['target_price']
            
            # Map Yahoo Finance tickers back if needed
            current_price = live_prices.get(ticker)
            if not current_price:
                continue
                
            close_trade = False
            
            if direction == 'LONG':
                if current_price <= stop_loss or current_price >= target:
                    close_trade = True
            else: # SHORT
                if current_price >= stop_loss or current_price <= target:
                    close_trade = True
                    
            if close_trade:
                self.ledger.close_trade(trade_id, current_price)
                reason = "Target" if current_price >= target else "Stop Loss"
                if direction == 'SHORT':
                    reason = "Target" if current_price <= target else "Stop Loss"
                print(f"[CLOSED] {ticker} ({direction}) | Exit: {current_price:,.2f} | Hit: {reason}")
