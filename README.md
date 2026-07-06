# tweet_report

X(Twitter) 투자 정보 자동 수집·분류 파이프라인.

매일 아침 07:00 KST, 지정 계정들의 전날 활동을 수집한다.
15개 섹터로 자동 분류해 마크다운 리포트를 생성한다.
GitHub Actions가 전 과정을 무인 실행하고 결과를 커밋한다.

## 문제

투자 정보가 트위터 타임라인에 흩어져 있었다.
RT한 글을 다시 찾는 데 매일 시간을 썼다.
종목·섹터별로 모아 보는 수단이 없었다.

## 설계

```
X API ─→ fetcher.py ─→ classifier.py ─→ reporter.py ─→ reports/
              │              │                │
        RT/원본/답글      키워드 기반        섹터별 정렬
        구분 수집        15개 섹터 분류     md + json 출력
```

| 모듈 | 역할 |
|---|---|
| `fetcher.py` | X API v2 페이지네이션 수집. RT, 원본, 자기답글 구분 |
| `classifier.py` | config 키워드 사전으로 섹터 다중 분류 |
| `reporter.py` | 섹터별 마크다운 리포트, 유형별 통계 생성 |
| `tweet_report.py` | 엔트리포인트. 설정 로드, 파이프라인 오케스트레이션 |

### 분류 섹터 (15개)

반도체 4개 세부 섹터, AI 2개, 로보틱스, 바이오, 에너지,
금융 2개, 테크 2개, 기업이슈, 기타.
키워드 사전은 `config.yaml`에서 관리. 코드 수정 없이 확장 가능.

### 자동화

GitHub Actions cron이 매일 22:00 UTC 실행.
리포트를 `reports/`에 자동 커밋. 수동 실행 버튼 지원.

## 결과

- 일 평균 100건 이상 수집·분류 (예: 2026-05-09 총 121건)
- 리포트 확인 시간: 타임라인 재탐색 수십 분 → 아침 5분
- 리포트는 LLM 분석용 프롬프트 헤더 포함. 바로 AI 분석에 투입 가능

## 실행

```bash
pip install -r requirements.txt
export BEARER_TOKEN="your-x-api-bearer-token"
python tweet_report.py
```

GitHub Actions 사용 시 `Settings > Secrets > Actions`에
`BEARER_TOKEN` 등록.

## 테스트

```bash
pytest tests/
```

fetcher, classifier, reporter 각 모듈 단위 테스트 포함.
