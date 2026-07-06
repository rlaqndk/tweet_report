from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from fetcher import fetch_my_tweets, get_user_id

KST = timezone(timedelta(hours=9))
START = datetime(2026, 4, 29, 7, 0, 0, tzinfo=KST)
END = datetime(2026, 4, 30, 7, 0, 0, tzinfo=KST)
USER_ID = "111"


def _make_resp(tweets, includes=None, next_token=None):
    resp = MagicMock()
    resp.data = tweets
    resp.includes = includes or {}
    resp.meta = {"next_token": next_token} if next_token else {}
    return resp


def _make_tweet(tweet_id, text, ref_types=None, in_reply_to_user_id=None, created_at="2026-04-29T10:00:00+00:00"):
    t = MagicMock()
    t.id = tweet_id
    t.text = text
    t.created_at = created_at
    t.note_tweet = None
    t.author_id = USER_ID
    t.in_reply_to_user_id = in_reply_to_user_id
    if ref_types:
        refs = []
        for rtype, rid in ref_types:
            r = MagicMock()
            r.type = rtype
            r.id = rid
            refs.append(r)
        t.referenced_tweets = refs
    else:
        t.referenced_tweets = []
    t.entities = None
    return t


def test_get_user_id():
    client = MagicMock()
    client.get_user.return_value.data.id = "123456"
    assert get_user_id(client, "testuser") == "123456"
    client.get_user.assert_called_once_with(username="testuser")


def test_fetch_no_data_returns_empty():
    client = MagicMock()
    client.get_users_tweets.return_value = _make_resp(None)
    result = fetch_my_tweets(client, USER_ID, START, END)
    assert result == []


def test_rt_is_collected():
    orig = MagicMock()
    orig.id = 999
    orig.text = "원본 RT 내용"
    orig.author_id = "999"
    orig.note_tweet = None

    orig_user = MagicMock()
    orig_user.id = 999
    orig_user.username = "origuser"

    tweet = _make_tweet("1", "RT @origuser: 원본 RT 내용", ref_types=[("retweeted", 999)])
    client = MagicMock()
    client.get_users_tweets.return_value = _make_resp(
        [tweet],
        includes={"tweets": [orig], "users": [orig_user]},
    )

    result = fetch_my_tweets(client, USER_ID, START, END)
    assert len(result) == 1
    assert result[0]["tweet_type"] == "rt"
    assert result[0]["text"] == "원본 RT 내용"
    assert result[0]["rt_author"] == "origuser"


def test_original_post_is_collected():
    tweet = _make_tweet("2", "내가 직접 쓴 게시글")
    client = MagicMock()
    client.get_users_tweets.return_value = _make_resp([tweet])

    result = fetch_my_tweets(client, USER_ID, START, END)
    assert len(result) == 1
    assert result[0]["tweet_type"] == "original"
    assert result[0]["text"] == "내가 직접 쓴 게시글"


def test_self_reply_is_collected():
    # 본인 트윗(222)에 달린 답글
    tweet = _make_tweet("3", "추가 설명입니다", ref_types=[("replied_to", 222)], in_reply_to_user_id=USER_ID)
    client = MagicMock()
    client.get_users_tweets.return_value = _make_resp([tweet])

    result = fetch_my_tweets(client, USER_ID, START, END)
    assert len(result) == 1
    assert result[0]["tweet_type"] == "self_reply"


def test_reply_to_others_is_excluded():
    # 다른 사람(OTHER) 트윗에 달린 대화 답글
    tweet = _make_tweet("4", "대화 답글", ref_types=[("replied_to", 333)], in_reply_to_user_id="OTHER")
    client = MagicMock()
    client.get_users_tweets.return_value = _make_resp([tweet])

    result = fetch_my_tweets(client, USER_ID, START, END)
    assert result == []


def test_multiple_types_collected_together():
    rt_tweet = _make_tweet("5", "RT @a: x", ref_types=[("retweeted", 888)])
    orig_tweet = _make_tweet("6", "내 게시글")
    self_reply = _make_tweet("7", "내 추가설명", ref_types=[("replied_to", 666)], in_reply_to_user_id=USER_ID)
    other_reply = _make_tweet("8", "대화", ref_types=[("replied_to", 777)], in_reply_to_user_id="SOMEONE")

    orig_expanded = MagicMock()
    orig_expanded.id = 888
    orig_expanded.text = "x"
    orig_expanded.author_id = "999"
    orig_expanded.note_tweet = None

    client = MagicMock()
    client.get_users_tweets.return_value = _make_resp(
        [rt_tweet, orig_tweet, self_reply, other_reply],
        includes={"tweets": [orig_expanded], "users": []},
    )

    result = fetch_my_tweets(client, USER_ID, START, END)
    assert len(result) == 3
    types = {t["tweet_type"] for t in result}
    assert types == {"rt", "original", "self_reply"}
