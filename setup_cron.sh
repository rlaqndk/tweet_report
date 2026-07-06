#!/bin/bash
# 매일 오전 7시 KST(= 전날 22:00 UTC)에 tweet_report.py 실행
# KST = UTC+9, 오전 7시 KST = 전날 22:00 UTC

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(which python3)"
LOG="$SCRIPT_DIR/cron.log"

if [ -z "$PYTHON" ]; then
  echo "ERROR: python3 not found in PATH" >&2
  exit 1
fi

if [ ! -f "$SCRIPT_DIR/tweet_report.py" ]; then
  echo "ERROR: tweet_report.py not found at $SCRIPT_DIR" >&2
  exit 1
fi

CRON_JOB="0 22 * * * cd $SCRIPT_DIR && $PYTHON tweet_report.py >> $LOG 2>&1"

# 기존 tweet_report cron 제거 후 새로 추가
(crontab -l 2>/dev/null | grep -v "tweet_report.py"; echo "$CRON_JOB") | crontab -

echo "Cron job registered:"
echo "$CRON_JOB"
echo ""
echo "To verify: crontab -l"
