#!/bin/sh
set -eu
python -m scripts.migrate
if [ "$SEED_DEMO" = true ]; then
  python -m scripts.seed_demo || echo '演示数据初始化失败，可手动重试' >&2
fi
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
