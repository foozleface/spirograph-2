#!/bin/bash
PORT="${1:-8890}"
echo "http://127.0.0.1:${PORT}/"
exec python server.py --port "$PORT"
