"""Sentiment analysis for event feedback comments.

Three layers, tried in order, so the app never crashes if one is missing:

  1. TRAINED MODEL  — TF-IDF + Logistic Regression saved by train_sentiment.py
                      (app/ml_models/sentiment_model.joblib). Learns from labelled data.
  2. VADER          — pre-built sentiment lexicon (no training). Optional dependency.
  3. RATING         — last resort: use the 1–5 star rating (>=4 positive, 3 neutral, <=2 negative).

predict_sentiment() returns (label, score) where label is
"positive" | "neutral" | "negative".
"""
import os
import re
from collections import Counter

_MODEL = None
_MODEL_TRIED = False
_VADER = None
_VADER_TRIED = False

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models", "sentiment_model.joblib")

STOPWORDS = set("""a an the and or but if of to in on at for with is was were be been it this that these those i we you
they he she my our your their me us them so very really just also as are am do did does have has had not no at from by
about there here what which who when where how all any some more most than then too can could would should will""".split())


def _load_model():
    global _MODEL, _MODEL_TRIED
    if _MODEL_TRIED:
        return _MODEL
    _MODEL_TRIED = True
    try:
        import joblib
        if os.path.exists(MODEL_PATH):
            _MODEL = joblib.load(MODEL_PATH)
    except Exception:
        _MODEL = None
    return _MODEL


def _load_vader():
    global _VADER, _VADER_TRIED
    if _VADER_TRIED:
        return _VADER
    _VADER_TRIED = True
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _VADER = SentimentIntensityAnalyzer()
    except Exception:
        _VADER = None
    return _VADER


def _from_rating(rating):
    if rating is None:
        return "neutral", 0.0
    if rating >= 4:
        return "positive", 0.5
    if rating <= 2:
        return "negative", -0.5
    return "neutral", 0.0


def predict_sentiment(text, rating=None):
    """Classify one comment. Empty comments fall back to the star rating."""
    text = (text or "").strip()
    if not text:
        return _from_rating(rating)

    model = _load_model()
    if model:
        pipe = model["pipeline"]
        label = pipe.predict([text])[0]
        proba = pipe.predict_proba([text])[0]
        return str(label), float(max(proba))

    vader = _load_vader()
    if vader:
        c = vader.polarity_scores(text)["compound"]
        label = "positive" if c >= 0.05 else "negative" if c <= -0.05 else "neutral"
        return label, float(c)

    return _from_rating(rating)


def top_keywords(texts, n=8):
    """Most frequent meaningful words across comments (simple, explainable)."""
    counts = Counter()
    for t in texts:
        for w in re.findall(r"[a-zA-Z']{3,}", (t or "").lower()):
            if w not in STOPWORDS:
                counts[w] += 1
    return counts.most_common(n)


def event_sentiment_summary(events):
    """Aggregate sentiment over every feedback row of the given events.

    Uses the label saved at submit time; computes it on the fly for older rows
    that were submitted before sentiment analysis existed.
    """
    totals = {"positive": 0, "neutral": 0, "negative": 0}
    texts_by_label = {"positive": [], "negative": []}
    all_comments = []
    for event in events:
        for fb in event.feedback:
            label = fb.sentiment_label
            if not label:
                label, _ = predict_sentiment(fb.comments, fb.rating)
            totals[label] = totals.get(label, 0) + 1
            if fb.comments:
                all_comments.append(fb.comments)
                if label in texts_by_label:
                    texts_by_label[label].append(fb.comments)
    count = sum(totals.values())
    return {
        "total": count,
        "counts": totals,
        "keywords_positive": top_keywords(texts_by_label["positive"], 6),
        "keywords_negative": top_keywords(texts_by_label["negative"], 6),
        "keywords_all": top_keywords(all_comments, 10),
        "engine": "trained model" if _load_model() else ("VADER" if _load_vader() else "star rating"),
    }
