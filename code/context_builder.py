#context_builder.py

def get_quality_score(row, helpfulness_ratio):
    """
    Computes a review quality score based on verification status, helpfulness, and review length.
    Returns a float score between 0.0 and 1.0.
    """
    quality_score = 0.0
    if row['verified_purchase']:
        quality_score += 0.3
    if helpfulness_ratio >= 0.6:
        quality_score += 0.2
    if row['review_length'].str.len() > 150:
        quality_score += 0.3
    quality_score = min(quality_score+0.2, 1.0)
    return quality_score

def get_persona_mode(sentiment_trend, quality_score):
    """
    Determines persona mode (Critical, Optimistic, Balanced) based on sentiment trend and quality score.
    """
    if sentiment_trend == "negative" and quality_score > 0.6:
        persona_mode = "Critical"
    elif sentiment_trend == "positive" and quality_score > 0.6:
        persona_mode = "Optimistic"
    else:
        persona_mode = "Balanced"
    return persona_mode

def build_context(row, memory):
    """
    Builds a structured context dictionary combining review metadata, memory trends, and derived metrics.
    Used as input for downstream analysis or LLM tasks.
    """
    helpfulness_ratio = row['helpful_votes']/row['total_votes'] if row['total_votes'] > 0 else 0.0

    quality_score = get_quality_score(row, helpfulness_ratio)

    sentiment_trend = memory.get_sentiment_trend()
    recent_issues = memory.get_top_issues(limit=3)
    top_usps = memory.get_top_usps(limit=3)

    persona_mode = get_persona_mode(sentiment_trend, quality_score)

    return {
        "verified_purchase" : bool(row['verfied_purchase']),
        "rating" : int(row['rating']),
        "review_length" : int(row['review_length']),
        "helpfulness_helpfulness_ratio" : helpfulness_ratio,
        "quality_score" : quality_score,
        "base_confidence" : 0.8 if row['verified_purchase'] else 0.6,
        "persona_mode" : persona_mode,
        "sentiment_trend" : sentiment_trend,
        "recent_issues" : recent_issues,
        "top_usps" : top_usps,
        "purchase_date" : row['purchase_date'],
        "review_date" : row['review_date'],
        "reviewer_name" : row["reviewer_name"]
    }  
