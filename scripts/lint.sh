#!/bin/bash
# Check code quality (like CI does)

set -e

echo "════════════════════════════════════════════"
echo "🔍 Running Code Quality Checks"
echo "════════════════════════════════════════════"

cd "$(dirname "$0")/.."

source .venv/bin/activate 2>/dev/null || true

echo ""
echo "1️⃣  Checking for syntax errors..."
flake8 scripts --count --select=E9,F63,F7,F82 --show-source --statistics

echo ""
echo "2️⃣  Checking code quality..."
flake8 scripts --count --max-complexity=10 --max-line-length=127 --statistics

echo ""
echo "3️⃣  Checking import sorting..."
isort scripts --check-only --diff

echo ""
echo "4️⃣  Running tests..."
pytest tests/ -v --tb=short

echo ""
echo "════════════════════════════════════════════"
echo "✅ All checks passed!"
echo "════════════════════════════════════════════"
