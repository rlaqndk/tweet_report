from datetime import date
from collections import defaultdict

SECTOR_ORDER = [
    "반도체_메모리", "반도체_파운드리", "반도체_팹리스", "반도체_소부장",
    "AI_소프트웨어", "AI_인프라", "로보틱스",
    "바이오", "에너지",
    "금융_매크로", "금융_국내",
    "테크_플랫폼", "테크_글로벌",
    "기업이슈", "기타",
]


def generate_report(tweets: list, report_date: date) -> str:
    by_sector = defaultdict(list)
    for tweet in tweets:
        for sector in tweet["sectors"]:
            by_sector[sector].append(tweet)

    type_counts = {"rt": 0, "original": 0, "self_reply": 0}
    for tweet in tweets:
        type_counts[tweet.get("tweet_type", "rt")] += 1

    lines = [
        f"다음은 {report_date.isoformat()} 수집된 주식 관련 트윗입니다. (RT + 게시글 + 추가설명 답글)",
        "섹터별로 주요 종목 추이와 추천 종목을 분석해주세요.",
        "",
        f"> 총 {len(tweets)}건 (RT {type_counts['rt']} | 게시글 {type_counts['original']} | 추가설명 {type_counts['self_reply']})",
        "",
        "---",
        "",
    ]

    for sector in SECTOR_ORDER:
        if sector not in by_sector:
            continue
        lines.append(f"## {sector}")
        for t in by_sector[sector]:
            tweet_type = t.get("tweet_type", "rt")
            if tweet_type == "rt":
                type_part = f" RT @{t['rt_author']}" if t.get("rt_author") else " RT"
            elif tweet_type == "self_reply":
                type_part = " [답글]"
            else:
                type_part = ""
            lines.append(f"- @{t['author']}{type_part} ({t['time']}): {t['text']}<!-- {t['id']} -->")
        lines.append("")

    return "\n".join(lines)


def generate_weekly_stats(daily_data: list) -> str:
    """주간 누적 통계 생성.

    Args:
        daily_data: 일별 JSON 파일에서 로드한 dict 리스트 (7일치)
    """
    rt_by_author = defaultdict(int)
    rt_by_sector = defaultdict(int)
    daily_counts = []

    for day in daily_data:
        tweets = day.get("tweets", [])
        daily_counts.append((day["date"], len(tweets)))
        for t in tweets:
            if t.get("rt_author"):
                rt_by_author[t["rt_author"]] += 1
            for sector in t.get("sectors", []):
                rt_by_sector[sector] += 1

    total = sum(c for _, c in daily_counts)
    avg_daily = total / len(daily_counts) if daily_counts else 0

    lines = ["# 주간 RT 통계", ""]

    if daily_counts:
        lines.append(f"**기간**: {daily_counts[0][0]} ~ {daily_counts[-1][0]}")
    lines.append(f"**총 RT**: {total}건 | **일평균**: {avg_daily:.1f}건")
    lines.append("")

    lines.append("## 원본 작성자별 RT 수 (다양성)")
    top_authors = sorted(rt_by_author.items(), key=lambda x: -x[1])[:20]
    if top_authors:
        for author, count in top_authors:
            lines.append(f"- @{author}: {count}건")
    else:
        lines.append("- (데이터 없음)")
    lines.append("")

    lines.append("## 섹터별 RT 수")
    for sector in SECTOR_ORDER:
        if sector in rt_by_sector:
            lines.append(f"- {sector}: {rt_by_sector[sector]}건")
    lines.append("")

    lines.append("## 일별 RT 수")
    for d, c in daily_counts:
        lines.append(f"- {d}: {c}건")

    return "\n".join(lines)
