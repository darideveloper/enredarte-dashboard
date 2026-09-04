#!/bin/sh
# guard.sh — testing-contract gate (single source of truth)
# Fails if pytest is reintroduced. See openspec/specs/testing-contract/spec.md
set -eu

fail=0
say_fail() { echo "FAIL: $1" >&2; fail=1; }

# (a) Dependency ban: requirements*.txt
for f in requirements.txt requirements-dev.txt; do
  if [ -f "$f" ] && grep -qi "pytest" "$f" 2>/dev/null; then
    say_fail "pytest found in $f"
    grep -in "pytest" "$f" >&2 || true
  fi
done

# pip freeze fallback chain
pip_freeze=""
for cand in "venv/bin/pip freeze" ".venv/bin/pip freeze" "pip freeze" "python -m pip freeze" "python3 -m pip freeze"; do
  # split cand into command
  # try venv/bin/pip first if exists as file
  if echo "$cand" | grep -q "venv/bin/pip"; then
    bin=$(echo "$cand" | awk '{print $1}')
    if [ -x "$bin" ]; then
      if pip_freeze=$($bin freeze 2>/dev/null); then
        break
      fi
    fi
  elif echo "$cand" | grep -q ".venv/bin/pip"; then
    bin=$(echo "$cand" | awk '{print $1}')
    if [ -x "$bin" ]; then
      if pip_freeze=$($bin freeze 2>/dev/null); then
        break
      fi
    fi
  else
    # plain pip or python -m pip
    if pip_freeze=$(sh -c "$cand" 2>/dev/null); then
      # got output, use it if non-empty attempt
      # if command succeeded, break (even if empty output means no pytest)
      break
    fi
  fi
done

if echo "$pip_freeze" | grep -qi "pytest" 2>/dev/null; then
  say_fail "pytest found in pip freeze"
  echo "$pip_freeze" | grep -i "pytest" >&2 || true
fi

# (b) File ban: conftest.py / pytest.ini / .pytest.ini anywhere (except allowlist)
# use find, exclude .git, .venv, venv, openspec/changes/archive
found_files=$(find . \( -path "./.git/*" -o -path "./.venv/*" -o -path "./venv/*" -o -path "./openspec/changes/archive/*" -o -path "./.opencode/node_modules/*" \) -prune -o \( -name "conftest.py" -o -name "pytest.ini" -o -name ".pytest.ini" \) -print 2>/dev/null || true)
if [ -n "$found_files" ]; then
  say_fail "banned file found (conftest.py/pytest.ini/.pytest.ini)"
  echo "$found_files" >&2
fi

# setup.cfg / pyproject.toml tool config
if [ -f "setup.cfg" ] && grep -q "\[tool:pytest" setup.cfg 2>/dev/null; then
  say_fail "banned [tool:pytest] in setup.cfg"
  grep -n "\[tool:pytest" setup.cfg >&2 || true
fi
if [ -f "pyproject.toml" ] && grep -q "\[tool.pytest" pyproject.toml 2>/dev/null; then
  say_fail "banned [tool.pytest] in pyproject.toml"
  grep -n "\[tool.pytest" pyproject.toml >&2 || true
fi

# (c) Import ban: anchored import/from/@pytest in *.py
# exclude archive, .venv, venv, .git
import_hits=$(grep -R --include="*.py" -nE "^\s*(import pytest|from pytest|@pytest\.)" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=venv --exclude-dir=node_modules . 2>/dev/null | grep -v "openspec/changes/archive/" || true)
if [ -n "$import_hits" ]; then
  say_fail "banned pytest import/decorator in *.py"
  echo "$import_hits" >&2
fi

# (d) Task lint: pytest command in new tasks.md outside archive
# Only flag actual command invocations (e.g. `pytest foo`, `python -m pytest`, `pytest -k`),
# not narrative checks like "grep -i pytest" or "banning pytest".
raw_task_hits=$(grep -R -nE "python -m pytest|pytest -k|(^| )pytest( [A-Za-z0-9_/\.-]|$)" openspec/changes --include="tasks.md" 2>/dev/null | grep -v "openspec/changes/archive/" || true)
# filter out verification/narrative lines that mention pytest but don't invoke it
task_hits=$(echo "$raw_task_hits" | grep -v -i "banning" | grep -v -i "banned" | grep -v "grep.*pytest" | grep -v "no pytest" | grep -v "import.*pytest" | grep -v "contains no instruction" || true)
if [ -n "$task_hits" ]; then
  say_fail "pytest command in openspec/changes/*/tasks.md (non-archive)"
  echo "$task_hits" >&2
fi

if [ "$fail" -ne 0 ]; then
  echo "test-contract-guard FAILED" >&2
  exit 1
fi

echo "test-contract-guard OK"
