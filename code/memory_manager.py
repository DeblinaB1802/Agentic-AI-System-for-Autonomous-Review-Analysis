# memory_manager.py
from collections import defaultdict, Counter
from datetime import datetime

class ProductMemory:
    def __init__(self):
        self.stats = Counter()
        self.monthly_sentiment = defaultdict(lambda: Counter())
        self.issues = Counter()
        self.usps = Counter()
        self.reviewers_seen = set()
        self.duplicates = set()
        self.review_text_hashes = set()
        self.sentiment_history = []

    def update(self, result, context):
        self.sentiment_history.append({
            "result": result,
            "context": context
        })

        cat = result.get("sentiment_category", "neutral")
        self.stats[cat] += 1
        if context["verified_purchase"]:
            self.stats[f"verified_{cat}"] += 1

        try:
            month = datetime.strptime(context["review_date"], "%Y-%m-%d").strftime("%Y-%m")
            self.monthly_sentiment[month][cat] += 1
        except:
            pass

        for issue in result.get("key_issues", []):
            self.issues[issue.lower()] += 1

        for usp in result.get("usp_features", []):
            self.usps[usp.lower()] += 1

        text = result.get("raw_review_text", "").strip().lower()
        if text:
            self.review_text_hashes.add(hash(text))
            self.reviewers_seen.add(context["reviewer_name"])

    def get_sentiment_trend(self):
        if sum(self.stats.values) < 10:
            return "unknown"
        elif self.stats["negative"] > self.stats["positive"]:
            return "mostly negative"
        elif self.stats["positive"] > self.stats["negative"]:
            return "mostly positive"
        elif self.stats["positive"] == self.stats["negative"]:
            return "mixed"

    def get_top_issues(self, limit=3):
        return [issue for issue, _ in self.issues.most_common(limit)]

    def get_top_usps(self, limit=3):
        return [usp for usp, _ in self.usps.most_common(limit)]

    def generate_summary(self):
        return {
            "sentiment_breakdown": dict(self.stats),
            "top_issues": self.get_top_issues(),
            "top_usps": self.get_top_usps(),
            "sentiment_trend": self.get_sentiment_trend(),
            "monthly_sentiment": {
                k: dict(v) for k, v in self.monthly_sentiment.items()
            },
            "total_reviews_analyzed": len(self.sentiment_history)
        }

    def get_recent_reviews(self, n=5):
        return self.sentiment_history[-n:]

    def filter_by_sentiment(self, sentiment="negative"):
        return [entry for entry in self.sentiment_history if entry["result"].get("sentiment_category") == sentiment]
