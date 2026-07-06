import pytest
from classifier import classify_tweet, load_sectors

SECTORS = {
    "반도체": ["NVDA", "AMD", "반도체"],
    "바이오": ["FDA", "바이오"],
    "기타": [],
}

def test_classify_single_sector():
    result = classify_tweet("NVDA is going to the moon", SECTORS)
    assert result == ["반도체"]

def test_classify_multiple_sectors():
    result = classify_tweet("NVDA FDA approval news", SECTORS)
    assert set(result) == {"반도체", "바이오"}

def test_classify_no_match_returns_기타():
    result = classify_tweet("Good morning everyone", SECTORS)
    assert result == ["기타"]

def test_classify_case_insensitive():
    result = classify_tweet("nvda is cheap", SECTORS)
    assert result == ["반도체"]

def test_classify_korean_keyword():
    result = classify_tweet("반도체 섹터 강세", SECTORS)
    assert result == ["반도체"]
