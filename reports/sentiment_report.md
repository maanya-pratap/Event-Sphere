# Sentiment analysis report

Training files: data\synthetic_feedback.csv
Rows: 900 (train 720 / test 180). Class counts: {'positive': 300, 'negative': 300, 'neutral': 300}

> **Caveat:** if only `synthetic_feedback.csv` is present, this data is template-generated, so scores are optimistic. Retrain on real labelled Aurora comments for honest numbers.

### Logistic Regression + TF-IDF ← selected
Accuracy 1.000 · macro-precision 1.000 · macro-recall 1.000 · macro-F1 1.000

Confusion matrix (rows = actual, columns = predicted):

| actual \ predicted | negative | neutral | positive |
|---|---|---|---|
| negative | 60 | 0 | 0 |
| neutral | 0 | 60 | 0 |
| positive | 0 | 0 | 60 |

### Naive Bayes + TF-IDF
Accuracy 1.000 · macro-precision 1.000 · macro-recall 1.000 · macro-F1 1.000

Confusion matrix (rows = actual, columns = predicted):

| actual \ predicted | negative | neutral | positive |
|---|---|---|---|
| negative | 60 | 0 | 0 |
| neutral | 0 | 60 | 0 |
| positive | 0 | 0 | 60 |

### VADER (no training, lexicon-based) on the same test split
Accuracy 0.806 · macro-precision 0.847 · macro-recall 0.806 · macro-F1 0.783

Confusion matrix (rows = actual, columns = predicted):

| actual \ predicted | negative | neutral | positive |
|---|---|---|---|
| negative | 59 | 1 | 0 |
| neutral | 8 | 26 | 26 |
| positive | 0 | 0 | 60 |

### Hard hold-out set (12 tricky sentences, never trained on) — Logistic Regression + TF-IDF
Accuracy 0.250 · macro-precision 0.300 · macro-recall 0.250 · macro-F1 0.259

Confusion matrix (rows = actual, columns = predicted):

| actual \ predicted | negative | neutral | positive |
|---|---|---|---|
| negative | 1 | 2 | 1 |
| neutral | 3 | 1 | 0 |
| positive | 1 | 2 | 1 |

### VADER on the hard hold-out set
Accuracy 0.667 · macro-precision 0.774 · macro-recall 0.667 · macro-F1 0.626

Confusion matrix (rows = actual, columns = predicted):

| actual \ predicted | negative | neutral | positive |
|---|---|---|---|
| negative | 3 | 0 | 1 |
| neutral | 1 | 1 | 2 |
| positive | 0 | 0 | 4 |
