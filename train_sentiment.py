"""Train and evaluate the sentiment model for EventSphere feedback.

Run:   python train_sentiment.py

What it does
  1. Loads every CSV in data/ (columns: text,label). Synthetic + any real data you add.
  2. 80/20 stratified train/test split.
  3. Trains two classic models on TF-IDF features: Logistic Regression and Naive Bayes.
  4. Reports accuracy, precision, recall, F1 and the confusion matrix for each
     model, and for VADER (a pre-built lexicon, no training) if installed.
  5. Also tests on data/holdout/*.csv (tricky sentences never trained on).
  6. Saves the best model to app/ml_models/sentiment_model.joblib and a
     human-readable report to reports/sentiment_report.md.
"""
import glob
import os
import sys

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

LABELS = ["negative", "neutral", "positive"]
MODEL_PATH = os.path.join("app", "ml_models", "sentiment_model.joblib")
REPORT_PATH = os.path.join("reports", "sentiment_report.md")


def load_csvs(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        return pd.DataFrame(columns=["text", "label"]), []
    frames = [pd.read_csv(f)[["text", "label"]] for f in files]
    df = pd.concat(frames, ignore_index=True).dropna()
    df["label"] = df["label"].str.strip().str.lower()
    return df[df["label"].isin(LABELS)].drop_duplicates(), files


def vader_predict(texts):
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        return None
    an = SentimentIntensityAnalyzer()
    out = []
    for t in texts:
        c = an.polarity_scores(t)["compound"]
        out.append("positive" if c >= 0.05 else "negative" if c <= -0.05 else "neutral")
    return out


def metrics(y_true, y_pred):
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": p, "recall": r, "f1": f,
        "confusion": confusion_matrix(y_true, y_pred, labels=LABELS),
    }


def fmt(name, m):
    cm = m["confusion"]
    lines = [
        f"### {name}",
        f"Accuracy {m['accuracy']:.3f} · macro-precision {m['precision']:.3f} · macro-recall {m['recall']:.3f} · macro-F1 {m['f1']:.3f}",
        "",
        "Confusion matrix (rows = actual, columns = predicted):",
        "",
        "| actual \\ predicted | " + " | ".join(LABELS) + " |",
        "|---|" + "---|" * len(LABELS),
    ]
    for lab, row in zip(LABELS, cm):
        lines.append(f"| {lab} | " + " | ".join(str(int(x)) for x in row) + " |")
    return "\n".join(lines)


def main():
    df, files = load_csvs("data/*.csv")
    if df.empty:
        sys.exit("No training data found. Run: python ml/generate_synthetic_data.py")
    hold, hold_files = load_csvs("data/holdout/*.csv")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    candidates = {
        "Logistic Regression + TF-IDF": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
            ("clf", LogisticRegression(max_iter=1000, C=3.0)),
        ]),
        "Naive Bayes + TF-IDF": Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True)),
            ("clf", MultinomialNB(alpha=0.3)),
        ]),
    }

    results, trained = {}, {}
    for name, pipe in candidates.items():
        pipe.fit(X_train, y_train)
        results[name] = metrics(y_test, pipe.predict(X_test))
        trained[name] = pipe

    best_name = max(results, key=lambda n: results[n]["f1"])
    best = trained[best_name]

    vader_test = vader_predict(list(X_test))
    vader_m = metrics(y_test, vader_test) if vader_test else None

    out = ["# Sentiment analysis report", ""]
    out.append(f"Training files: {', '.join(files)}")
    out.append(f"Rows: {len(df)} (train {len(X_train)} / test {len(X_test)}). Class counts: {df['label'].value_counts().to_dict()}")
    out.append("")
    out.append("> **Caveat:** if only `synthetic_feedback.csv` is present, this data is template-generated, "
               "so scores are optimistic. Retrain on real labelled Aurora comments for honest numbers.")
    out.append("")
    for n, m in results.items():
        out += [fmt(n + (" ← selected" if n == best_name else ""), m), ""]
    if vader_m:
        out += [fmt("VADER (no training, lexicon-based) on the same test split", vader_m), ""]
    else:
        out += ["### VADER", "`vaderSentiment` is not installed in this environment, so no VADER numbers were produced. "
                "Run `pip install vaderSentiment` and re-run this script to add the comparison.", ""]

    if not hold.empty:
        hm = metrics(hold["label"], best.predict(hold["text"]))
        out += [fmt(f"Hard hold-out set ({len(hold)} tricky sentences, never trained on) — {best_name}", hm), ""]
        vh = vader_predict(list(hold["text"]))
        if vh:
            out += [fmt("VADER on the hard hold-out set", metrics(hold["label"], vh)), ""]

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    joblib.dump({"pipeline": best, "labels": LABELS, "name": best_name}, MODEL_PATH)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("\n".join(out))
    print(f"\nSaved model -> {MODEL_PATH}\nSaved report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
