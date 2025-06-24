# app.py

import streamlit as st
import pandas as pd
import pickle
import openai
import os
from Core.self_evaluation import self_evaluate
from analyzer.base import MultiAgent
from analyzer.trend import TrendAnalyzerAgent
from memory_manager import ProductMemory

st.set_page_config(page_title="📊 Agentic Review Analyzer", layout="wide")

st.title("🤖 Agentic AI Review Analyzer")

st.sidebar.header("🔧 Configuration Options")
# Model Choice
model_choice = st.sidebar.selectbox(
    label="Choose LLM Model",
    options=["gpt-4o-mini", "gpt-4.1-nano"],
    index=1
)
# API Key Input
api_key = st.sidebar.text_input(
    label="🔑 Enter your OpenAI API Key",
    type="password",
    help="This key is used only during your session and not stored."
)
# Display in main area for debug 
st.write("Selected Model:", model_choice)
if not api_key:
    st.warning("⚠️ Please enter your OpenAI API Key in the sidebar to continue.")
    st.stop()
openai.api_key = api_key

agent = MultiAgent(model=model_choice)

# Initialize session state variables
if "product_memory" not in st.session_state:
    st.session_state.product_memory = None
if "tasks" not in st.session_state:
    st.session_state.tasks = None
if "quality_parameter" not in st.session_state:
    st.session_state.quality_parameter = None
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# Upload File
uploaded_file = st.file_uploader("Upload Review Dataset (CSV)", type=["csv", "xlsx"])

