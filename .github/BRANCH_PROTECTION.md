# Branch Protection Setup

Configure branch protection rules for `main` branch with these required status checks:

## Required Checks (exact names):
- `detect`
- `CI (python)`
- `CI (node)`
- `contract`
- `e2e`
- `gitleaks`

## GitHub Settings > Branches > Add Rule

**Branch name pattern:** `main`

**Settings to enable:**
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require pull request reviews before merging (1 reviewer)
- ✅ Restrict pushes that create files to the root directory

This ensures green-or-doesn't-ship enforcement for all CI workflows.