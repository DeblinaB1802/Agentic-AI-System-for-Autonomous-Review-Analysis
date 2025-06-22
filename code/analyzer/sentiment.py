from typing import Dict
import re
import json
from Utils.helpers import calculate_days_passed
from Core.model_runner import run_llm_model

class SentimentAnalyzerAgent:
    def __init__(self, model: str = "gpt-3.5-turbo"):
         """Initialize the sentiment analyzer with a specified LLM model."""
        self.model = model

    @staticmethod
    def build_adaptive_prompt(review: str, context: Dict) :
         """Constructs a detailed sentiment analysis prompt using review text and context for the LLM."""
        quality_score = context.get('quality_score', 'unknown')
        verified = context.get('verified_purchase', False)
        rating = context.get('rating', 'unknown')
        review_length = context.get('review_length', 'unknown')
        helpfulness_ratio = context.get('helpfulness_ratio', 0.0)
        sentiment_trend = context.get('sentiment_trend', 'unknown')
        recent_issues = ', '.join(context.get('recent_issues', []))
        top_usps = ', '.join(context.get('top_usps', []))
        persona_mode = context.get('persona_mode', 'balanced')
        base_confidence = context.get('base_confidence', 0.7)
        review_date = context.get('review_date', 'unknown')
        reviewer_name = context.get('reviewer_name', 'unknown')

        if sentiment_trend == 'unknown':
            example = FEW_SHOT_EXAMPLES['default']
        else:
            example = FEW_SHOT_EXAMPLES[sentiment_trend]
        
        FEW_SHOT_EXAMPLES = {
            "positive": """
        Example: Strong Positive Review
        Review: "Absolutely love the display and battery life! Feels like a flagship phone. Will recommend it to friends."
        Context: Verified Purchase = True, Helpfulness Ratio = 0.85, Sentiment Trend = Mostly Positive

        Expected Output:
        {
        "sentiment_category": "positive",
        "sentiment_score": 0.91,
        "model_confidence": 0.96,
        "key_drivers": ["display quality", "battery life", "recommendation"],
        "emotional_intensity": 0.85,
        "mixed_signals": false,
        "conflicting_phrases": [],
        "justification": "Reviewer praises display and battery, and expresses willingness to recommend.",
        "trust_tag": "high_trust",
        "persona_adjusted": true
        }
        """,

            "negative": """
        Example: Strong Negative Review
        Review: "Camera is decent, but the phone heats up really badly and lags during games. Regret buying this."
        Context: Verified Purchase = True, Helpfulness Ratio = 0.9, Sentiment Trend = Mostly Negative

        Expected Output:
        {
        "sentiment_category": "negative",
        "sentiment_score": -0.75,
        "model_confidence": 0.89,
        "key_drivers": ["heating issue", "gaming lag", "regret"],
        "emotional_intensity": 0.92,
        "mixed_signals": true,
        "conflicting_phrases": ["camera is decent", "regret buying this"],
        "justification": "Despite a neutral comment on the camera, the strong emotional regret and major issues dominate the sentiment.",
        "trust_tag": "high_trust",
        "persona_adjusted": true
        }
        """,

            "neutral": """
        Example: Neutral Review
        Review: "It’s okay, not bad but nothing special either."
        Context: Verified Purchase = False, Helpfulness Ratio = 0.1, Sentiment Trend = Mostly Neutral

        Expected Output:
        {
        "sentiment_category": "neutral",
        "sentiment_score": 0.05,
        "model_confidence": 0.62,
        "key_drivers": ["average experience", "lack of enthusiasm"],
        "emotional_intensity": 0.2,
        "mixed_signals": false,
        "conflicting_phrases": [],
        "justification": "The reviewer gives a neutral stance with no strong praise or complaint.",
        "trust_tag": "low_trust",
        "persona_adjusted": false
        }
        """,

            "mixed": """
        Example: Mixed Signals Review
        Review: "The phone looks stylish and works fine, but I had to replace it in 2 weeks because of charging issues."
        Context: Verified Purchase = True, Helpfulness Ratio = 0.7, Sentiment Trend = Mixed

        Expected Output:
        {
        "sentiment_category": "negative",
        "sentiment_score": -0.4,
        "model_confidence": 0.75,
        "key_drivers": ["charging issues", "short product lifespan"],
        "emotional_intensity": 0.7,
        "mixed_signals": true,
        "conflicting_phrases": ["looks stylish", "had to replace it"],
        "justification": "Although appearance is praised, the functional issue leads to a negative overall impression.",
        "trust_tag": "medium_trust",
        "persona_adjusted": true
        }
        """,

            "default": """
        Example: General Balanced Review
        Review: "The phone is fast and sleek, but the camera quality is just average. Not sure if it’s worth the price."
        Context: Verified Purchase = True, Helpfulness Ratio = 0.5, Sentiment Trend = Unknown

        Expected Output:
        {
        "sentiment_category": "neutral",
        "sentiment_score": 0.1,
        "model_confidence": 0.68,
        "key_drivers": ["performance", "camera quality", "value concern"],
        "emotional_intensity": 0.5,
        "mixed_signals": true,
        "conflicting_phrases": ["fast and sleek", "just average", "not sure if it’s worth the price"],
        "justification": "Performance is appreciated but concerns about price and camera introduce ambivalence.",
        "trust_tag": "medium_trust",
        "persona_adjusted": true
        }
        """
        }


        prompt = f"""
        You are an advanced adaptive sentiment analysis AI with access to review metadata and product memory.

        Your task is to assess the sentiment of the following customer review, considering not just the text but the full context below.

        ===========================
        Review: {review}
        Review Date: {review_date}
        Reviewer: {reviewer_name}
        ===========================

        Review Metadata:
        - Verified Purchase: {verified}
        - Star Rating: {rating}
        - Review Length: {review_length}
        - Helpfulness Ratio: {helpfulness_ratio:.2f}
        - Quality Score: {quality_score}
        
        If star rating sentiment and review sentiment are mismatched, star rating should be neglected and review should be given weightage.

        Product Memory Context:
        - Sentiment Trend: {sentiment_trend}
        - Recent Top Issues: {recent_issues}
        - Top Praised Features (USPs): {top_usps}

        Persona Mode: {persona_mode}
        Expected Base Confidence Threshold: {base_confidence}

        ---
        Analyze this review carefully, adapting to the trustworthiness of the reviewer based helpfulness ratio and overall product trends. 
        If the review seems contradictory, mixed, or unusually emotional, reflect that in your response.

        Include justification and emotional insight.

        Use the format below for output:

        {{
        "sentiment_category": "positive|negative|neutral|mixed",
        "sentiment_score": float (-1.0 to +1.0),
        "model_confidence": float (0 to 1),
        "key_drivers": ["list", "of", "sentiment", "drivers"],
        "emotional_intensity": float (0 to 1),
        "mixed_signals": true|false,
        "conflicting_phrases": ["list", "if", "any"],
        "justification": "short explanation",
        "trust_tag": "high_trust|low_trust",
        "persona_adjusted": true|false
        }}

        Here are examples to guide your thinking:
        {example}

        Now analyze the input review with all the above context.
        """
        return prompt

    def adaptive_sentiment_analysis(self, review: str, context: Dict):
        """Performs adaptive sentiment analysis by sending a constructed prompt to the LLM and parsing its output."""
        prompt = self.build_adaptive_prompt(review, context)
        response, _ = run_llm_model(self.model, prompt, max_retries=5)
        try:
            cleaned_response = re.findall(r"\{.*?\}", response, flags=re.DOTALL)
            if cleaned_response:
                result = json.loads(cleaned_response[0])
                return result
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Failed to parse through LLM output: {e}")
            return {
            "sentiment_category": "neutral",
            "sentiment_score": 0.0,
            "model_confidence": 0.0,
            "key_drivers": [],
            "emotional_intensity": 0.0,
            "mixed_signals": False,
            "conflicting_phrases": [],
            "justification": "",
            "trust_tag": "",
            "persona_adjusted": False
        }

    def estimate_weightage(self, result):
        """Estimates the confidence-based weightage of a sentiment result using heuristics and model confidence."""
        HEURISTIC_WEIGHTS = {
            "persona_adjusted": 0.1,
            "no_conflict": 0.1,
            "has_key_drivers": 0.1,
            "no_mixed_signals": 0.1
        }
        CONFIDENCE_BIAS_TERM = 0.4
        HIGH_CONFIDENCE_THRESHOLD = 0.7

        score = 0

        if result.get("persona_adjusted", False):
            score += HEURISTIC_WEIGHTS["persona_adjusted"]

        if not result.get("conflicting_phrases"):
            score += HEURISTIC_WEIGHTS["no_conflict"]

        if result.get("key_drivers"):
            score += HEURISTIC_WEIGHTS["has_key_drivers"]

        if not result.get("mixed_signals", False):
            score += HEURISTIC_WEIGHTS["no_mixed_signals"]

        model_confidence = result.get("model_confidence", 0)
        adjusted_conf = (score + model_confidence) / (model_confidence + CONFIDENCE_BIAS_TERM)
        result["adjusted_model_confidence"] = adjusted_conf
        result["weightage"] = 1.0 if adjusted_conf > HIGH_CONFIDENCE_THRESHOLD else 0.0

    def overall_sentiment(self, product_memory):
        """Computes the overall sentiment score for a product based on historical sentiment data and time decay."""
        add_score = 0
        for item in product_memory.sentiment_history:
            days_since = calculate_days_passed(item['context']['purchase_date'])
            if days_since > 365:
                add_score += ((item['result']['weightage'] * item['result']['sentiment_score']) * 0.5)
            else:
                add_score += (item['result']['weightage'] * item['result']['sentiment_score'])
        
        overall_sentiment_score = add_score/len(product_memory.sentiment_history)

        if overall_sentiment_score > 0.75:
            overall_sentiment = "Highly Positive"
        elif overall_sentiment_score > 0.55:
            overall_sentiment = "Positive"
        elif overall_sentiment_score > 0.45:
            overall_sentiment = "Neutral"
        elif overall_sentiment_score > 0.25:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Highly Negative"

        product_memory.overall_sentiment = overall_sentiment
        product_memory.overall_sentiment_score = overall_sentiment_score
        
        return overall_sentiment, overall_sentiment_score
