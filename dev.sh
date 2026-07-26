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
tmux select-window -t $SESSION_NAME:0
tmux attach -t $SESSION_NAME
