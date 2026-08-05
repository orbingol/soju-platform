#!/bin/sh
# Start nginx, print the host URL once the site answers, then wait.
set -eu

PORT="${SOJU_WEB_PORT:-8080}"

nginx -g 'daemon off;' &
pid=$!

shutdown() {
    kill -TERM "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    exit 0
}
trap shutdown TERM INT

i=0
while [ "$i" -lt 120 ]; do
    if ! kill -0 "$pid" 2>/dev/null; then
        wait "$pid"
        exit $?
    fi
    # Succeeds only when upstream web responds (nginx returns 5xx while web is down).
    if wget -q -O /dev/null http://127.0.0.1/ 2>/dev/null; then
        printf '\n  Soju: http://localhost:%s\n\n' "$PORT"
        break
    fi
    i=$((i + 1))
    sleep 1
done

wait "$pid"
