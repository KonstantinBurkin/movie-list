# Branch Protection Setup Guide

Configure branch protection rules to ensure all tests pass before merging PRs.

## Required Setup (GitHub UI)

Follow these steps to protect your `main` branch:

### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Branches** in the left sidebar
4. Under "Branch protection rules", click **Add rule**

### 2. Configure Protection Rules

#### Branch Name Pattern
```
main
```

#### Protection Settings to Enable

**✅ Require a pull request before merging**
- [x] Require approvals: **1** (or more if you have a team)
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require review from Code Owners (optional)

**✅ Require status checks to pass before merging**
- [x] Require branches to be up to date before merging
- **Select these status checks:**
  - `PR Validation`
  - `Dependency Security Check`
  - `Ready to Merge`
  - `test (3.12)` - from test.yml workflow
  - `test (3.13)` - from test.yml workflow

**✅ Require conversation resolution before merging**
- [x] All conversations on code must be resolved

**✅ Require signed commits** (optional but recommended)
- [x] Require signed commits

**✅ Require linear history** (optional)
- [x] Prevent merge commits (enforces squash or rebase)

**✅ Do not allow bypassing the above settings**
- [x] Include administrators

**✅ Restrict who can push to matching branches** (optional)
- Only allow specific users/teams to push directly

