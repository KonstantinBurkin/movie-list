#!/bin/bash
# Auto-fix code quality issues

cd "$(dirname "$0")/.."

source .venv/bin/activate 2>/dev/null || true

echo "════════════════════════════════════════════"
echo "🔧 Auto-Fixing Code Quality Issues"
echo "════════════════════════════════════════════"

echo ""
echo "✨ Formatting with black..."
black scripts --line-length=120

echo ""
echo "📦 Sorting imports..."
if command -v isort &> /dev/null; then
    isort scripts
else
    echo "⚠️  isort not installed (optional)"
    echo "   Install: pip install isort"
fi

echo ""
echo "════════════════════════════════════════════"
echo "✅ Auto-fixes applied!"
echo "════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Run './scripts/lint.sh' to check for remaining issues"
echo "  2. Manually fix any remaining flake8 errors"
echo "  3. Run 'pytest tests/' to verify tests pass"
