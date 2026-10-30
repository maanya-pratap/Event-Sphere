"""Generate a SYNTHETIC labelled dataset of event-feedback comments.

IMPORTANT — be honest about this in the viva:
  This data is machine-generated from templates, not written by real students.
  It exists only so the training pipeline runs end-to-end before Aurora
  produces real feedback. Accuracy measured on it is OPTIMISTIC (the
  sentences share a small vocabulary). Once real, human-labelled comments
  exist, drop them into data/real_feedback_labelled.csv (columns: text,label)
  and re-run train_sentiment.py — it merges every CSV in data/ automatically.

Run:  python ml/generate_synthetic_data.py
"""
import csv
import os
import random

random.seed(42)

EVENTS = ["the hackathon", "the workshop", "the cultural fest", "the seminar", "the quiz", "the coding contest",
          "the event", "the session", "the competition", "the talk", "the tech fest", "the dance night"]

POS_OPEN = ["Loved", "Really enjoyed", "Had a great time at", "Amazing experience at", "Super fun", "Brilliant",
            "Thoroughly enjoyed", "Such a fantastic", "Great", "Absolutely loved"]
POS_BODY = ["the organisers were friendly and helpful", "everything was well managed and on time",
            "the speakers were inspiring and engaging", "I learned so much and made new friends",
            "the venue was perfect and the energy was awesome", "the volunteers were super supportive",
            "it was very well organised", "the content was excellent and useful",
            "the prizes and the atmosphere were fantastic", "would definitely attend again"]
NEG_OPEN = ["Disappointed with", "Really bad experience at", "Did not enjoy", "Terrible", "Very poorly organised",
            "Waste of time at", "Frustrating", "Honestly the worst", "Not happy with", "Boring"]
NEG_BODY = ["it started very late and nobody told us why", "the sound system was bad and we could not hear anything",
            "the registration queue was chaotic and slow", "the speakers were dull and unprepared",
            "it was overcrowded and there was no water", "the organisers were rude and unhelpful",
            "nothing was managed properly", "the venue was dirty and uncomfortable",
            "the schedule kept changing and it was confusing", "would not recommend to anyone"]
NEU_OPEN = ["Attended", "Went to", "Was present at", "Took part in", "Joined", "Visited"]
NEU_BODY = ["it was okay, nothing special", "it was fine, some parts good and some average",
            "it started at 10 and ended at 4", "it was held in the main auditorium",
            "average experience overall", "some things were good, some could be better",
            "it was an ordinary event", "not bad, not great either",
            "the topic was standard and the duration was normal", "it was alright"]

# Mixed / negated sentences: kept OUT of training and used as a harder hold-out test.
HARD = [
    ("Not bad at all, I actually enjoyed it", "positive"),
    ("Not good, I expected much more", "negative"),
    ("It was not boring, the speakers kept us hooked", "positive"),
    ("Great idea but terrible execution", "negative"),
    ("Good content but the venue was too crowded to enjoy it", "neutral"),
    ("The food was great but the sound system was bad", "neutral"),
    ("Could have been better but I still learned something", "neutral"),
    ("I wouldn't say it was great", "negative"),
    ("Never been to a better college event", "positive"),
    ("Nothing to complain about, smooth and well planned", "positive"),
    ("Not worth the time", "negative"),
    ("Decent, I guess", "neutral"),
]


def make(label):
    if label == "positive":
        o, b = POS_OPEN, POS_BODY
    elif label == "negative":
        o, b = NEG_OPEN, NEG_BODY
    else:
        o, b = NEU_OPEN, NEU_BODY
    opener = random.choice(o)
    if opener.endswith(("at", "of")) or opener in {"Attended", "Went to", "Was present at", "Took part in", "Joined", "Visited"}:
        sentence = f"{opener} {random.choice(EVENTS)} — {random.choice(b)}"
    else:
        sentence = f"{opener} {random.choice(EVENTS).replace('the ', '')}, {random.choice(b)}"
    if random.random() < 0.25:
        sentence = sentence.lower()
    if random.random() < 0.2:
        sentence += random.choice(["!", ".", "...", " :)" if label == "positive" else " :("])
    return sentence


def main(n_per_class=300, out="data/synthetic_feedback.csv"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = set()
    for label in ("positive", "negative", "neutral"):
        count = 0
        while count < n_per_class:
            r = (make(label), label)
            if r not in rows:
                rows.add(r)
                count += 1
    # HARD cases are NOT trained on: they go to data/holdout/ as an extra, tougher test set.
    os.makedirs("data/holdout", exist_ok=True)
    with open("data/holdout/hard_cases.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label"])
        w.writerows(HARD)
    rows = sorted(rows)
    random.shuffle(rows)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label"])
        w.writerows(rows)
    print(f"Wrote {len(rows)} SYNTHETIC rows to {out}")


if __name__ == "__main__":
    main()
