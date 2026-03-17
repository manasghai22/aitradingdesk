import pandas as pd
from typing import Dict, Optional

class SignalGenerator:
    def __init__(self):
        pass

    def generate_signal(self, ticker: str, df: pd.DataFrame, current_price: float, 
                        sentiment_data: dict, options_data: dict, index_trend: str) -> Optional[Dict]:
        """
        Evaluates technicals, sentiment, and options logic to generate trade setups.
        Returns a dict with trade details if a signal is found, else None.
        """
        if df.empty or len(df) < 50:
            return None
            
        latest = df.iloc[-1]
        
        # Technicals
        rsi = latest.get('RSI_14', 50)
        macd = latest.get('MACD', 0)
        macd_signal = latest.get('MACD_SIGNAL', 0)
        ema_20 = latest.get('EMA_20', 0)
        ema_50 = latest.get('EMA_50', 0)
        vwap = latest.get('vwap', current_price)
        vol_spike = latest.get('VOL_SPIKE', False)
        atr = latest.get('ATR_14', current_price * 0.01)
        
        # Sentiment & Options Context
        news_sentiment = sentiment_data.get('sentiment', 'NEUTRAL')
        options_sentiment = options_data.get('sentiment', 'NEUTRAL')
        
        # 1. Strong Trending Market Setup (Futures logic - LONG)
        if (macd > macd_signal) and (rsi > 60) and (current_price > vwap) and (ema_20 > ema_50) and vol_spike:
            if index_trend != 'BEARISH' and news_sentiment != 'BEARISH' and options_sentiment != 'BEARISH':
                reasoning = (f"MACD bullish crossover | RSI ({rsi:.1f}) > 60 | Price ({current_price:.2f}) > VWAP ({vwap:.2f}) | "
                             f"EMA 20 > EMA 50 | Volume Spike | News: {news_sentiment} | Options: {options_sentiment}")
                
                stop_loss = current_price - (1.5 * atr)
                target = current_price + (3.0 * atr)
                
                return {
                    "ticker": ticker,
                    "instrument_type": "Futures",
                    "direction": "LONG",
                    "entry_price": current_price,
                    "stop_loss": round(stop_loss, 2),
                    "target_price": round(target, 2),
                    "confidence_score": 85,
                    "reasoning": reasoning
                }
                
        # 2. Low Volatility Breakout (Options logic - LONG)
        bb_high = latest.get('BB_HIGH', current_price * 1.05)
        bb_width = latest.get('BB_WIDTH', 100)
        # Check squeeze (current width < 80% of recent average)
        recent_bb_width = df['BB_WIDTH'].iloc[-10:-1].mean() if 'BB_WIDTH' in df.columns else 100
        
        if (current_price > bb_high) and (bb_width < recent_bb_width * 0.8) and (rsi > 55):
            if index_trend != 'BEARISH' and options_sentiment == 'BULLISH':
                reasoning = (f"BB Breakout from Squeeze | Price > BB High ({bb_high:.2f}) | "
                             f"RSI ({rsi:.1f}) > 55 | Options Bullish")
                             
                stop_loss = latest.get('BB_MID', current_price * 0.98)
                target = current_price + (current_price - stop_loss) * 2.5
                
                return {
                    "ticker": ticker,
                    "instrument_type": "Options",
                    "direction": "LONG",
                    "entry_price": current_price,
                    "stop_loss": round(stop_loss, 2),
                    "target_price": round(target, 2),
                    "confidence_score": 75,
                    "reasoning": reasoning
                }
                
        # 3. Pullback to Support / Swing (Equity logic - LONG)
        sma_200 = latest.get('SMA_200', current_price * 0.9)
        if (ema_20 > sma_200) and (current_price > sma_200):
            if rsi < 40 and df['RSI_14'].iloc[-5:].min() < 30:
                if news_sentiment == 'BULLISH':
                    reasoning = (f"Pullback to support | Price > SMA 200 ({sma_200:.2f}) | "
                                 f"RSI bounced from oversold ({rsi:.1f}) | News Bullish")
                                 
                    stop_loss = current_price - (2 * atr)
                    target = current_price + (4 * atr)
                    
                    return {
                        "ticker": ticker,
                        "instrument_type": "Equity",
                        "direction": "LONG",
                        "entry_price": current_price,
                        "stop_loss": round(stop_loss, 2),
                        "target_price": round(target, 2),
                        "confidence_score": 80,
                        "reasoning": reasoning
                    }
                    
        return None
