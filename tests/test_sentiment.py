from app.models import Feedback
from app.services.ml_service import predict_sentiment, top_keywords
from tests.conftest import login


def test_empty_comment_falls_back_to_rating():
    assert predict_sentiment("", 5)[0] == "positive"
    assert predict_sentiment("", 1)[0] == "negative"
    assert predict_sentiment(None, 3)[0] == "neutral"


def test_clear_comments_are_classified():
    assert predict_sentiment("Loved it, the speakers were inspiring and engaging")[0] == "positive"
    assert predict_sentiment("Terrible, it started very late and nothing was managed properly")[0] == "negative"


def test_top_keywords_ignores_stopwords():
    words = dict(top_keywords(["the food was great", "great food and the queue"]))
    assert words["great"] == 2 and words["food"] == 2 and "the" not in words


def test_feedback_stores_sentiment_label(client, db, participant_user, sample_event):
    login(client, participant_user.email)
    client.post(f"/participant/events/{sample_event.id}/feedback",
                data={"rating": "5", "comments": "Absolutely loved it, amazing organisers"})
    fb = Feedback.query.first()
    assert fb.sentiment_label == "positive"
