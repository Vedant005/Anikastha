#!/bin/sh
set -e

echo "=== Initializing PR-Sentinel Backend Service ==="

# 1. Start embedded Redis if REDIS_URL points to localhost or is empty
case "$REDIS_URL" in
  ""|*localhost*|*127.0.0.1*)
    if command -v redis-server >/dev/null 2>&1; then
      echo "[Startup] Starting embedded redis-server on port 6379..."
      redis-server --daemonize yes
    else
      echo "[Startup] Warning: redis-server command not found, relying on external REDIS_URL."
    fi
    ;;
  *)
    echo "[Startup] Using external Redis configuration."
    ;;
esac

# 2. Apply Database Migrations automatically
echo "[Startup] Applying database migrations via Alembic..."
alembic upgrade head || echo "[Startup] Warning: Alembic upgrade finished with notice."

# 3. Start ARQ Background Worker in background (unless explicitly disabled)
if [ "$RUN_WORKER" != "false" ]; then
    echo "[Startup] Starting ARQ background review worker..."
    arq app.worker.worker.WorkerSettings &
    WORKER_PID=$!
    echo "[Startup] ARQ worker running with PID: $WORKER_PID"
fi

# 4. Start FastAPI server in foreground to bind Render's dynamic $PORT
echo "[Startup] Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
