#!/usr/bin/env bash
# trendminer 启动文件（外层 run/ 目录）
# 用法：
#   ./run/start.sh                # 使用 config/settings.yaml 的端口（默认 8770，被占用自动顺延）
#   ./run/start.sh --port 8899    # 指定端口
#   PORT=8899 ./run/start.sh      # 用环境变量指定端口
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PY="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3)"
fi

exec "$PY" "$PROJECT_ROOT/run/serve.py" "$@"