if uploaded_file:

    # Clear cached analysis if new file uploaded
    if "last_uploaded_file" in st.session_state and uploaded_file.name != st.session_state.last_uploaded_file:
        st.session_state.pop("product_memory", None)
        st.session_state.pop("tasks", None)
        st.session_state.pop("quality_parameter", None)
    st.session_state.last_uploaded_file = uploaded_file.name

    # Load dataset
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Validate essential columns
    required_cols = {"customer_review", "rating", "verified_purchase", "review_date", "customer_name", "helpful_votes", "total_votes", "review_length"}
    if not required_cols.issubset(df.columns):
        st.error(f"Dataset must contain: {', '.join(required_cols)}")
        st.stop()

   # Run multi-agent analysis only once
    if "product_memory" not in st.session_state:
        with st.spinner("Running Multi-Agent Analysis..."):
            product_memory, tasks, quality_parameter = agent.create_product_memory_and_prioritize_tasks(df)
            st.session_state.product_memory = product_memory
            st.session_state.tasks = tasks
            st.session_state.quality_parameter = quality_parameter
    else:
        product_memory = st.session_state.product_memory
        tasks = st.session_state.tasks
        quality_parameter = st.session_state.quality_parameter

    #Data Quality Parameter
    with st.expander("📊 Data Quality Parameter", expanded=False):
        st.json(st.session_state.quality_parameter)
        print(tasks)

    # Validate Data Completeness
    if tasks == []:
        st.error(f"Data contains missing values (completeness ratio: {st.session_state.quality_parameter['review_completeness']}). Please handle null entries before proceeding.")
        st.stop()
    st.success("✅ Initial Analysis Complete! Expand below to explore data quality insights.")

    # Save Memory Option
    if st.sidebar.button("💾 Save Memory"):
        save_dir = r"C:\Users\debli\OneDrive\Desktop\CV_PROJECT\AGENTIC_AI_BASED_REVIEW_ANALYZER\data\memory"
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, f"{st.session_state.product_memory.product_name}.pkl")
        
        with open(path, "wb") as f:
            pickle.dump(st.session_state.product_memoryy, f)

        st.sidebar.success(f"Memory saved at:\n📂 `{path}`")

    # Product Summary
    with st.expander("📄 Product Summary", expanded=False):
        if st.session_state.product_memory is not None:
            summary = st.session_state.product_memory.generate_summary()
            st.json(summary)
        else:
            st.info("ℹ️ Product memory not available. Please upload a valid dataset.")


    # Overall Sentiment 
    with st.expander("💬 Overall Sentiment Analysis", expanded=False):
        if st.session_state.product_memory is not None:
            overall_sentiment, overall_sentiment_score = agent.SentimentAnalyzerAgent.overall_sentiment(st.session_state.product_memory)

            # Color mapping
            sentiment_color = {
                "Positive": "#34d399",  # Green
                "Neutral": "#facc15",   # Yellow
                "Negative": "#f87171",  # Red
                "Mixed": "#60a5fa"      # Blue
            }.get(overall_sentiment, "#e5e7eb")  # Default gray

            # Icon mapping
            sentiment_icon = {
                "Positive": "😊",
                "Neutral": "😐",
                "Negative": "😠",
                "Mixed": "🤔"
            }.get(overall_sentiment, "💬")

            # Render UI block
            html_block = f"""
                <div style="background-color: #1e1e1e; border-left: 6px solid {sentiment_color}; padding: 1.3rem 1.5rem; border-radius: 10px; box-shadow: 0 0 8px rgba(255,255,255,0.04); margin-top: 0.5rem;">
                    <h4 style="margin: 0; color: {sentiment_color};">{sentiment_icon} {overall_sentiment} Sentiment</h4> 
                    <p style="font-size: 1.05rem; margin-top: 0.5rem; color: #e5e7eb;">
                        Sentiment Score: <span style="color: {sentiment_color}; font-weight: bold;"> {overall_sentiment_score:.2f} </span>
                    </p>
                </div>
            """
            st.markdown(html_block, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Product memory not available. Please upload a valid dataset.")

    # Review Overview
    with st.expander("🧠 AI-Generated Review Summary", expanded=False):
        if st.session_state.product_memory is not None:
            result, execution_time = agent.ReviewOverviewAgent.create_review_summary(st.session_state.product_memory)
            retry = self_evaluate(result, execution_time)
            if retry:
                result, execution_time = agent.ReviewOverviewAgent.create_review_summary(st.session_state.product_memory)

            summary = result["summary"]
            confidence = result["model_confidence"]

            html_block = f"""
                <div style="background-color: #1e1e1e; border-radius: 12px; padding: 1.2rem 1.5rem; margin-top: 0.5rem; box-shadow: 0 0 10px rgba(255,255,255,0.05);">
                    <h4 style="margin-top: 0; color: #c084fc;">🔍 AI Summary Insight</h4>
                    <p style="font-size: 1.05rem; line-height: 1.6; color: #e5e7eb; margin-bottom: 1rem;">
                        {summary}
                    </p>
                    <p style="font-size: 0.9rem; color: #9ca3af;">
                        🤖 <strong>Model Confidence:</strong> <span style="color: {'#34d399' if confidence >= 0.8 else '#facc15' if confidence >= 0.5 else '#f87171'};">{confidence:.2f}</span>
                    </p>
                </div>
            """
            st.markdown(html_block, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Product memory not available. Please upload a valid dataset.")

    # Top USPs
    with st.expander("✨ Top Praised Features (USPs)", expanded=False):
        if st.session_state.product_memory is not None:
            result, _ = agent.USPDectectorAgent.detect_usps(st.session_state.product_memory)
            retry = self_evaluate(result, execution_time)
            if retry:
                result, execution_time = agent.USPDectectorAgent.detect_usps(st.session_state.product_memory)

            for usp in result['top_usps']:
                feature = usp['feature']
                mentions = usp['positive_mentions']
                justification = usp['justification']

                html_block = f"""
                    <div style="border-left: 5px solid #4ade80; background-color: #1e1e1e; padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 0.8rem;">
                        <h4 style="margin: 0 0 0.2rem 0;">🌟 {feature}</h4>
                        <p style="margin: 0.2rem 0;"><span style="background-color: #10b98133; color: #10b981; padding: 0.2rem 0.5rem; border-radius: 5px; font-weight: bold;">{mentions} mentions</span></p>
                        <p style="margin: 0.3rem 0; color: #d1d5db;"><em>“{justification}”</em></p>
                    </div>
                """
                st.markdown(html_block, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Product memory not available. Please upload a valid dataset.")

    # Top Issues
    with st.expander("⚠️ Top Complaints (Issues)", expanded=False):
        if st.session_state.product_memory is not None:
            result, _ = agent.IssueDetectorAgent.detect_issues(st.session_state.product_memory)
            retry = self_evaluate(result, execution_time)
            if retry:
                result, execution_time = agent.IssueDetectorAgent.detect_issues(st.session_state.product_memory)

            for issue in result['top_issues']:
                feature = issue['feature']
                mentions = issue['negative_mentions']
                justification = issue['justification']

                html_block = f"""
                    <div style="border-left: 5px solid #ef4444; background-color: #2a2a2a; padding: 0.75rem 1rem; border-radius: 10px; margin-bottom: 0.8rem;">
                        <h4 style="margin: 0 0 0.2rem 0;">🚫 {feature}</h4>
                        <p style="margin: 0.2rem 0;">
                            <span style="background-color: #f8717133; color: #f87171; padding: 0.2rem 0.5rem; border-radius: 5px; font-weight: bold;">
                                {mentions} complaints
                            </span>
                        </p>
                        <p style="margin: 0.3rem 0; color: #fca5a5;"><em>“{justification}”</em></p>
                    </div>
                """
                st.markdown(html_block, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Product memory not available. Please upload a valid dataset.")
            

    # Trend Chart
    with st.expander("📈 Sentiment Trend Over Time", expanded=False):
        if st.session_state.product_memory is not None:
            trend_result, trend_dict, _ = agent.TrendAnalyzerAgent.analyze_trend(st.session_state.product_memory, "historical")
            df_trend, metrics = agent.TrendAnalyzerAgent.compute_trend_metrics(trend_dict)

            # Display chart
            st.markdown("### 🔄 Sentiment Evolution")
            agent.TrendAnalyzerAgent.visualize_trend(df_trend, metrics)

            # Display model confidence with color coding
            confidence = trend_result["model_confidence"]
            confidence_color = (
                "#34d399" if confidence >= 0.8 else 
                "#facc15" if confidence >= 0.5 else 
                "#f87171"
            )

            # Card-like summary and confidence report
            html_block = f"""
                <div style="background-color: #1e1e1e; border-left: 5px solid #60a5fa;
                            padding: 1rem 1.2rem; border-radius: 10px; margin-top: 1rem;">
                    <p style="margin-top: 0.5rem; color: #e5e7eb; line-height: 1.5;">
                        {trend_result["trend_analysis_report"]}
                    </p>
                    <p style="margin: 0; font-size: 0.9rem; color: #9ca3af;">
                        🤖 <strong>Model Confidence:</strong> 
                        <span style="color: {confidence_color};">{confidence:.2f}</span>
                    </p>
                </div>
            """
            st.markdown(html_block, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Product memory not available. Please upload a valid dataset.")

    # Recent Processed Reviews
    with st.expander("🕵️‍♂️ Recent Processed Reviews", expanded=False):
        if st.session_state.product_memory is not None:
            recent_reviews = st.session_state.product_memory.get_recent_reviews(n=5)
            
            for idx, review in enumerate(recent_reviews, start=1):
                review_date = review['context']['review_date']
                sentiment = review['result']['sentiment_category']
                score = review['result']['sentiment_score']
                key_drivers = review['result']['key_drivers']
                justification = review['result']['justification']

                with st.container():
                    html_block = f"""
                        <div style="border: 1px solid #444; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; background-color: #1e1e1e;">
                            <h4 style="margin-bottom: 0.3rem;">📝 Review {idx}</h4>
                            <p style="margin: 0.2rem 0;"><strong>📅 Date:</strong> {review_date}</p>
                            <p style="margin: 0.2rem 0;"><strong>🎯 Sentiment:</strong> <span style="color: {'#34c759' if sentiment=='Positive' else '#ff3b30' if sentiment=='Negative' else '#ffd60a'};">{sentiment}</span> (Score: {score:.2f})</p>
                            <p style="margin: 0.2rem 0;"><strong>🧠 Key Drivers:</strong> {key_drivers}</p>
                            <p style="margin: 0.2rem 0;"><strong>🔍 Justification:</strong> {justification}</p>
                        </div>
                    """
                    st.markdown(html_block, unsafe_allow_html=True)

        else:
            st.info("ℹ️ Product memory not available. Please upload a valid dataset.")
