import pytest
from datetime import date
from reporter import generate_report

SAMPLE_TWEETS = [
    {"id": "1", "author": "elonmusk", "text": "NVDA is going to the moon", "time": "07:30", "sectors": ["반도체_팹리스"]},
    {"id": "2", "author": "jimcramer", "text": "FDA approval incoming", "time": "06:15", "sectors": ["바이오"]},
    {"id": "3", "author": "elonmusk", "text": "Good morning", "time": "05:00", "sectors": ["기타"]},
]

def test_report_contains_prompt_header():
    report = generate_report(SAMPLE_TWEETS, date(2026, 4, 30))
    assert "2026-04-30" in report
    assert "섹터별로" in report

def test_report_contains_sector_headers():
    report = generate_report(SAMPLE_TWEETS, date(2026, 4, 30))
    assert "## 반도체_팹리스" in report
    assert "## 바이오" in report

def test_report_contains_tweet_entries():
    report = generate_report(SAMPLE_TWEETS, date(2026, 4, 30))
    assert "@elonmusk" in report
    assert "NVDA is going to the moon" in report

def test_empty_sector_not_in_report():
    tweets = [{"id": "1", "author": "user", "text": "hello", "time": "08:00", "sectors": ["반도체_팹리스"]}]
    report = generate_report(tweets, date(2026, 4, 30))
    assert "## 바이오" not in report

def test_기타_section_at_end():
    report = generate_report(SAMPLE_TWEETS, date(2026, 4, 30))
    assert report.index("## 기타") > report.index("## 반도체_팹리스")
