import requests
import random
import time

class OptionsDataFetcher:
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.api_url = "https://www.nseindia.com/api/option-chain-equities?symbol="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def _fetch_cookies(self):
        try:
            self.session.get(self.base_url, timeout=5)
        except Exception:
            pass

    def get_option_chain(self, ticker: str) -> dict:
        """
        Fetches Option Chain for a specific NSE ticker.
        Calculates Put Call Ratio (PCR) to determine market sentiment.
        """
        self._fetch_cookies()
        url = f"{self.api_url}{ticker}"
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return self._parse_options_data(data)
        except Exception:
            # Fallback to mock data if NSE blocks the API request (common issue for scraping)
            return self._mock_options_data()
            
        return self._mock_options_data()

    def _parse_options_data(self, data: dict) -> dict:
        records = data.get("records", {})
        data_list = records.get("data", [])
        
        total_ce_oi = 0
        total_pe_oi = 0
        
        for item in data_list:
            if "CE" in item:
                total_ce_oi += item["CE"].get("openInterest", 0)
            if "PE" in item:
                total_pe_oi += item["PE"].get("openInterest", 0)
                
        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1.0
        
        sentiment = "NEUTRAL"
        if pcr > 1.0:
            sentiment = "BULLISH"
        elif pcr < 0.7:
            sentiment = "BEARISH"
            
        return {
            "pcr": round(pcr, 2),
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "sentiment": sentiment,
            "mocked": False
        }
        
    def _mock_options_data(self) -> dict:
        """Fallback mock options logic for paper trading."""
        # Realistic PCR range
        pcr = round(random.uniform(0.6, 1.4), 2)
        total_ce_oi = random.randint(100000, 500000)
        total_pe_oi = int(total_ce_oi * pcr)
        
        sentiment = "NEUTRAL"
        if pcr > 1.0:
            sentiment = "BULLISH"
        elif pcr < 0.7:
            sentiment = "BEARISH"
            
        return {
            "pcr": pcr,
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "sentiment": sentiment,
            "mocked": True
        }
