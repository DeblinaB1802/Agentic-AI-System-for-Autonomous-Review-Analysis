# memory_manager.py
from collections import defaultdict, Counter
from datetime import datetime

class ProductMemory:
    def __init__(self, product_name: str):
        self.product_name = product_name
        self.stats = Counter()
        self.usps = Counter()
        self.issues = Counter()
        self.usp_justification = []
        self.issue_justification = []
        self.sentiment_history = []
        self.overall_sentiment = 'unknown'
        self.overall_sentiment_score = 0.0
        self.reviewers = set()
        self.monthly_report = defaultdict(lambda: {
            'sentiment': Counter(),
            'score_sum': 0.0,
            'score_count': 0,
            'average_sentiment_score': 0.0,
            'key_drivers': [],
            'justification': []
        })
        
    def update(self, result, context):
        self.sentiment_history.append({
            "result": result,
            "context": context
        })

        cat = result.get("sentiment_category", "neutral")
        score = result['sentiment_score']
        confidence_score = result.get("mode_confidence", 0.0)
        if confidence_score >= 0.7:
            self.stats[cat] += 1
            if context["verified_purchase"]:
                self.stats[f"verified_{cat}"] += 1

            try:
                month = datetime.strptime(context["review_date"], "%Y-%m-%d").strftime("%Y-%m")
                self.monthly_report[month]['sentiment'][cat] += 1
                self.monthly_sentiment[month]['score_sum'] += score
                self.monthly_sentiment[month]['score_count'] += 1
                
                count = self.monthly_sentiment[month]['score_count']
                total = self.monthly_sentiment[month]['score_sum']
                self.monthly_sentiment[month]['average_sentiment_score'] = total / count

                self.monthly_report[month]['key_drivers'].extend(result['key_drivers'])
                self.monthly_report[month]['justification'].append(result['justification'])

            except Exception as e:
                print(f"Failed to update in monthly report: {str(e)}")
                pass

            if cat == 'positive' and result['emotional_intensity'] > 0.8:
                for usp in result.get("key_drivers", []):
                    self.usps[usp.lower()] += 1
                    self.usp_justification.append(result['justification'])

            if cat == 'negative' and result['emotional_intensity'] > 0.8:
                for issue in result.get("key_drivers", []):
                    self.issues[issue.lower()] += 1
                    self.issue_justification.append(result['justification'])

            self.reviewers.add(context["reviewer_name"])
    def get_sentiment_trend(self):
        if sum(self.stats.values) < 10:
            return "unknown"
        else:
            trend = max(self.stats, key=self.stats.get)
            return trend

    def get_top_usps(self, limit=3):
        return [usp for usp, _ in self.usps.most_common(limit)]

    def get_top_usps(self, limit=3):
        return [usp for usp, _ in self.usps.most_common(limit)]

    def generate_summary(self):
        return {
            "sentiment_breakdown": dict(self.stats),
            "top_usps": self.get_top_usps(),
            "top_usps": self.get_top_usps(),
            "sentiment_trend": self.get_sentiment_trend(),
            "monthly_report": {
                k: dict(v) for k, v in self.monthly_report.items()
            },
            "total_reviews_analyzed": len(self.sentiment_history)
        }

    def get_recent_reviews(self, n=5):
        return self.sentiment_history[-n:]

    def filter_by_sentiment(self, sentiment="negative"):
        return [entry for entry in self.sentiment_history if entry["result"].get("sentiment_category") == sentiment]
