import sqlite3
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Fix path to allow absolute imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

class PortfolioLedger:
    def __init__(self, target_db_path=config.DB_PATH):
        self.db_path = target_db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            instrument_type TEXT,
            direction TEXT,
            entry_price REAL,
            stop_loss REAL,
            target_price REAL,
            position_size INTEGER,
            risk_pct REAL,
            confidence_score INTEGER,
            expected_return REAL,
            entry_time TEXT,
            exit_price REAL,
            exit_time TEXT,
            pnl REAL,
            status TEXT,
            reasoning TEXT
        )
        ''')
        
        # Portfolio value history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_history (
            timestamp TEXT PRIMARY KEY,
            total_value REAL,
            cash REAL,
            invested REAL
        )
        ''')
        
        # Check if we need to initialize base capital
        cursor.execute('SELECT total_value FROM portfolio_history ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        if not row:
            self.log_portfolio_value(config.INITIAL_CAPITAL, config.INITIAL_CAPITAL, 0.0)
            
        conn.commit()
        conn.close()

    def add_trade(self, trade_data: dict) -> int:
        trade_data['entry_time'] = datetime.now().isoformat()
        trade_data['status'] = 'OPEN'
        trade_data['exit_price'] = None
        trade_data['exit_time'] = None
        trade_data['pnl'] = 0.0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        columns = ', '.join(trade_data.keys())
        placeholders = ', '.join(['?'] * len(trade_data))
        sql = f'INSERT INTO trades ({columns}) VALUES ({placeholders})'
        
        cursor.execute(sql, tuple(trade_data.values()))
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update invested amount
        entry_price = trade_data.get('entry_price', 0)
        qty = trade_data.get('position_size', 0)
        notional = entry_price * qty
        
        current_val, cash, invested = self.get_latest_portfolio_state()
        new_cash = max(0.0, cash - notional)
        new_invested = invested + notional
        self.log_portfolio_value(current_val, new_cash, new_invested)
        
        return trade_id

    def close_trade(self, trade_id: int, exit_price: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT entry_price, position_size, direction FROM trades WHERE trade_id = ? AND status = "OPEN"', (trade_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        
        entry_price, position_size, direction = row
        
        if direction.upper() == 'LONG':
            pnl = (exit_price - entry_price) * position_size
        else: # SHORT
            pnl = (entry_price - exit_price) * position_size
            
        exit_time = datetime.now().isoformat()
        
        cursor.execute('''
        UPDATE trades
        SET exit_price = ?, exit_time = ?, pnl = ?, status = 'CLOSED'
        WHERE trade_id = ?
        ''', (exit_price, exit_time, pnl, trade_id))
        
        conn.commit()
        conn.close()
        
        # Update portfolio value
        current_val, cash, invested = self.get_latest_portfolio_state()
        notional = entry_price * position_size
        
        new_cash = cash + notional + pnl
        new_invested = max(0.0, invested - notional)
        new_total = new_cash + new_invested
        self.log_portfolio_value(new_total, new_cash, new_invested)

    def get_open_trades(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades WHERE status = 'OPEN'", conn)
        conn.close()
        return df
        
    def get_closed_trades(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades WHERE status = 'CLOSED'", conn)
        conn.close()
        return df

    def log_portfolio_value(self, total_value: float, cash: float, invested: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO portfolio_history (timestamp, total_value, cash, invested)
        VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), total_value, cash, invested))
        conn.commit()
        conn.close()

    def get_latest_portfolio_state(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT total_value, cash, invested FROM portfolio_history ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        if row:
            return row  # (total, cash, invested)
        return config.INITIAL_CAPITAL, config.INITIAL_CAPITAL, 0.0

    def get_performance_metrics(self) -> dict:
        df = self.get_closed_trades()
        if df.empty:
            return {"win_rate": 0.0, "profit_factor": 0.0, "total_pnl": 0.0, "max_drawdown": 0.0}
            
        winning_trades = df[df['pnl'] > 0]
        losing_trades = df[df['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(df) if len(df) > 0 else 0
        
        gross_profit = winning_trades['pnl'].sum()
        gross_loss = abs(losing_trades['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate max drawdown
        conn = sqlite3.connect(self.db_path)
        hist_df = pd.read_sql_query("SELECT * FROM portfolio_history ORDER BY timestamp ASC", conn)
        conn.close()
        
        if not hist_df.empty:
            rolling_max = hist_df['total_value'].cummax()
            drawdown = (hist_df['total_value'] - rolling_max) / rolling_max
            max_drawdown = float(abs(drawdown.min()))
        else:
            max_drawdown = 0.0
            
        return {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_pnl": float(df['pnl'].sum()),
            "max_drawdown": max_drawdown
        }
