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
        issues = sorted(product_memory.issues.items(), key = lambda item: item[1], reverse=True)
        usps_justification = product_memory.usp_justification
        issues_justification = product_memory.issue_justification

        top_usps = ', '.join([f"{feature} (frequency: {count})" for feature, count in usps[:5]])
        top_issues = ', '.join([f"{feature} (frequency: {count})" for feature, count in issues[:5]])

        example_summary = """
        Example Summary:
        {
        "summary": "Customers generally have a highly positive impression of the product. Praise centers on its battery life, crisp display, and responsive performance. 
        Many noted that the device feels premium and delivers consistently on daily reliability, especially for users engaged in multitasking or extensive media consumption. 
        The seamless software experience, build quality, and charging speed were also mentioned frequently, adding to the overall appeal.
        Users appreciated the thoughtfully designed user interface and minimal bloatware, which enhanced day-to-day usability. Long battery endurance stood out for commuters and travelers, 
        while the vibrant display drew praise from those who frequently stream videos or engage in gaming. There were repeated mentions of smooth app switching and minimal lag, 
        which suggests the device’s internal performance is tuned well for real-world usage scenarios. However, the product is not without criticisms. 
        Some users pointed out issues with the durability of the charging port after a few months of usage, and a smaller but vocal group noted inconsistent camera quality in low-light conditions. 
        A handful of reviews flagged heating during extended gaming sessions. While these concerns were significant for a subset of customers, they did not generally outweigh the phone’s strengths.
        Overall, the tone of the feedback is confident and enthusiastic, reflecting a strong alignment between user expectations and actual experience. 
        The review landscape shows that while some functional improvements could elevate the product further, the current feature set is already meeting — and often exceeding — consumer 
        needs across multiple usage profiles.",
        "model_confidence": 0.92
        }"""

        prompt = f"""
        You are a customer insights and sentiment analysis AI tasked with generating a human-readable review summary
        for the product: **{product_name}**.

        You will be provided with:
        - The most praised features (USPs) and common issues.
        - Justifications or extracted phrases behind those praises or complaints.
        - An aggregated overall sentiment and sentiment score.

        Your goal is to generate a clear, structured, and emotionally aligned overview that could be shown on a product page,
        executive summary, or review dashboard.

        ======================
        Product: {product_name}

        Overall Sentiment Summary:
        - Trend: {overall_sentiment}
        - Sentiment Score: {overall_sentiment_score:.2f} (range: -1.0 to +1.0)

        Top Praised Features (USPs):
        {top_usps}

        USP Justifications:
        {usps_justification}

        Top Reported Issues:
        {top_issues}

        Issue Justifications:
        {issues_justification}
        ======================

        🧠 Write a concise overview that:
        - Starts with the overall customer impression and emotional tone.
        - Highlights the most appreciated features with brief context.
        - Points out common issues, neutrally and constructively.
        - Reflects emotional intensity based on sentiment score.
        - Does **not** include raw counts — use them to prioritize content only.

        🎯 Format as a short paragraph (approx. 300–350 words) suitable for business reports or customer-facing summaries.

        Use the example below as guidance:
        {example_summary}

        Generate the review summary below in the following JSON format:
        {
        "summary": "<insert full review summary here>",
        "model_confidence": float (range: 0.0 to 1.0, indicating how confident you are in the quality and accuracy of the summary)
        }
        """
        return prompt
    
    def create_review_summary(self, product_memory, overall_sentiment, overall_sentiment_score):
        prompt = self.build_adaptive_prompt(product_memory, overall_sentiment, overall_sentiment_score)
        response = run_llm_model(self.model, prompt, max_retries=5)
        try:
            cleaned_response = re.findall(r"\{.*?\}", response, flags=re.DOTALL)
            result = json.loads(cleaned_response[0])
            return result
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Failed to parse review summary: {e}")
            return {
            "summary": "",
            "model_confidence": 0.0
        }
