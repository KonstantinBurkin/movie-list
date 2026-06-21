# CI/CD Setup Guide

Complete guide for setting up Continuous Integration and Deployment for the movie recommendation system.

## ✅ What's Already Set Up

- ✅ GitHub Actions workflow (`.github/workflows/test.yml`)
- ✅ 24 unit tests with pytest
- ✅ Code coverage tracking (69% coverage)
- ✅ Linting with flake8
- ✅ Code formatting with black
- ✅ Test fixtures and mocks

## 🔒 Branch Protection (PR Checks Before Merge)

The CI/CD system runs automatically on **every pull request** before allowing merge.

### Enable Branch Protection

**Option 1: GitHub UI** (Recommended)

1. Go to your repository → **Settings** → **Branches**
2. Click **Add rule** under "Branch protection rules"
3. Branch name: `main`
4. Enable these settings:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Select: `PR Validation`, `Ready to Merge`, `test (3.12)`, `test (3.13)`
   - ✅ Require conversation resolution before merging
   - ✅ Do not allow bypassing the above settings
5. Click **Create**

**Option 2: GitHub CLI**

```bash
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]=PR Validation \
  -f required_status_checks[contexts][]=Ready to Merge \
  -f required_pull_request_reviews[required_approving_review_count]=1 \
  -f enforce_admins=true
```

See detailed guide: [.github/BRANCH_PROTECTION.md](.github/BRANCH_PROTECTION.md)

## 🚀 Quick Setup (GitHub Actions)

### Step 1: Add GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value | Required? |
|-------------|-------|-----------|
| `TMDB_API_KEY` | Your TMDB API key | ✅ Yes |
| `OMDB_API_KEY` | Your OMDB API key | Optional |
| `CODECOV_TOKEN` | Codecov upload token | Optional |

**Get TMDB API Key**: https://www.themoviedb.org/settings/api

### Step 2: Push Your Code

```bash
git add .
git commit -m "Add CI/CD pipeline and tests"
git push origin main
```

### Step 3: Verify GitHub Actions

1. Go to your repository on GitHub
2. Click **Actions** tab
3. You should see the "Tests" workflow running
4. Wait for it to complete (usually ~2-3 minutes)

## 📊 Test Coverage

Current coverage: **69%**

| Module | Coverage |
|--------|----------|
| `tmdb_client.py` | 78% |
| `collaborative_filtering.py` | 84% |
| `generate_recommendations.py` | 78% |
| `streamlit_app.py` | 0% (not tested) |

## 🧪 Running Tests Locally

### Install Test Dependencies

```bash
source .venv/bin/activate
pip install pytest pytest-cov pytest-mock flake8 black
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage Report

```bash
pytest tests/ -v --cov=scripts --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Test File

```bash
pytest tests/test_tmdb_client.py -v
pytest tests/test_collaborative_filtering.py -v
pytest tests/test_generate_recommendations.py -v
```

### Lint Code

```bash
# Check for syntax errors
flake8 scripts --count --select=E9,F63,F7,F82 --show-source

# Full linting
flake8 scripts --max-line-length=127
```

### Format Code

```bash
# Check formatting
black --check scripts --line-length=120

# Auto-format
black scripts --line-length=120
```

## 🔄 GitHub Actions Workflow

The workflow runs on:
- Push to `main` branch
- Pull requests to `main`

### Jobs

**1. test** (runs on Python 3.12 and 3.13)
- Install dependencies
- Lint with flake8
- Check formatting with black
- Run pytest with coverage
- Upload coverage to Codecov (optional)

**2. integration-test**
- Verify data files exist
- Test imports
- Dry run recommendation script (if API key available)

## 📝 Test Structure

```
tests/
├── __init__.py
├── test_tmdb_client.py              # TMDB API client tests (9 tests)
├── test_collaborative_filtering.py  # ML model tests (11 tests)
└── test_generate_recommendations.py # CLI script tests (4 tests)
```

### Test Categories

**Unit Tests**:
- `test_tmdb_client.py` - API client, movie formatting, genre mapping
- `test_collaborative_filtering.py` - Model training, feature extraction, scoring

**Integration Tests**:
- `test_generate_recommendations.py` - End-to-end recommendation generation

## 🛠️ Adding New Tests

### Example Test

```python
# tests/test_my_feature.py
import pytest
from scripts.my_module import my_function

def test_my_function():
    """Test my function does what it should."""
    result = my_function("input")
    assert result == "expected_output"

@pytest.fixture
def sample_data():
    """Create sample test data."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data["key"] == "value"
```

Run new tests:
```bash
pytest tests/test_my_feature.py -v
```

## 🔐 Security Best Practices

### ✅ Do's
- ✅ Store API keys in GitHub Secrets
- ✅ Never commit `.env` files
- ✅ Use environment variables for credentials
- ✅ Add `.env` to `.gitignore`

### ❌ Don'ts
- ❌ Don't hardcode API keys in code
- ❌ Don't commit sensitive data
- ❌ Don't expose secrets in logs

## 📈 Improving Coverage

Current gaps:
- `streamlit_app.py` - 0% (not tested)
- Error handling paths - partially covered
- Edge cases - some missing

To improve:
1. Add tests for streamlit app
2. Test error scenarios
3. Add integration tests with real API (marked as `@pytest.mark.integration`)

## 🐛 Troubleshooting

### Tests fail locally but pass in CI

**Cause**: Different Python versions or dependencies

**Fix**:
```bash
# Match CI environment
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

### "TMDB_API_KEY not set" in CI

**Cause**: Secret not added to GitHub

**Fix**: Add `TMDB_API_KEY` to GitHub Secrets (see Step 1 above)

### Coverage upload fails

**Cause**: No Codecov token

**Fix**: This is non-fatal. Add `CODECOV_TOKEN` secret or ignore.

### Import errors in tests

**Cause**: Path issues

**Fix**: Tests use `sys.path.append()` to find modules. Verify paths are correct.

## 🚀 Advanced: Pre-commit Hooks

Install pre-commit hooks to run tests before committing:

```bash
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        language_version: python3.13
        args: [--line-length=120]

  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks:
      - id: flake8
        args: [--max-line-length=127]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [tests/, -v]
EOF

# Install hooks
pre-commit install
```

Now tests run automatically before each commit!

## 📊 Badges

Add these to your `README.md`:

```markdown
![Tests](https://github.com/YOUR_USERNAME/movie-list/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/movie-list/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/movie-list)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
```

## 🎯 Next Steps

1. **Merge to Main**: Your CI/CD is ready! Merge your branch.
2. **Monitor**: Check GitHub Actions tab after merging
3. **Iterate**: Add more tests as you add features
4. **Deploy**: Consider adding CD for Streamlit deployment

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [GitHub Actions docs](https://docs.github.com/en/actions)
- [flake8 rules](https://flake8.pycqa.org/en/latest/user/error-codes.html)
- [black formatting](https://black.readthedocs.io/)
- [Codecov](https://about.codecov.io/)

---

**Setup Complete!** Your recommendation system now has:
- ✅ Automated testing on every push
- ✅ Code quality checks
- ✅ Coverage reporting
- ✅ Multi-version Python testing (3.12, 3.13)
