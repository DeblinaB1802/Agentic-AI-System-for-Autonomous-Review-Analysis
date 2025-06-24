# memory_manager.py
from collections import defaultdict, Counter
from datetime import datetime

class ProductMemory:
    """
    Tracks and analyzes customer sentiment, USPs, and issues for a product over time.
    Stores sentiment history, monthly trends, and key insights for summary reporting.
    """
    def __init__(self, product_name: str):
        """Initializes memory for a specific product, setting up tracking structures."""
        self.product_name = product_name
        self.stats = Counter()
        self.usps = Counter()
        self.issues = Counter()
        self.usp_justification = set()
        self.issue_justification = set()
        self.reviewers = set()
        self.sentiment_history = []
        self.overall_sentiment = 'unknown'
        self.overall_sentiment_score = 0.0

        def default_monthly_report():
            """Returns a default dictionary structure for monthly sentiment reports."""
            return {
                'sentiment': Counter(),
                'score_sum': 0.0,
                'score_count': 0,
                'average_sentiment_score': 0.0,
                'key_drivers': [],
                'justification': []
            }
    
        self.monthly_report = defaultdict(default_monthly_report)
        
    def update(self, result: dict, context: dict) -> None:
        """Updates memory with a new review result and its associated context."""
        self.sentiment_history.append({
            "result": result,
            "context": context
        })
        if len(self.sentiment_history) > 1000:
            self.sentiment_history.pop(0)

        cat = result.get("sentiment_category", "neutral")
        score = result['sentiment_score']
        confidence_score = result.get("model_confidence", 0.0)
        if confidence_score >= 0.7:
            self.stats[cat] += 1
            if context["verified_purchase"]:
                self.stats[f"verified_{cat}"] += 1

            try:
                month = datetime.strptime(context["review_date"], "%d-%m-%Y").strftime("%m-%Y")
                self.monthly_report[month]['sentiment'][cat] += 1
                self.monthly_report[month]['score_sum'] += score
                self.monthly_report[month]['score_count'] += 1
                
                count = self.monthly_report[month]['score_count']
                total = self.monthly_report[month]['score_sum']
                self.monthly_report[month]['average_sentiment_score'] = total / count

                self.monthly_report[month]['key_drivers'].extend(result['key_drivers'])
                self.monthly_report[month]['justification'].append(result['justification'])

            except Exception as e:
                print(f"Failed to update in monthly report: {str(e)}")
                pass

            if cat == 'positive' and result['emotional_intensity'] > 0.7:
                for usp in result.get("key_drivers", []):
                    self.usps[usp.lower()] += 1
                    self.usp_justification.add(result.get('justification', 'No justification provided'))

            if cat == 'negative' and result['emotional_intensity'] > 0.7:
                for issue in result.get("key_drivers", []):
                    self.issues[issue.lower()] += 1
                    self.issue_justification.add(result.get('justification', 'No justification provided'))

            self.reviewers.add(context["reviewer_name"])

    def get_sentiment_trend(self) -> str:
        """Returns the dominant sentiment trend (positive/negative/neutral) or 'unknown'."""
        if sum(self.stats.values()) < 10:
            return "unknown"
        else:
            trend = max(self.stats, key=self.stats.get)
            return trend

    def get_top_usps(self, limit: int = 3) -> list[str]:
        """Returns the top N unique selling points (USPs) based on frequency."""
        return [usp for usp, _ in self.usps.most_common(limit)]

    def get_top_issues(self, limit: int = 3) -> list[str]:
        """Returns the top N issues mentioned in reviews based on frequency."""
        return [issue for issue, _ in self.issues.most_common(limit)]

    def generate_summary(self) -> dict:
        """Generates a summary of review sentiment, trends, top USPs/issues, and monthly insights."""
        total_reviews = len(self.sentiment_history)
        total_reviews = len(self.sentiment_history)
        top_usps = self.get_top_usps()
        top_issues = self.get_top_issues()
        sentiment_trend = self.get_sentiment_trend()

        monthly_summary = {}
        for month, report in self.monthly_report.items():
            monthly_summary[month] = {
                "sentiment_breakdown": dict(report["sentiment"]),
                "average_sentiment_score": round(report["average_sentiment_score"], 3),
                "key_drivers": list(set(report["key_drivers"])),
                "justifications": report["justification"]
            }

        return {
            "product_name": self.product_name,
            "overall_sentiment_trend": sentiment_trend,
            "total_reviews_analyzed": total_reviews,
            "sentiment_distribution": dict(self.stats),
            "top_usps": top_usps,
            "top_issues": top_issues,
            "unique_reviewers_count": len(self.reviewers),
            "monthly_analysis": monthly_summary
        }

    def get_recent_reviews(self, n: int = 5) -> list[dict]:
        """Returns the most recent N sentiment-analyzed reviews."""
        return self.sentiment_history[-n:]

    def filter_by_sentiment(self, sentiment: str = "negative") -> list[dict]:
        """Returns all reviews matching a specific sentiment category."""
        return [entry for entry in self.sentiment_history if entry["result"].get("sentiment_category") == sentiment]
