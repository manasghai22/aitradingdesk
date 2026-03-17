import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from execution.portfolio import PortfolioLedger
from execution.risk_manager import RiskManager
from execution.paper_broker import PaperBroker
from data.market_data import MarketDataFetcher
from data.options_data import OptionsDataFetcher
from data.sentiment import NewsSentimentFetcher
from strategies.indicators import TechnicalAnalyzer
from strategies.signal_generator import SignalGenerator
from engine.scheduler import is_market_open, is_square_off_time

class TradingDesk:
    def __init__(self):
        self.ledger = PortfolioLedger()
        self.risk_manager = RiskManager(self.ledger)
        self.broker = PaperBroker(self.ledger, self.risk_manager)
        
        self.market_data = MarketDataFetcher()
        self.options_data = OptionsDataFetcher()
        self.sentiment = NewsSentimentFetcher()
        self.signal_gen = SignalGenerator()
        
        # Focus universe: liquid NIFTY 50 setups
        self.universe = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "LT", "ITC"]
        
    def run_iteration(self):
        print("\n--- Running Market Scan Iteration ---")
        
        # 1. Broad Market Context
        nifty_history = self.market_data.get_historical_data("^NSEI", period="1mo", interval="1d")
        index_trend = "BULLISH"
        
        if not nifty_history.empty:
            sma_20 = nifty_history['Close'].rolling(20).mean().iloc[-1]
            if nifty_history['Close'].iloc[-1] < sma_20:
                index_trend = "BEARISH"
            
        live_prices = {}
        
        # 2. Iterate Universe
        for ticker in self.universe:
            # Fetch latest data state
            current_state = self.market_data.get_latest_data(ticker)
            if not current_state:
                continue
                
            current_price = current_state['ltp']
            live_prices[ticker] = current_price
            
            # 3. Fetch Historical for Indicators
            hist_df = self.market_data.get_historical_data(ticker, period="3mo", interval="1d")
            if hist_df.empty:
                continue
                
            analyzer = TechnicalAnalyzer(hist_df)
            df_tech = analyzer.add_all_indicators()
            
            # 4. Synthesize external context smoothly
            opt_data = self.options_data.get_option_chain(ticker)
            news_data = self.sentiment.fetch_sentiment(ticker)
            
            # 5. Generate Signals
            signal = self.signal_gen.generate_signal(
                ticker=ticker,
                df=df_tech,
                current_price=current_price,
                sentiment_data=news_data,
                options_data=opt_data,
                index_trend=index_trend
            )
            
            # 6. Execute Valid Setup
            if signal:
                self.broker.execute_signal(signal)
                
        # 7. Manage Existing Open Trades
        self.broker.manage_open_positions(live_prices)
        
    def close_all_positions(self):
        open_trades = self.ledger.get_open_trades()
        for _, trade in open_trades.iterrows():
            ticker = trade['ticker']
            trade_id = trade['trade_id']
            latest = self.market_data.get_latest_data(ticker)
            if latest:
                self.ledger.close_trade(trade_id, latest['ltp'])
                print(f"[SQUARE OFF] Closed {ticker} @ {latest['ltp']}")

    def start(self):
        print("AI Trading Desk Started.")
        while True:
            # Uncomment for strictly Live NSE hours (Paper trading usually tests 24/7 or whenever run)
            # if not is_market_open():
            #     print("Market is Closed. Waiting...")
            #     time.sleep(60)
            #     continue
                
            # if is_square_off_time():
            #     print("Square off time reached! Closing all intraday positions.")
            #     self.close_all_positions()
            #     time.sleep(60)
            #     continue
            
            try:
                self.run_iteration()
                time.sleep(300) # Scan every 5 minutes in reality
            except KeyboardInterrupt:
                print("\nDesk stopped by user.")
                break
            except Exception as e:
                print(f"Error in engine loop: {e}")
                time.sleep(30)
                
if __name__ == "__main__":
    desk = TradingDesk()
    desk.start()
