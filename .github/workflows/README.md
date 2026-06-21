# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for continuous integration and testing.

## Workflows

### `test.yml` - Main Test Pipeline

Runs on every push to `main` and on all pull requests.

**Jobs:**

1. **test** - Unit and integration tests
   - Runs on Python 3.12 and 3.13
   - Linting with flake8
   - Code formatting check with black
   - Test execution with pytest
   - Code coverage reporting with Codecov

2. **integration-test** - Integration verification
   - Verifies imports work correctly
   - Checks data file structure
   - Validates recommendation script (if API key available)

## Setup Requirements

### Required Secrets

Add these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

1. **`TMDB_API_KEY`** (Required)
   - Your TMDB API key for testing
   - Get from: https://www.themoviedb.org/settings/api
   - Used in integration tests

2. **`OMDB_API_KEY`** (Optional)
   - Your OMDB API key
   - Used if you have OMDB integration tests

3. **`CODECOV_TOKEN`** (Optional)
   - Token for uploading coverage reports to Codecov
   - Get from: https://codecov.io/
   - Only needed if you want coverage tracking

### How to Add Secrets

```bash
# Via GitHub Web UI:
# 1. Go to your repository
# 2. Settings → Secrets and variables → Actions
# 3. Click "New repository secret"
# 4. Add each secret with its value

# Or via GitHub CLI:
gh secret set TMDB_API_KEY
# Paste your API key when prompted

gh secret set OMDB_API_KEY
# Paste your API key when prompted

gh secret set CODECOV_TOKEN
# Paste your Codecov token when prompted
```

## Test Coverage

Coverage reports are automatically generated and can be:
- Viewed in the GitHub Actions logs
- Uploaded to Codecov (if token is configured)
- Generated locally with: `pytest --cov=scripts --cov-report=html`

## Local Testing

Run the same tests locally before pushing:

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock flake8 black

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=scripts --cov-report=term-missing

# Check code formatting
black --check scripts --line-length=120

# Lint code
flake8 scripts --max-line-length=127
```

## Badges

Add these badges to your README.md:

```markdown
![Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/YOUR_REPO)
```

Replace `YOUR_USERNAME` and `YOUR_REPO` with your actual values.

## Troubleshooting

### Tests fail with "TMDB_API_KEY not set"

Add your TMDB API key to GitHub secrets (see above).

### Integration tests skipped

This is normal if TMDB_API_KEY secret is not configured. The tests will still pass.

### Coverage upload fails

This is non-fatal. If you don't have a Codecov account/token, the workflow will continue successfully.

### Black formatting fails

Run locally to fix:
```bash
black scripts --line-length=120
```

### Flake8 linting fails

Fix the reported issues or adjust `.flake8` configuration if needed.

## Continuous Deployment (Future)

To add deployment to your Streamlit dashboard:

1. Create `.github/workflows/deploy.yml`
2. Add deployment steps after tests pass
3. Configure Streamlit secrets in GitHub Actions
