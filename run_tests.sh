#!/usr/bin/env bash
# Every gate in the repo. No hardware, no network, no server.
#
#   ./run_tests.sh            all of them
#   ./run_tests.sh scene      just tests/test_scene.py
set -uo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

if [ $# -gt 0 ]; then
    FILES=()
    for name in "$@"; do FILES+=("tests/test_${name#test_}.py"); done
else
    FILES=(tests/test_*.py)
fi

fail=0
for f in "${FILES[@]}"; do
    echo "=== $f"
    # The generators narrate to stdout; the gate's own lines are what matters.
    "$PY" "$f" 2>&1 | grep -v '^Pipeline:\|^Period:\|^Generating\|^Reparameteriz\|^Path length' || fail=1
done
exit $fail
