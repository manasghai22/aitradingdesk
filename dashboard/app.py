import streamlit as st
import pandas as pd
import sqlite3
import sys
from pathlib import Path
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# Auto-refresh interval (10 seconds)
st_autorefresh(interval=10000, key="data_refresh")

# Setup Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

DB_PATH = config.DB_PATH

st.set_page_config(page_title="AI Trading Desk", layout="wide", page_icon="📈")

@st.cache_data(ttl=5)
def load_data():
    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame()
        
    conn = sqlite3.connect(DB_PATH)
    try:
        trades = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_id DESC", conn)
        history = pd.read_sql_query("SELECT * FROM portfolio_history ORDER BY timestamp ASC", conn)
    except Exception:
        trades = pd.DataFrame()
        history = pd.DataFrame()
    finally:
        conn.close()
    return trades, history

st.title("🤖 NSE AI Trading Desk")
st.markdown("Fully Automated Technical & Sentiment based Alpha Generation")

trades_df, history_df = load_data()

# 1. Top Metrics
if not history_df.empty:
    latest_state = history_df.iloc[-1]
    curr_value = latest_state['total_value']
    cash = latest_state['cash']
    invested = latest_state['invested']
    
    pnl = curr_value - config.INITIAL_CAPITAL
    pnl_pct = (pnl / config.INITIAL_CAPITAL) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Portfolio Value", f"₹ {curr_value:,.2f}", f"{pnl_pct:.2f}%")
    col2.metric("Available Cash", f"₹ {cash:,.2f}")
    
    exposure_pct = (invested / config.INITIAL_CAPITAL) * 100
    col3.metric("Capital Deployed", f"₹ {invested:,.2f}", f"{exposure_pct:.1f}% Exposure", delta_color="off")
    
    # Calculate win rate and profit factor
    win_rate = 0.0
    pf = 0.0
    if not trades_df.empty:
        closed = trades_df[trades_df['status'] == 'CLOSED']
        if not closed.empty:
            wins = len(closed[closed['pnl'] > 0])
            win_rate = (wins / len(closed)) * 100
            
            gross_profit = closed[closed['pnl'] > 0]['pnl'].sum()
            gross_loss = abs(closed[closed['pnl'] <= 0]['pnl'].sum())
            pf = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
            
    col4.metric("Win Rate | Profit Factor", f"{win_rate:.1f}%", f"{pf:.2f} PF", delta_color="off")

st.divider()

# 2. Portfolio PnL Chart
if not history_df.empty:
    st.subheader("Equity Curve")
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
    fig = px.line(history_df, x='timestamp', y='total_value', title="Portfolio Growth (INR)")
    fig.update_layout(yaxis_title="Value", xaxis_title="Time")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("System initializing. Waiting for portfolio logic to log first state.")

# 3. Active Trades
st.subheader("🟢 Active Trades")
if not trades_df.empty:
    open_trades = trades_df[trades_df['status'] == 'OPEN'].copy()
    if not open_trades.empty:
        st.dataframe(open_trades[['trade_id', 'ticker', 'direction', 'entry_price', 'target_price', 'stop_loss', 'position_size', 'reasoning']], use_container_width=True, hide_index=True)
    else:
        st.info("No active trades currently open.")
else:
    st.info("No trades records found.")

# 4. Closed Trades Log
st.subheader("🔴 Trade Ledger")
if not trades_df.empty:
    closed_trades = trades_df[trades_df['status'] == 'CLOSED'].copy()
    if not closed_trades.empty:
        # Style PnL natively by letting pandas highlight or just display it
        st.dataframe(closed_trades[['trade_id', 'ticker', 'direction', 'entry_price', 'exit_price', 'pnl', 'reasoning']], use_container_width=True, hide_index=True)
    else:
        st.info("No trades closed yet.")
