import yfinance as yf
print(yf.Ticker('RELIANCE.NS').history(period='1d', interval='5m'))
print(yf.Ticker('^NSEI').history(period='1mo', interval='1d'))
