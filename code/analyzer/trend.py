import re
import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress
from Core.model_runner import run_llm_model

class TrendAnalyzerAgent:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model

    @staticmethod
    def prepare_data(product_memory, time_span: str):
        sorted_data = sorted(product_memory.monthly_report.items(), reverse=True)

        TIME_SPREAD = {
            "historical" : len(sorted_data),
            "year" : 12 if len(sorted_data) > 12 else None,
            "halfyear" : 6 if len(sorted_data) > 6 else None,
            "quarter" : 3 if len(sorted_data) > 3 else None,
            "month" : 1 if len(sorted_data) > 1 else None
        }
        try:
            trend_type = TIME_SPREAD[time_span.lower()]
        except Exception as e:
            print(f"To run trend analysis choose correct time_spread from ['historical','year','halfyear','quarter', 'month']): {str(e)}")
            return None, None

        if trend_type is not None:
            product_history = ""
            trend_dict = {}
            for month, meta in sorted_data[:trend_type]:
                temp = {}
                for key, value in meta.items():
                    if key not in ['score_sum', 'score_count']:
                        temp[key] = value
                    if key == 'average_sentiment_score':
                        trend_dict[month] = value
                product_history += f"monthly report for {month} : {temp}"
            return product_history, trend_dict
        
        else:
            print("Time span exceeds the available monthly data. Choose a valid time spread.")
            return None, None
        

    @staticmethod
    def build_adaptive_prompt(product_history: str):

        prompt = f"""
        You are an intelligent analytics assistant. Your task is to analyze the historical customer sentiment data of a product over time.

        You will be given month-wise aggregated review insights that include:
        - sentiment distribution (positive, negative, neutral counts)
        - average sentiment score (range: -1.0 to +1.0)
        - key drivers (phrases commonly associated with the sentiment in that month)
        - justification snippets from real customer reviews

        ========================
        Product Monthly Report:
        {product_history}
        ========================

        🎯 Task:
        - Analyze the trend in customer sentiment across the months.
        - Identify whether sentiment is improving, worsening, stable, or fluctuating.
        - If a significant shift in trend occurs (e.g., sudden drop or rise), clearly state:
        1. The **time period of the shift** (e.g., from 2024-12 to 2025-01)
        2. The **likely causes** using key drivers and justification texts.
        - Summarize your findings in a clear paragraph.

        ✅ Strictly produce output in ONLY JSON Format:
        {{
        "trend_analysis_report": "Your paragraph summary here...",
        "model_confidence": float (range: 0.0 to 1.0, indicating your confidence on your trend analysis)
        }}

        📘 Example Output 1 (with trend shift):
        {{
        "trend_analysis_report": "The product experienced generally positive sentiment from 2024-09 to 2024-12, with steadily increasing average sentiment scores. 
        However, there was a noticeable drop in sentiment between 2024-12 and 2025-01. This shift appears to be driven by complaints about overheating and app crashes, 
        as reflected in the increased frequency of negative mentions in justifications like 'gets too hot while charging' and 'frequent app crashes'. Sentiment recovered slightly by 2025-03.",
        "model_confidence": 0.92
        }}

        📘 Example Output 2 (no trend shift):
        {{
        "trend_analysis_report": "Customer sentiment has remained largely stable from 2024-08 to 2025-05. The average sentiment scores hovered between 0.61 and 0.66, and 
        the sentiment distribution showed a consistently high number of positive mentions. No significant changes in sentiment pattern or customer concerns were observed across the months.",
        "model_confidence": 0.89
        }}

        Now generate the output JSON.
        """
        return prompt
    
    def analyze_trend(self, product_memory, time_span: str):
        product_history, trend_dict = self.prepare_data(product_memory, time_span)

        if product_history and trend_dict:
            prompt = self.build_adaptive_prompt(product_history)
            response, execution_time = run_llm_model(self.model, prompt, max_retries=5)

            try:
                cleaned_response = re.findall(r"\{.*?\}", response, flags=re.DOTALL)
                if cleaned_response:
                    result = json.loads(cleaned_response[0])
                    return result, trend_dict, execution_time
                
            except (json.JSONDecodeError, IndexError) as e:
                print(f"Failed to parse through LLM output: {e}")
                return {
                "trend_analysis_report": "",
                "model_confidence": 0.0
            }, trend_dict, execution_time

        return {
                "trend_analysis_report": "",
                "model_confidence": 0.0
            }, {}, 0.0
    
    def compute_trend_metrics(self, trend_dict):

        df = pd.DataFrame(list(trend_dict.items()), columns=['month', 'sentiment_score'])
        if isinstance(df["month"].iloc[0], str):
            df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
        df = df.dropna().sort_values("month")

        if len(df) < 2:
            return df, None
        
        x = np.arange(len(df))
        y = df['sentiment_score'].values

        max_min_delta = np.max(y) - np.min(y)
        volatility = np.std(y)
        slope, _, _, _, _ = linregress(x, y)

        trend_metrics = {'MAX_MIN_DELTA': max_min_delta, 'VOLATILITY': volatility, 'SLOPE': slope}

        return df, trend_metrics

    
    def visualize_trend(self, df, trend_metrics):
        if trend_metrics:
            fig = px.line(
                df,
                x="month",
                y="sentiment_score",
                title="📈 Monthly Sentiment Score Trend",
                markers=True,
                labels={
                    "month": "Month",
                    "sentiment_score": "Average Sentiment Score"})

            fig.update_traces(
                line=dict(color='royalblue', width=2),
                marker=dict(size=8),
                hovertemplate='Month: %{x}<br>Score: %{y:.2f}<extra></extra>')

            fig.add_hline(
                y=0.0,
                line_dash="dot",
                line_color="gray",
                annotation_text="Neutral Line",
                annotation_position="top left")

            annotation_text = (
            f"📊 **Trend Metrics**\n"
            f"- Slope: {trend_metrics['SLOPE']:.4f}\n"
            f"- Min-Max Delta: {trend_metrics['MAX_MIN_DELTA']:.4f}\n"
            f"- Volatility: {trend_metrics['VOLATILITY']:.4f}")

            fig.add_annotation(
                text=annotation_text,
                xref="paper", yref="paper",
                x=1.0, y=1.0,
                showarrow=False,
                align="left",
                bordercolor="black",
                borderwidth=1,
                borderpad=10,
                bgcolor="lightyellow",
                font=dict(size=12, family="Courier New"))

            fig.update_layout(
                template="plotly_white",
                autosize=True,
                margin=dict(l=40, r=40, t=60, b=40),
                xaxis=dict(
                    tickangle=45,
                    title="Month",
                    tickfont=dict(size=12)),
                yaxis=dict(
                    title="Sentiment Score",
                    tickfont=dict(size=12)),
                title=dict(
                    x=0.5,
                    xanchor='center',
                    font=dict(size=20)))

            fig.show()







