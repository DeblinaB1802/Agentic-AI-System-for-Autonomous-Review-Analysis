import re
import json
from Core.model_runner import run_llm_model

class ReviewOverviewAgent:
    def __init__(self, model: str = "deepseek-r1"):
        self.model = model

    @staticmethod
    def build_adaptive_prompt(product_memory, overall_sentiment, overall_sentiment_score):

        product_name = product_memory.product_name
        usps = sorted(product_memory.usps.items(), key = lambda item: item[1], reverse=True)
        usps_justification = product_memory.usp_justification

        all_usps = ', '.join([f"{feature} (frequency: {count})" for feature, count in usps])

        example_output = """
        Example Output:
        {
        "top_usps": [
            {
            "feature": "battery life",
            "positive_mentions": 42,
            "justification": "Users consistently praise the phone's ability to last over a day on a single charge.",
            "model_confidence": 0.94
            },
            {
            "feature": "display quality",
            "positive_mentions": 38,
            "justification": "Customers are impressed by the crisp, vibrant screen quality, especially for video streaming.",
            "model_confidence": 0.91
            },
            {
            "feature": "performance",
            "positive_mentions": 33,
            "justification": "Reviewers appreciate the smooth and lag-free experience when multitasking.",
            "model_confidence": 0.89
            }
        ]
        "model_confidence" : 0.93
        }
        """

        prompt = f"""
        You are an intelligent USP (Unique Selling Point) extraction agent. Your job is to find the top 3 most positively mentioned product features
        from historical customer reviews and summarize why they matter. These are typically the features that customers repeatedly praise with enthusiasm.

        You will be provided with the product name, overall sentiment, sentiment score, and a list of all previously extracted praised features (USPs)
        along with how frequently they were mentioned and some justification phrases collected from reviews.

        Prioritize features that are mentioned frequently AND have emotionally strong, well-supported justifications. Confidence should be higher if the volume and clarity are both strong.
        =======================
        Product: {product_name}

        Overall Sentiment: {overall_sentiment}
        Sentiment Score: {overall_sentiment_score:.2f} (range: -1.0 to +1.0)

        All USPs Mentioned:
        {all_usps}

        USP Justifications:
        {usps_justification}
        =======================

        🎯 Task:
        From the data above, identify the 3 strongest USPs based on volume, clarity of justification, and emotional positivity.
        For each USP, include:
        - The feature name
        - Positive mention count (from the data)
        - A short justification (in your own words, summarizing the praise)
        - Your confidence score for this decision (0.0 to 1.0)

        Format your output as a JSON object with keys called "top_usps" that contains a list of three USP records and overall model confidence score range between 0 to 1.

        Use the example below as a guide:
        {example_output}

        Now generate the JSON output below:
        {
        "top_usps": [a list of three USP records],
        "model_confidence": float (range: 0.0 to 1.0, indicating how confident you are in the quality and accuracy of the top usps)
        }
        """
        return prompt
    
    def create_review_summary(self, product_memory, overall_sentiment, overall_sentiment_score):
        prompt = self.build_adaptive_prompt(product_memory, overall_sentiment, overall_sentiment_score)
        response = run_llm_model(self.model, prompt, max_retries=5)

        try:
            cleaned_response = re.findall(r"\{.*?\}", response, flags=re.DOTALL)
            if cleaned_response:
                result = json.loads(cleaned_response[0])

            if result['model_confidence'] < 0.8:
                print("No strong USPs exist.")
                return {
                "top_usps": [],
                "model_confidence": 0.0
            }
            else:
                result["top_usps"] = [usp for usp in result["top_usps"] if usp['model_confidence'] > 0.85]
                result["top_usps"] = sorted(result["top_usps"], key=lambda x: x["positive_mentions"], reverse=True)
                return result
        
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Failed to parse review summary: {e}")
            return {
            "top_usps": [],
            "model_confidence": 0.0
        }