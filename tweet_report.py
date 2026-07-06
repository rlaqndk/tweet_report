#!/usr/bin/env python3
"""
Twitter RT 수집기 — kkupuff 계정의 최근 24시간 RT를 섹터별로 정리
Usage:
  python tweet_report.py              # 오늘 07:00 KST 기준 직전 24시간
  python tweet_report.py --date 2026-04-30  # 해당 날짜 07:00 KST 기준 직전 24시간
  python tweet_report.py --weekly     # 최근 7일 누적 통계 출력
"""
import argparse
import json
import os
import sys
import yaml
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from fetcher import make_client, get_user_id, fetch_my_tweets
from classifier import classify_tweet, load_sectors
from reporter import generate_report, generate_weekly_stats

KST = timezone(timedelta(hours=9))


def load_config(path: str = "config.yaml") -> dict:
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: config file not found: {path}", file=sys.stderr)
        sys.exit(1)


def run_weekly(output_dir: Path, base_date: date) -> None:
    """최근 7일치 JSON 파일을 읽어 주간 통계 생성."""
    daily_data = []
    for i in range(6, -1, -1):
        d = base_date - timedelta(days=i)
        json_path = output_dir / f"{d.isoformat()}.json"
        if json_path.exists():
            with open(json_path, encoding="utf-8") as f:
                daily_data.append(json.load(f))

    if not daily_data:
        print("ERROR: 주간 통계를 생성할 일별 데이터가 없습니다. (reports/*.json 확인)", file=sys.stderr)
        sys.exit(1)

    print(f"주간 통계 생성 중 ({len(daily_data)}일치 데이터)...")
    stats = generate_weekly_stats(daily_data)
    out_path = output_dir / f"weekly_{base_date.isoformat()}.md"
    out_path.write_text(stats, encoding="utf-8")
    print(f"Weekly stats saved: {out_path}")
    print(stats)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="YYYY-MM-DD (기본: 오늘)", default=None)
    parser.add_argument("--weekly", action="store_true", help="최근 7일 누적 통계 출력")
    args = parser.parse_args()

    if args.date:
        base_date = date.fromisoformat(args.date)
    else:
        base_date = date.today()

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    if args.weekly:
        run_weekly(output_dir, base_date)
        return

    # 수집 윈도우: base_date 07:00 KST ~ base_date-1 07:00 KST
    end   = datetime(base_date.year, base_date.month, base_date.day, 7, 0, 0, tzinfo=KST)
    start = end - timedelta(days=1)

    config = load_config()
    bearer_token = os.environ.get("BEARER_TOKEN") or config.get("bearer_token")
    if not bearer_token:
        print("ERROR: BEARER_TOKEN env var or config.yaml bearer_token required", file=sys.stderr)
        sys.exit(1)
    client = make_client(bearer_token)
    usernames = config.get("usernames") or [config["username"]]
    sectors = load_sectors(config)

    all_tweets = []
    for username in usernames:
        print(f"Fetching tweets for @{username} ({start.isoformat()} ~ {end.isoformat()})...")
        user_id = get_user_id(client, username)
        tweets = fetch_my_tweets(client, user_id, start, end)
        for tweet in tweets:
            tweet["author"] = username
            tweet["sectors"] = classify_tweet(tweet["text"], sectors)
        by_type = {"rt": 0, "original": 0, "self_reply": 0}
        for t in tweets:
            by_type[t.get("tweet_type", "rt")] += 1
        print(f"  {len(tweets)} tweets fetched (RT {by_type['rt']} | 게시글 {by_type['original']} | 추가설명 {by_type['self_reply']})")
        all_tweets.extend(tweets)

    base = output_dir / base_date.isoformat()

    report = generate_report(all_tweets, base_date)
    (base.with_suffix(".md")).write_text(report, encoding="utf-8")

    json_data = {
        "date": base_date.isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "usernames": usernames,
        "total": len(all_tweets),
        "tweets": all_tweets,
    }
    (base.with_suffix(".json")).write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Report saved: {base}.md + {base.name}.json")


if __name__ == "__main__":
    main()
