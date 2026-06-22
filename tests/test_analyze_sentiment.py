
import storybuilder.analysis.analyze_sentiment as analyze_sentiment

def test_get_sentiment_value():
    assert analyze_sentiment.get_sentiment_value({"label": "positive", "score": 0.8}) == 0.8
    assert analyze_sentiment.get_sentiment_value({"label": "NEGATIVE", "score": 0.8}) == -0.8
    assert analyze_sentiment.get_sentiment_value({"label": "neutral", "score": 0.8}) == 0.0

def test_extract_chapter_number():
    assert analyze_sentiment.extract_chapter_number("story-name-12.txt") == 12
    assert analyze_sentiment.extract_chapter_number("12-story-name.txt") == 12
    assert analyze_sentiment.extract_chapter_number("story-name.txt") == 0
