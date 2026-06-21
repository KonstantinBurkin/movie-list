# Pull Request Workflow

Visual guide to the PR → Test → Merge workflow.

## 📋 Quick Reference

```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Make changes and test locally
pytest tests/ -v
black scripts --line-length=120
flake8 scripts

# 3. Commit and push
git add .
git commit -m "feat: your feature"
git push origin feature/your-feature

# 4. Create PR
gh pr create --title "Your Feature" --body "Description"

# 5. Wait for CI checks to pass (automatic)

# 6. Merge when approved
gh pr merge --squash --delete-branch
```

## 🔄 Full Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Developer Workflow                            │
└─────────────────────────────────────────────────────────────────┘

   Developer's Machine                    GitHub
   ═══════════════════                    ══════

1. Create branch
   git checkout -b
   feature/rec-algo
        │
        │
2. Write code
   scripts/*.py
        │
        │
3. Test locally ──────────────────┐
   pytest tests/ -v               │ (Optional but
   black --check scripts          │  recommended)
   flake8 scripts                 │
        │                         │
        │◄────────────────────────┘
        │
4. Commit & Push ─────────────────────────►  GitHub Repository
   git push origin                            │
   feature/rec-algo                           │
        │                                     │
        │                                     ▼
5. Create PR ─────────────────────────────►  Pull Request Created
   gh pr create                               │
        │                                     │
        │                                     ▼
        │                              ┌─────────────────┐
        │                              │ GitHub Actions  │
        │                              │    Triggered    │
        │                              └────────┬────────┘
        │                                       │
        │                              ┌────────▼─────────────────┐
        │                              │ pr-checks.yml workflow   │
        │                              │                          │
        │                              │ Jobs run in parallel:    │
        │                              │  1. PR Validation        │
        │                              │     ✓ Black formatting   │
        │                              │     ✓ Flake8 linting     │
        │                              │     ✓ Pytest tests       │
        │                              │     ✓ Coverage (≥65%)    │
        │                              │                          │
        │                              │  2. Dependency Check     │
        │                              │     ✓ Security scan      │
        │                              │                          │
        │                              │  3. PR Size Check        │
        │                              │     ⚠️  Size warning      │
        │                              │                          │
        │                              │  4. Ready to Merge       │
        │                              │     ✓ All checks pass    │
        │                              └────────┬─────────────────┘
        │                                       │
        │                              ┌────────▼─────────┐
        │                              │  Status Checks   │
        │                              │     Report       │
        │                              └────────┬─────────┘
        │                                       │
        │                              ┌────────▼──────────────────┐
        │                              │   All Checks Passed?      │
        │                              └────────┬──────────────────┘
        │                                       │
        │                              ┌────────▼─────┬────────────┐
        │                              │              │            │
        │                           ✅ YES          ❌ NO          │
        │                              │              │            │
        │                  ┌───────────▼────────┐    │            │
        │                  │ Merge Button       │    │            │
        │                  │ ENABLED ✅         │    │            │
        │                  │                    │    │            │
        │◄─────────────────┤ Ready for Review   │    │            │
        │   (Notification) │ & Merge            │    │            │
6. Review changes         └───────────┬────────┘    │            │
   Address comments                   │             │            │
        │                             │   ┌─────────▼──────────┐ │
        │                             │   │ Merge Button       │ │
        │                             │   │ DISABLED ❌        │ │
        │                             │   │                    │ │
        │                             │   │ Fix Issues and     │ │
        │◄────────────────────────────┼───┤ Push Again         │ │
        │   (Fix required)            │   └────────────────────┘ │
7. Fix issues (if needed)             │              │            │
   git commit --amend                 │              │            │
   git push --force-with-lease        │              │            │
        │                             │              │            │
        └─────────────────────────────┴──────────────┘            │
                                      │                           │
                                      │ (Checks re-run            │
                                      │  automatically)           │
                                      └───────────────────────────┘

8. Get approval (if required)
   Reviewer approves PR
        │
        │
9. Merge PR ──────────────────────────►  Merge to main
   gh pr merge --squash                   │
        │                                 │
        │                                 ▼
        │                          ┌─────────────────┐
        │                          │  test.yml       │
        │                          │  workflow runs  │
        │                          │  on main        │
        │                          └─────────────────┘
        │
        ▼
   Feature branch deleted
   (optional: --delete-branch)

═══════════════════════════════════════════════════════════════════
```

## 🎯 Status Check Details

When you create a PR, these checks run automatically:

### 1️⃣ PR Validation (REQUIRED ✅)

```yaml
Jobs:
  ✓ Black code formatting
  ✓ Flake8 linting (no syntax errors)
  ✓ Pytest test suite (all 24 tests)
  ✓ Code coverage ≥ 65%
  ✓ Import verification
  ✓ Data file check

Duration: ~2-3 minutes
Blocks Merge: YES
```

**What it checks:**
- Code follows black formatting (120 char line length)
- No linting errors (syntax, undefined vars, complexity)
- All unit tests pass
- Test coverage meets minimum threshold
- Critical imports work
- Required data files exist

### 2️⃣ Dependency Security Check (REQUIRED ✅)

```yaml
Jobs:
  ✓ Install dependencies
  ✓ Run safety check for vulnerabilities
  ✓ Report security issues

Duration: ~1-2 minutes
Blocks Merge: YES
```

**What it checks:**
- Known security vulnerabilities in dependencies
- Outdated packages with CVEs
- Dependency conflicts

### 3️⃣ PR Size Check (WARNING ONLY ⚠️)

```yaml
Jobs:
  ✓ Count changed lines
  ⚠️  Warn if > 1000 lines changed

Duration: ~30 seconds
Blocks Merge: NO
```

**What it checks:**
- Total lines added + removed
- Warns if PR is too large
- Suggests breaking into smaller PRs

### 4️⃣ Ready to Merge (REQUIRED ✅)

```yaml
Jobs:
  ✓ Confirms all required checks passed

Duration: ~10 seconds
Blocks Merge: YES
```

**What it checks:**
- All previous jobs succeeded
- Final confirmation gate

### 5️⃣ Test Matrix (from test.yml) (REQUIRED ✅)

```yaml
Jobs:
  ✓ Python 3.12 tests
  ✓ Python 3.13 tests

Duration: ~2-3 minutes each
Blocks Merge: YES
```

**What it checks:**
- Tests pass on multiple Python versions
- Cross-version compatibility

## 🚫 What Blocks Merging

Your PR **CANNOT** be merged if:

- ❌ Any test fails
- ❌ Code coverage drops below 65%
- ❌ Linting errors exist
- ❌ Code formatting is incorrect
- ❌ Security vulnerabilities found (high severity)
- ❌ Branch is not up to date with main
- ❌ Required reviews not approved (if configured)
- ❌ Conversations not resolved

## ✅ What Allows Merging

Your PR **CAN** be merged when:

- ✅ All status checks pass
- ✅ Code is up to date with main branch
- ✅ Required approvals received (if configured)
- ✅ All conversations resolved

## 🎬 Example PR Lifecycle

### Initial PR

```bash
$ gh pr create --title "feat: improve recommendation scoring"

Creating pull request for feature/scoring on GitHub.com...

✓ Created PR #42: feat: improve recommendation scoring
  https://github.com/user/movie-list/pull/42
```

**GitHub immediately triggers:**
```
⏳ PR Validation — In progress
⏳ Dependency Security Check — In progress
⏳ PR Size Check — In progress
⏳ Ready to Merge — Waiting
⏳ test (3.12) — In progress
⏳ test (3.13) — In progress
```

### Checks Complete (Success)

```
✅ PR Validation — Passed in 2m 34s
✅ Dependency Security Check — Passed in 1m 12s
✅ PR Size Check — Passed (234 lines changed)
✅ Ready to Merge — Passed
✅ test (3.12) — Passed in 2m 18s
✅ test (3.13) — Passed in 2m 21s

🟢 All checks have passed
   Merge button is now enabled
```

### Checks Complete (Failure)

```
❌ PR Validation — Failed in 1m 45s
✅ Dependency Security Check — Passed in 1m 12s
✅ PR Size Check — Passed (234 lines changed)
❌ Ready to Merge — Failed
❌ test (3.12) — Failed in 1m 32s
✅ test (3.13) — Passed in 2m 21s

🔴 Some checks were not successful
   Merge button is disabled
```

**View details to fix:**
```
PR Validation failed:
  ❌ test_collaborative_filtering.py::test_train FAILED
  
test (3.12) failed:
  ❌ AssertionError: expected 5, got 4
```

### Fix and Re-run

```bash
# Fix the failing test
vim tests/test_collaborative_filtering.py

# Commit fix
git add tests/test_collaborative_filtering.py
git commit -m "fix: update test assertion"

# Push (triggers checks again automatically)
git push origin feature/scoring
```

```
⏳ PR Validation — In progress (re-running)
⏳ test (3.12) — In progress (re-running)
...
```

## 💡 Pro Tips

### Run Checks Locally Before Pushing

Save time by catching issues before CI:

```bash
# Run all pre-push checks
pytest tests/ -v && \
black --check scripts --line-length=120 && \
flake8 scripts --max-line-length=127 && \
echo "✅ All local checks passed!"
```

### Auto-fix Formatting

```bash
# Auto-format instead of checking
black scripts --line-length=120

# Then commit
git add scripts/
git commit -m "style: apply black formatting"
```

### Watch PR Status

```bash
# Watch PR checks in terminal
gh pr checks --watch

# View detailed check logs
gh run view --log-failed
```

### Draft PRs

Mark PR as draft to prevent notifications and reviews while still running checks:

```bash
# Create as draft
gh pr create --draft

# Mark ready when done
gh pr ready
```

Checks run on drafts but won't block merge (draft PRs can't be merged anyway).

## 🆘 Troubleshooting

### "Checks are not running"

1. Check Actions tab for errors
2. Verify workflows exist in `.github/workflows/`
3. Ensure branch protection is configured
4. Check workflow permissions

### "Merge button disabled despite passing checks"

1. Branch may not be up to date:
   ```bash
   git pull origin main
   git push
   ```
2. Review approval may be required (check branch protection settings)
3. Conversations may need resolution

### "Checks running forever"

1. Check Actions tab for stuck jobs
2. Cancel and re-run:
   ```bash
   gh run list
   gh run cancel <run-id>
   gh pr checks --required  # Trigger re-run by pushing
   ```

### "Failed: context deadline exceeded"

Timeout issue (rare). Re-run the check:
```bash
gh pr checks --required
```

## 📚 Resources

- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Actions Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [PR Best Practices](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/best-practices-for-pull-requests)

---

**Result**: PRs cannot be merged until all tests pass! 🎉
