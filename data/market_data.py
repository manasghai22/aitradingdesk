import yfinance as yf
import pandas as pd
from typing import Optional
import time

def format_nse_ticker(ticker: str) -> str:
    """Appends .NS to NSE tickers for Yahoo Finance if not present."""
    if not ticker.endswith('.NS') and not ticker.startswith('^'):
        return f"{ticker}.NS"
    return ticker

class MarketDataFetcher:
    def get_latest_data(self, ticker: str) -> dict:
        symbol = format_nse_ticker(ticker)
        ticker_obj = yf.Ticker(symbol)
        
        # Fast fetch for intraday status
        time.sleep(0.5)
        hist = ticker_obj.history(period='1d', interval='5m')
        if hist.empty:
            return {}
            
        latest = hist.iloc[-1]
        
        # Calculate approximate daily VWAP based on intraday segments
        vwap = self._calculate_vwap(hist)
        
        return {
            "ticker": ticker,
            "ltp": float(latest['Close']),
            "volume": int(latest['Volume']),
            "vwap": float(vwap),
            "high": float(hist['High'].max()),
            "low": float(hist['Low'].min()),
            "open": float(hist['Open'].iloc[0])
        }
        
    def _calculate_vwap(self, df: pd.DataFrame) -> float:
        """Calculate Volume Weighted Average Price."""
        if df.empty or df['Volume'].sum() == 0:
            return df['Close'].iloc[-1] if not df.empty else 0.0
            
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        vwap = (typical_price * df['Volume']).sum() / df['Volume'].sum()
        return float(vwap)

    def get_historical_data(self, ticker: str, period: str = '3mo', interval: str = '1d') -> pd.DataFrame:
        """Fetches historical OHLCV data."""
        time.sleep(0.5)
        symbol = format_nse_ticker(ticker)
        ticker_obj = yf.Ticker(symbol)
        df = ticker_obj.history(period=period, interval=interval)
        if not df.empty and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
