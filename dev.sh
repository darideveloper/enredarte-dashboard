#!/bin/bash

PROJECT_NAME=$(basename "$PWD")
SESSION_NAME="${PROJECT_NAME}_dev"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Session $SESSION_NAME already exists. Attaching..."
    tmux attach -t $SESSION_NAME
    exit 0
fi

portless proxy start
portless trust

PORT=8000
while ss -tuln | grep -q ":$PORT " ; do
    PORT=$((PORT+1))
done

VENV_CMD=""
[ -d "venv" ] && VENV_CMD="source venv/bin/activate && "
[ -d ".venv" ] && VENV_CMD="source .venv/bin/activate && "

tmux new-session -d -s $SESSION_NAME -n 'django' -c "$PWD" \
    "bash -c '${VENV_CMD}portless $PROJECT_NAME --app-port $PORT -- python manage.py runserver $PORT; read'"

# --- Cloudflare Tunnel (auto-start) ---
# SECURITY: The tunnel makes runserver publicly reachable over HTTPS.
# For dev-only use; consider Cloudflare Access (zero-trust) in front of
# the hostname so only you can reach it.
cf_env() { grep -E "^$1=" .env.dev 2>/dev/null | head -1 | cut -d= -f2-; }
CF_NAME="${CLOUDFLARE_TUNNEL_NAME:-$(cf_env CLOUDFLARE_TUNNEL_NAME)}"
CF_HOST="${CLOUDFLARE_TUNNEL_HOST:-$(cf_env CLOUDFLARE_TUNNEL_HOST)}"

if command -v cloudflared >/dev/null 2>&1 && [ -n "$CF_NAME" ] && [ -n "$CF_HOST" ]; then
  CF_ID=$(cloudflared tunnel list -o json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(t['id'] for t in d if t.get('name')=='$CF_NAME'))")
  CF_CRED="$HOME/.cloudflared/$CF_ID.json"
  CF_CONFIG="$HOME/.cloudflared/config-${PROJECT_NAME}.yml"
  cat > "$CF_CONFIG" <<YML
tunnel: $CF_NAME
credentials-file: $CF_CRED
ingress:
  - hostname: $CF_HOST
    service: http://localhost:$PORT
  - service: http_status:404
YML
  tmux new-window -n 'tunnel' -c "$PWD" \
    "bash -c 'cloudflared tunnel --config $CF_CONFIG run $CF_NAME; read'"
fi

tmux select-window -t $SESSION_NAME:0
tmux attach -t $SESSION_NAME
