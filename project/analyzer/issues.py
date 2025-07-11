import re
import json
from Core.model_runner import run_llm_model

class IssueDetectorAgent:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initializes the IssueDetectorAgent with a specified LLM model.
        """
        self.model = model

    @staticmethod
    def build_adaptive_prompt(product_memory):
        """
        Builds a structured LLM prompt for extracting the top 3 negatively mentioned product issues.
        It includes product metadata, issue frequencies, and customer-quoted justifications to guide reasoning.
        """
        product_name = product_memory.product_name
        overall_sentiment = product_memory.overall_sentiment
        overall_sentiment_score = product_memory.overall_sentiment_score
        issues = sorted(product_memory.issues.items(), key = lambda item: item[1], reverse=True)
        issues_justification = product_memory.issue_justification

        all_issues = ', '.join([f"{feature} (frequency: {count})" for feature, count in issues])

        example_output = """
        Example Output:
        {
        "top_issues": [
            {
            "feature": "battery life",
            "negative_mentions": 42,
            "justification": "Users frequently complain that the phone drains quickly and does not last a full day.",
            "model_confidence": 0.94
            },
            {
            "feature": "heating problem",
            "negative_mentions": 38,
            "justification": "Customers often report the phone overheating during gaming or charging.",
            "model_confidence": 0.91
            },
            {
            "feature": "software bugs",
            "negative_mentions": 33,
            "justification": "Reviewers mention frequent app crashes and sluggish updates affecting usability.",
            "model_confidence": 0.89
            }
        ],
        "model_confidence": 0.93
        }
        """

        prompt = f"""
        You are an intelligent **issue detection agent**. Your job is to find the **top 3 most negatively mentioned product features**
        from historical customer reviews and summarize why they were criticized. These are typically the aspects of the product that customers complain about most.

        You will be provided with the product name, overall sentiment, sentiment score, and a list of all previously extracted **negatively highlighted features (issues)**
        along with how frequently they were mentioned and some justification phrases collected from reviews.

        Prioritize features that are mentioned **frequently** AND have **emotionally strong, clearly expressed justifications** for dissatisfaction. Confidence should be higher if the volume and clarity are both strong.

        =======================
        Product: {product_name}

        Overall Sentiment: {overall_sentiment}
        Sentiment Score: {overall_sentiment_score:.2f} (range: -1.0 to +1.0)

        All Issues Mentioned:
        {all_issues}

        Issue Justifications:
        {issues_justification}
        =======================

        🎯 Task:
        From the data above, identify the 3 strongest **issues** based on volume, clarity of justification, and emotional negativity.

        For each issue, include:
        - The feature name
        - Negative mention count (from the data)
        - A short justification (in your own words, summarizing the complaints)
        - Your confidence score for this decision (0.0 to 1.0)

        Format your output as a JSON object with a key called `"top_issues"` that contains a list of three issue records and an overall model confidence score between 0 to 1.

        Use the example below as a guide:
        {example_output}

        Now STRICTLY generate ONLY JSON output like shown below:
        {{
        "top_issues": [a list of three issue records],
        "model_confidence": float (range: 0.0 to 1.0, indicating how confident you are in the quality and accuracy of the top issues)
        }}
        """

        return prompt
    
    def detect_issues(self, product_memory):
        """
        Sends the adaptive prompt to the LLM and parses its JSON response to extract high-confidence issues.
        Filters out weak results and returns a summary of the top issues based on frequency and confidence.
        """
        prompt = self.build_adaptive_prompt(product_memory)
        response, execution_time = run_llm_model(self.model, prompt, max_retries=5)

        try:
            if response:
                result = json.loads(response)

            if result['model_confidence'] < 0.8:
                print("No strong issues exist.")
                return {
                "top_issues": [],
                "model_confidence": 0.0
            }, execution_time
            else:
                result["top_issues"] = [issue for issue in result["top_issues"] if issue['model_confidence'] > 0.85]
                result["top_issues"] = sorted(result["top_issues"], key=lambda x: x["negative_mentions"], reverse=True)
                return result, execution_time
        
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Failed to parse through LLM output: {e}")
            return {
            "top_issues": [],
            "model_confidence": 0.0
        }, execution_time