**✅ Allow force pushes**
- [ ] Leave unchecked (don't allow force pushes)

**✅ Allow deletions**
- [ ] Leave unchecked (don't allow branch deletion)

### 3. Save Settings

Click **Create** to save the branch protection rule.

## Automated Setup via GitHub CLI

Alternatively, use GitHub CLI to configure programmatically:

```bash
# Install GitHub CLI if not already installed
brew install gh  # macOS
# or: sudo apt install gh  # Linux

# Authenticate
gh auth login

# Create branch protection rule
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]=PR Validation \
  -f required_status_checks[contexts][]=Ready to Merge \
  -f required_status_checks[contexts][]=test (3.12) \
  -f required_status_checks[contexts][]=test (3.13) \
  -f required_pull_request_reviews[dismiss_stale_reviews]=true \
  -f required_pull_request_reviews[require_code_owner_reviews]=false \
  -f required_pull_request_reviews[required_approving_review_count]=1 \
  -f enforce_admins=true \
  -f required_conversation_resolution=true \
  -f allow_force_pushes=false \
  -f allow_deletions=false
```

## Verification

After setup, verify protection is active:

### Via GitHub UI
1. Go to **Settings** → **Branches**
2. You should see the `main` branch listed under "Branch protection rules"
3. Click **Edit** to review settings

### Via GitHub CLI
```bash
gh api repos/:owner/:repo/branches/main/protection
```

## Testing Branch Protection

### Create a Test PR

```bash
# Create a new branch
git checkout -b test-branch-protection

# Make a change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test: branch protection"
git push origin test-branch-protection

# Create PR via GitHub CLI
gh pr create --title "Test: Branch Protection" --body "Testing branch protection rules"
```

### Verify Protection Works

1. **Try to push directly to main** - Should be blocked:
   ```bash
   git checkout main
   echo "test" >> test.txt
   git add test.txt
   git commit -m "test"
   git push origin main
   # Should fail with: "protected branch hook declined"
   ```

2. **Create PR without passing tests** - Should show checks pending
3. **Try to merge before checks pass** - Merge button should be disabled
4. **Wait for checks to pass** - Merge button becomes enabled

## What Happens When You Create a PR

With branch protection enabled, here's the workflow:

```
1. Developer creates PR
   ↓
2. GitHub triggers PR-checks.yml workflow
   ↓
3. Workflow runs:
   ✓ Code formatting check (black)
   ✓ Linting (flake8)
   ✓ Unit tests (pytest)
   ✓ Coverage check (must be ≥65%)
   ✓ Dependency security scan
   ✓ Import verification
   ↓
4. Status checks report to PR:
   • PR Validation: ✅ or ❌
   • Dependency Security Check: ✅ or ❌
   • Ready to Merge: ✅ or ❌
   ↓
5. If ALL checks pass:
   • Merge button becomes enabled ✅
   • PR can be merged
   
   If ANY check fails:
   • Merge button disabled ❌
   • Developer must fix issues and push new commits
   • Checks run again automatically
```

## Status Checks Details

| Check Name | What It Does | Blocks Merge? |
|------------|--------------|---------------|
| **PR Validation** | Runs tests, linting, formatting | ✅ Yes |
| **Dependency Security Check** | Scans for vulnerabilities | ✅ Yes |
| **Ready to Merge** | Confirms all checks passed | ✅ Yes |
| **test (3.12)** | Tests on Python 3.12 | ✅ Yes |
| **test (3.13)** | Tests on Python 3.13 | ✅ Yes |
| **PR Size Check** | Warns if PR is too large | ⚠️ No (warning only) |

## Bypassing Protection (Emergency)

If you absolutely must merge without passing checks (not recommended):

### Temporary Disable
1. Go to **Settings** → **Branches**
2. Click **Edit** on the main protection rule
3. Temporarily uncheck **Require status checks to pass**
4. Merge your PR
5. **IMPORTANT**: Re-enable the protection immediately

### Admin Override
Admins with bypass permission can:
1. Click **Merge** dropdown
2. Select **Merge without waiting for requirements**
3. Confirm override

⚠️ **Warning**: Only use in genuine emergencies. Every bypass weakens your code quality.

## Troubleshooting

### "Merge button disabled but checks passed"

**Cause**: Branch is not up to date with main

**Fix**:
```bash
git checkout your-branch
git pull origin main
git push origin your-branch
```

### "Status check never completes"

**Cause**: Workflow stuck or failed to start

**Fix**:
1. Check Actions tab for errors
2. Re-run failed checks
3. Push empty commit to trigger again:
   ```bash
   git commit --allow-empty -m "Trigger checks"
   git push
   ```

### "Required status check is missing"

**Cause**: Status check name in settings doesn't match workflow

**Fix**:
1. Go to a PR with completed checks
2. Note the exact status check names
3. Update branch protection settings with exact names

### "All checks pass but merge still disabled"

**Cause**: Missing review approval

**Fix**: Get required number of approvals from reviewers

## Best Practices

### ✅ Do's
- ✅ Always create PRs for changes
- ✅ Wait for all checks to pass
- ✅ Address reviewer comments
- ✅ Keep PRs small and focused
- ✅ Write descriptive PR titles and descriptions

### ❌ Don'ts
- ❌ Don't force push to PR branches (breaks CI)
- ❌ Don't bypass checks unless emergency
- ❌ Don't merge your own PRs without review
- ❌ Don't commit directly to main
- ❌ Don't skip CI checks locally before pushing

## Workflow Example

```bash
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/my-feature

# 2. Make changes and commit
# ... make changes ...
git add .
git commit -m "feat: add my feature"

# 3. Run tests locally BEFORE pushing
pytest tests/ -v
black --check scripts --line-length=120
flake8 scripts

# 4. Push and create PR
git push origin feature/my-feature
gh pr create --title "Add my feature" --body "Description..."

# 5. Wait for CI checks (automatic)
# GitHub Actions runs all checks

# 6. Address review comments if any
# ... make changes ...
git add .
git commit -m "fix: address review comments"
git push

# 7. Merge when approved and checks pass
gh pr merge --squash --delete-branch
```

## Next Steps

After configuring branch protection:

1. ✅ Test by creating a PR
2. ✅ Share workflow with your team
3. ✅ Document any custom checks
4. ✅ Review and update protection rules quarterly

---

**Protection Level**: 🔒 **High**

With these settings, your `main` branch is protected from:
- Accidental direct pushes
- Merging broken code
- Merging code that fails tests
- Merging code with security vulnerabilities
- Merging code without review
