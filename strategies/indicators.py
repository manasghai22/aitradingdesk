import pandas as pd
import ta
import numpy as np

class TechnicalAnalyzer:
    def __init__(self, data: pd.DataFrame):
        """
        Expects a pandas DataFrame with ['Open', 'High', 'Low', 'Close', 'Volume']
        from yfinance history data.
        """
        self.df = data.copy()
        
    def add_all_indicators(self):
        """Computes and appends all requested indicators to the DataFrame."""
        if self.df.empty:
            return self.df
            
        self._add_trend_indicators()
        self._add_momentum_indicators()
        self._add_volatility_indicators()
        self._add_volume_indicators()
        
        # Drop rows where indicators cannot be computed (NaNs due to windows like SMA 200)
        # Note: If running live, you might want contiguous history instead of dropping all NaNs.
        # For a clean signal generation, let's keep all and the signal generator will just check if not isnull
        
        return self.df
        
    def _add_trend_indicators(self):
        # SMA
        self.df['SMA_50'] = ta.trend.sma_indicator(self.df['Close'], window=50)
        self.df['SMA_200'] = ta.trend.sma_indicator(self.df['Close'], window=200)
        
        # EMA
        self.df['EMA_20'] = ta.trend.ema_indicator(self.df['Close'], window=20)
        self.df['EMA_50'] = ta.trend.ema_indicator(self.df['Close'], window=50)
        
        # Parabolic SAR
        indicator_psar = ta.trend.PSARIndicator(self.df['High'], self.df['Low'], self.df['Close'])
        self.df['PSAR'] = indicator_psar.psar()

        # ADX and DI+/DI-
        indicator_adx = ta.trend.ADXIndicator(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['ADX'] = indicator_adx.adx()
        self.df['DI_PLUS'] = indicator_adx.adx_pos()
        self.df['DI_MINUS'] = indicator_adx.adx_neg()

    def _add_momentum_indicators(self):
        # RSI
        self.df['RSI_14'] = ta.momentum.rsi(self.df['Close'], window=14)
        
        # MACD
        indicator_macd = ta.trend.MACD(self.df['Close'])
        self.df['MACD'] = indicator_macd.macd()
        self.df['MACD_SIGNAL'] = indicator_macd.macd_signal()
        self.df['MACD_HIST'] = indicator_macd.macd_diff()
        
        # Stochastic Oscillator
        indicator_stoch = ta.momentum.StochasticOscillator(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['STOCH_K'] = indicator_stoch.stoch()
        self.df['STOCH_D'] = indicator_stoch.stoch_signal()

    def _add_volatility_indicators(self):
        # ATR
        indicator_atr = ta.volatility.AverageTrueRange(self.df['High'], self.df['Low'], self.df['Close'], window=14)
        self.df['ATR_14'] = indicator_atr.average_true_range()
        
        # Bollinger Bands
        indicator_bb = ta.volatility.BollingerBands(self.df['Close'], window=20, window_dev=2)
        self.df['BB_HIGH'] = indicator_bb.bollinger_hband()
        self.df['BB_MID'] = indicator_bb.bollinger_mavg()
        self.df['BB_LOW'] = indicator_bb.bollinger_lband()
        self.df['BB_WIDTH'] = indicator_bb.bollinger_wband()  # Used for squeeze
        
        # Donchian Channel
        indicator_dc = ta.volatility.DonchianChannel(self.df['High'], self.df['Low'], self.df['Close'], window=20)
        self.df['DONCHIAN_HIGH'] = indicator_dc.donchian_channel_hband()
        self.df['DONCHIAN_LOW'] = indicator_dc.donchian_channel_lband()

    def _add_volume_indicators(self):
        # OBV (On Balance Volume)
        self.df['OBV'] = ta.volume.on_balance_volume(self.df['Close'], self.df['Volume'])
        
        # Volume Spikes
        self.df['VOL_SMA_20'] = self.df['Volume'].rolling(window=20).mean()
        self.df['VOL_SPIKE'] = self.df['Volume'] > (2 * self.df['VOL_SMA_20'])
