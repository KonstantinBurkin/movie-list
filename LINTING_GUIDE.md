# Linting & Code Quality Guide

How to check and fix code quality issues before committing.

## Quick Commands

### Check Everything (Before Committing)
```bash
# Activate virtual environment
source .venv/bin/activate

# Run all checks
pytest tests/ -v && \
flake8 scripts --max-line-length=127 && \
black --check scripts --line-length=120 && \
echo "✅ All checks passed!"
```

## Individual Tools

### 1. Black (Auto-Formatter) ✨

**Check if formatting is correct:**
```bash
black --check scripts --line-length=120
```

**Auto-fix formatting issues:**
```bash
black scripts --line-length=120
```

**Fix specific file:**
```bash
black scripts/tmdb_client.py --line-length=120
```

**What it fixes:**
- Indentation
- Line length
- Quotes (single vs double)
- Spacing around operators
- Trailing commas

### 2. Flake8 (Linter) 🔍

**Check for issues:**
```bash
# Check syntax errors only
flake8 scripts --count --select=E9,F63,F7,F82 --show-source

# Check all issues
flake8 scripts --count --max-line-length=127 --statistics
```

**Check specific file:**
```bash
flake8 scripts/tmdb_client.py --max-line-length=127
```

**Common error codes:**
- `E402` - Module import not at top
- `F401` - Imported but unused
- `E712` - Comparison to True (use `if var:`)
- `F541` - f-string missing placeholders
- `C901` - Function too complex
- `E501` - Line too long

**Flake8 CANNOT auto-fix** - you must fix manually

### 3. Autopep8 (Alternative Auto-Fixer)

**Install:**
```bash
pip install autopep8
```

**Auto-fix PEP8 issues:**
```bash
autopep8 --in-place --aggressive --aggressive scripts/
```

**Fix specific issues:**
```bash
autopep8 --in-place --select=E501,W293 scripts/tmdb_client.py
```

### 4. isort (Import Sorter)

**Install:**
```bash
pip install isort
```

**Check imports:**
```bash
isort --check-only scripts/
```

**Auto-fix imports:**
```bash
isort scripts/
```

**Configure (pyproject.toml):**
```toml
[tool.isort]
profile = "black"
line_length = 120
```

## Common Linting Issues & Fixes

### Issue: E402 - Import not at top

**Error:**
```python
import sys
sys.path.append('something')
from mymodule import something  # E402 error here
```

**Fix Option 1 - Suppress:**
```python
import sys
sys.path.append('something')
from mymodule import something  # noqa: E402
```

**Fix Option 2 - Reorganize:**
```python
from mymodule import something
import sys
# Move path manipulation if possible
```

### Issue: F401 - Imported but unused

**Error:**
```python
from pathlib import Path  # F401: imported but unused
```

**Fix:**
```python
# Just remove it
```

### Issue: E712 - Comparison to True

**Error:**
```python
if variable == True:  # E712
```

**Fix:**
```python
if variable:  # or: if variable is True:
```

### Issue: F541 - f-string missing placeholders

**Error:**
```python
print(f"Hello world")  # No {} placeholders
```

**Fix:**
```python
print("Hello world")  # Remove f
# or
print(f"Hello {name}")  # Add placeholder
```

### Issue: E501 - Line too long

**Error:**
```python
some_very_long_function_call_with_many_parameters(param1, param2, param3, param4, param5)  # > 127 chars
```

**Fix:**
```python
some_very_long_function_call_with_many_parameters(
    param1, param2, param3, 
    param4, param5
)
```

### Issue: C901 - Function too complex

**Error:**
```python
def complex_function():  # C901: too many branches
    if ...:
        if ...:
            if ...:
                # too nested
```

**Fix Option 1 - Suppress (if necessary):**
Add to `.flake8`:
```ini
per-file-ignores =
    path/to/file.py:C901
```

**Fix Option 2 - Refactor:**
- Extract nested logic into helper functions
- Use early returns
- Simplify conditions

## Automated Workflow

### Create Pre-Commit Hook

**Install pre-commit:**
```bash
pip install pre-commit
```

**Create `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        args: [--line-length=120]
        language_version: python3.13

  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks:
      - id: flake8
        args: [--max-line-length=127]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black, --line-length=120]
```

**Install hooks:**
```bash
pre-commit install
```

**Now:** Every commit automatically runs checks!

### Manual Pre-Commit Check

**Run all checks without committing:**
```bash
pre-commit run --all-files
```

## IDE Integration

### VS Code

**Install extensions:**
1. Python (Microsoft)
2. Black Formatter
3. Flake8

**Settings (`.vscode/settings.json`):**
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=127"
  ],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": [
    "--line-length=120"
  ],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

