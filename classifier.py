def classify_tweet(text: str, sectors: dict) -> list:
    """트윗 텍스트를 섹터 키워드로 분류. 매칭 없으면 ['기타'] 반환."""
    text_lower = text.lower()
    matched = []
    for sector, keywords in sectors.items():
        if sector == "기타":
            continue
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(sector)
                break
    return matched if matched else ["기타"]


def load_sectors(config: dict) -> dict:
    """config dict에서 sectors 추출."""
    return config.get("sectors", {"기타": []})
