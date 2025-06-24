import nltk
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from datetime import datetime

nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('punkt')

def compute_word_diversity(df: pd.DataFrame):
    """Returns vocabulary richness of customer reviews."""
    stemmer = PorterStemmer()
    all_reviews = " ".join(df['customer_review'].dropna().astype(str).apply(lambda x: x.lower()).tolist())
    tokens = word_tokenize(all_reviews)
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [stemmer.stem(token) for token in tokens if token.isalpha() and token not in stop_words]
    
    vocab_richness = len(set(filtered_tokens))/len(filtered_tokens)
    return vocab_richness

def assess_data_quality(df: pd.DataFrame):
    """Returns quality metrics of the review dataset."""
    quality_metrics = {}
    try:
        avg_review_len = df['review_length'].mean()
        quality_metrics['review_length_ratio'] = round(min(avg_review_len/100, 1), 2)
        
        dates = df['review_date'].apply(lambda x: calculate_days_passed(x))
        date_range = max(dates) - min(dates)
        quality_metrics['temporal_spread'] = round(min(date_range/365, 1), 2)

        quality_metrics['vocab_richness'] = compute_word_diversity(df)

        verified_purchase = df[df['verified_purchase'] == True]
        quality_metrics['verified_purchase_ratio'] = round(len(verified_purchase)/len(df), 2)

        quality_metrics['rating_mean'] = round(df['rating'].mean(), 2)
        quality_metrics['rating_std'] = round(df['rating'].std(), 2)

        empty_ratio = df.isnull().sum().sum()/(len(df) * len(df.columns))
        quality_metrics['review_completeness'] = round((1 - empty_ratio), 2)
        return quality_metrics
    
    except Exception as e:
        print(f"Failed to analyze data quality: {str(e)}")
        return {}

def autonomous_task_selection(df: pd.DataFrame):
    """Returns list of tasks to perform and data quality parameters based on review quality."""
    selections = []
    quality_params = assess_data_quality(df)
    if quality_params['review_completeness'] != 1:
        print(f"Data has missing values with completeness ratio : {quality_params['review_completeness']}")
        return selections, quality_params
    selections.append("sentiment")
    selections.append("summary")
    try:
        if len(df) > 50 and quality_params['temporal_spread'] >= 0.1:
            selections.append("trend_analysis")
        if quality_params['vocab_richness'] > 0.1 and quality_params['verified_purchase_ratio'] > 0.8 and quality_params['review_length_ratio'] > 0.7:
            selections.append("usps")
            selections.append("issues")
        return selections, quality_params
    except Exception as e:
        print(f"Failed to complete task selection: {str(e)}")
    return selections, quality_params

def calculate_days_passed(date_str: str):
    """Returns days passed since given date string."""
    past_date = datetime.strptime(date_str, "%d-%m-%Y")
    today = datetime.today()
    days_passed = (today - past_date).days

    return days_passed