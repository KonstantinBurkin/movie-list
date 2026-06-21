#!/bin/bash
# Auto-fix code quality issues

cd "$(dirname "$0")/.."

source .venv/bin/activate 2>/dev/null || true

echo "════════════════════════════════════════════"
echo "🔧 Auto-Fixing Code Quality Issues"
echo "════════════════════════════════════════════"

echo ""
echo "📦 Sorting imports with isort..."
isort scripts

echo ""
echo "════════════════════════════════════════════"
echo "✅ Auto-fixes applied!"
echo "════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Run './scripts/lint.sh' to check for remaining issues"
echo "  2. Manually fix any remaining flake8 errors"
echo "  3. Run 'pytest tests/' to verify tests pass"
