import urllib.parse
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup

class NewsSentimentFetcher:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def fetch_sentiment(self, query: str) -> dict:
        """
        Fetches recent news for the query and returns an aggregated sentiment.
        Returns: { 'sentiment': str, 'score': float, 'articles_analyzed': int }
        """
        encoded_query = urllib.parse.quote(f"{query} stock NSE")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        feed = feedparser.parse(url)
        
        if not feed.entries:
            return {"sentiment": "NEUTRAL", "score": 0.0, "articles_analyzed": 0}
            
        total_score = 0.0
        count = min(10, len(feed.entries))
        
        for entry in feed.entries[:count]:
            # Clean HTML from title if any
            title = BeautifulSoup(entry.title, "html.parser").get_text()
            # Analyze sentiment (compound score between -1 and 1)
            score = self.analyzer.polarity_scores(title)['compound']
            total_score += score
            
        avg_score = total_score / count
        
        # Classification thresholds based on VADER
        if avg_score >= 0.15:
            sentiment = "BULLISH"
        elif avg_score <= -0.15:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
            
        return {
            "sentiment": sentiment,
            "score": round(avg_score, 3),
            "articles_analyzed": count
        }
