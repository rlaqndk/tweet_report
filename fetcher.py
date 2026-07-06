import tweepy
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def make_client(bearer_token: str) -> tweepy.Client:
    return tweepy.Client(bearer_token=bearer_token)


def get_user_id(client: tweepy.Client, username: str) -> str:
    response = client.get_user(username=username)
    return response.data.id


def fetch_my_tweets(client: tweepy.Client, user_id: str, start: datetime, end: datetime) -> list:
    """start ~ end 사이에 작성한 트윗 목록 반환.

    수집 대상:
    - RT: referenced_tweets에 "retweeted" 포함
    - 원본 게시글: referenced_tweets 없음
    - 자기 답글(추가 설명): in_reply_to_user_id == user_id (본인 트윗 스레드)

    제외:
    - 다른 사람 트윗에 달린 대화 답글

    Returns list of tweet dicts with: id, text, time, rt_at, rt_author, entities, tweet_type
    tweet_type: "rt" | "original" | "self_reply"
    """
    all_tweets = []
    pagination_token = None

    while True:
        resp = client.get_users_tweets(
            id=user_id,
            start_time=start,
            end_time=end,
            max_results=100,
            tweet_fields=["created_at", "referenced_tweets", "entities", "note_tweet", "author_id", "in_reply_to_user_id"],
            expansions=["referenced_tweets.id", "referenced_tweets.id.author_id"],
            user_fields=["username"],
            pagination_token=pagination_token,
        )

        if not resp.data:
            break

        # 원본 트윗 정보 맵: tweet_id -> {text, author_id}
        expanded = {}
        if resp.includes and resp.includes.get("tweets"):
            for t in resp.includes["tweets"]:
                nt = getattr(t, "note_tweet", None)
                if isinstance(nt, dict):
                    full_text = nt.get("text") or t.text
                elif nt is not None:
                    full_text = getattr(nt, "text", None) or t.text
                else:
                    full_text = t.text
                expanded[t.id] = {
                    "text": full_text,
                    "author_id": str(getattr(t, "author_id", "") or ""),
                }

        # user_id -> username 맵 (RT 원본 작성자)
        users = {}
        if resp.includes and resp.includes.get("users"):
            for u in resp.includes["users"]:
                users[str(u.id)] = u.username

        for tweet in resp.data:
            refs = getattr(tweet, "referenced_tweets", None) or []
            ref_types = {getattr(r, "type", None) for r in refs}

            in_reply_to_user_id = getattr(tweet, "in_reply_to_user_id", None)
            is_rt = "retweeted" in ref_types
            is_reply = "replied_to" in ref_types
            # 본인 트윗에 달린 답글(스레드형 추가설명)만 포함
            is_self_reply = is_reply and str(in_reply_to_user_id) == str(user_id)
            is_original = not is_rt and not is_reply

            if not (is_rt or is_original or is_self_reply):
                continue

            created_at = tweet.created_at
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            kst_time = created_at.astimezone(KST)

            text = tweet.text
            rt_author = None

            if is_rt:
                tweet_type = "rt"
                for r in refs:
                    if getattr(r, "type", None) == "retweeted":
                        orig = expanded.get(r.id)
                        if orig:
                            text = orig["text"]
                            author_id = orig.get("author_id")
                            if author_id:
                                rt_author = users.get(author_id)
                        break
            elif is_self_reply:
                tweet_type = "self_reply"
            else:
                tweet_type = "original"

            entities = {}
            ent_obj = getattr(tweet, "entities", None)
            if ent_obj:
                raw = ent_obj if isinstance(ent_obj, dict) else vars(ent_obj)
                if raw.get("urls"):
                    entities["urls"] = [
                        u.get("expanded_url", u.get("url", "")) if isinstance(u, dict)
                        else getattr(u, "expanded_url", "")
                        for u in raw["urls"]
                    ]

            all_tweets.append({
                "id": str(tweet.id),
                "text": text,
                "time": kst_time.strftime("%H:%M"),
                "rt_at": kst_time.isoformat(),
                "rt_author": rt_author,
                "entities": entities,
                "tweet_type": tweet_type,
            })

        next_token = resp.meta.get("next_token") if resp.meta else None
        if not next_token:
            break
        pagination_token = next_token

    return all_tweets


# 하위 호환성
def fetch_my_rts(client: tweepy.Client, user_id: str, start: datetime, end: datetime) -> list:
    return fetch_my_tweets(client, user_id, start, end)