**Settings → Editor → Code Style → Python:**
- Hard wrap at: 120
- Visual guides: 120

**Settings → Tools → Black:**
- ✅ Enable Black formatter
- Arguments: `--line-length=120`

**Settings → Editor → Inspections → Python:**
- ✅ Enable PEP 8 coding style violation
- Line length: 127

## CI/CD Checks

These run automatically on GitHub Actions:

```bash
# What CI runs
black --check scripts --line-length=120
flake8 scripts --count --select=E9,F63,F7,F82 --show-source
flake8 scripts --count --max-complexity=10 --max-line-length=127
pytest tests/ -v --cov=scripts --cov-fail-under=65
```

## Quick Fix Workflow

**When you get linting errors:**

1. **Run checks locally:**
   ```bash
   source .venv/bin/activate
   flake8 scripts --show-source
   ```

2. **Auto-fix what you can:**
   ```bash
   black scripts --line-length=120
   isort scripts
   autopep8 --in-place --aggressive scripts/
   ```

3. **Fix remaining issues manually:**
   - Look at flake8 output
   - Fix one error at a time
   - Re-run flake8 to verify

4. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

5. **Commit:**
   ```bash
   git add .
   git commit -m "fix: resolve linting issues"
   ```

## Useful Scripts

### Create `lint.sh`:
```bash
#!/bin/bash
# Run all linting checks

echo "🔍 Running flake8..."
flake8 scripts --max-line-length=127 || exit 1

echo "✨ Running black..."
black --check scripts --line-length=120 || exit 1

echo "🧪 Running tests..."
pytest tests/ -v || exit 1

echo "✅ All checks passed!"
```

### Create `fix.sh`:
```bash
#!/bin/bash
# Auto-fix what can be fixed

echo "✨ Formatting with black..."
black scripts --line-length=120

echo "📦 Sorting imports..."
isort scripts

echo "🔧 Fixing PEP8 issues..."
autopep8 --in-place --aggressive scripts/

echo "✅ Auto-fixes applied! Run 'flake8 scripts' to check remaining issues."
```

**Make executable:**
```bash
chmod +x lint.sh fix.sh
```

**Use:**
```bash
./fix.sh  # Auto-fix
./lint.sh # Check
```

## Configuration Files

### `.flake8`
```ini
[flake8]
max-line-length = 127
exclude = .git,__pycache__,.venv,venv
ignore = E203,W503,E501
per-file-ignores =
    __init__.py:F401
    */collaborative_filtering.py:C901
```

### `pyproject.toml`
```toml
[tool.black]
line-length = 120
target-version = ['py312', 'py313']

[tool.isort]
profile = "black"
line_length = 120

[tool.pytest.ini_options]
addopts = "-v --tb=short"
```

## Troubleshooting

### "flake8: command not found"

**Fix:**
```bash
source .venv/bin/activate
pip install flake8
```

### "black: command not found"

**Fix:**
```bash
source .venv/bin/activate
pip install black
```

### "Checks pass locally but fail in CI"

**Cause:** Different versions

**Fix:**
```bash
pip install -r requirements.txt
# Ensure versions match CI
```

### "Too many errors to fix manually"

**Fix:**
```bash
# Auto-fix most issues
black scripts --line-length=120
autopep8 --in-place --aggressive --aggressive scripts/

# Then manually fix remaining
flake8 scripts --show-source
```

## Best Practices

1. **Run checks before committing:**
   ```bash
   ./lint.sh
   ```

2. **Auto-format regularly:**
   ```bash
   black scripts --line-length=120
   ```

3. **Fix errors incrementally:**
   - Don't let them pile up
   - Fix as you write code

4. **Use IDE integration:**
   - Format on save
   - Real-time linting

5. **Understand errors:**
   - Don't just suppress with `# noqa`
   - Learn why it's an issue

## Summary

| Tool | Purpose | Can Auto-Fix? |
|------|---------|---------------|
| **black** | Code formatting | ✅ Yes |
| **flake8** | Linting & style | ❌ No |
| **autopep8** | PEP8 fixes | ✅ Yes |
| **isort** | Import sorting | ✅ Yes |
| **pytest** | Tests | ❌ No |

**Recommended workflow:**
1. Write code
2. Save (auto-format if IDE configured)
3. Run: `black scripts && flake8 scripts`
4. Fix any remaining flake8 errors
5. Run: `pytest tests/`
6. Commit

---

**Quick Reference:**
```bash
# Check everything
flake8 scripts && black --check scripts && pytest tests/

# Fix everything possible
black scripts && isort scripts && autopep8 --in-place scripts/

# Check what CI will check
flake8 scripts --max-line-length=127
black --check scripts --line-length=120
pytest tests/ -v --cov=scripts
```
