# Marketplace automation architecture and protected main

The bumper creates or updates `chore/auto-bump-external-plugins` and opens a pull request. It validates the selected manifests and README before pushing, then dispatches `validate.yml` on the exact bot branch. GitHub Actions does not trigger pull_request workflows for PRs created with GITHUB_TOKEN, so the explicit dispatch supplies the validation check.

Validation failure stops publication of the generated changes. Existing validation-failure issue reporting remains in place. A conflict while merging current main into the automation branch fails the workflow for manual resolution; the bot never force-pushes or bypasses protection.

After this workflow change is merged:

1. Enable **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests**. The bot only creates PRs; no approval/merge step is added.
2. Require a PR for main, enforce for administrators, disable force pushes/deletion, and require the `Marketplace validation` check with an up-to-date branch.
3. Review and merge bump PRs. The workflow no longer directly publishes new pins to main. Release executors must report a pending bump PR until the merged manifest is verified.

Do not enable the main PR requirement while the old direct-push workflow is still active. This change does not dispatch the bumper, change plugin pins or publish a plugin release.

Checks: `python3 scripts/validate-marketplace.py`, `python3 -m unittest discover -s tests -v`, and actionlint for the workflow definitions. The isolated shell test exercises new/existing/unchanged bot branches against a disposable remote and verifies remote main does not change.

## Source map and contracts

| Source | Responsibility |
|---|---|
| `scripts/bump-external-plugins.py` | Resolve latest public plugin releases, update existing Claude ref/SHA and README versions, synchronize already-listed portable plugin SHAs |
| `scripts/validate-marketplace.py` | Read-only structural and version consistency checks; online mode required in CI, offline mode only for quick local feedback |
| `.github/workflows/auto-bump-external-plugins.yml` | Schedule/notification/manual triggers; orchestrate generation, validation, branch merge/push, PR and exact-branch check dispatch |
| `.github/workflows/validate.yml` | Required `Marketplace validation` check on PRs, main pushes and explicit workflow dispatch |
| `tests/test_bump_workflow.py` | Execute the actual workflow shell against a disposable Git remote with gh mocked; prove branch refreshes never push main |
| `AGENTS.md`, `CLAUDE.md` | Discoverable agent policy and existing marketplace-specific project rules |

The scripts use Python's standard library and gh. The bumper mutates only generated source files locally; it does not commit/push/merge. Its `--sync-agents` mode synchronizes already-approved portable listings without release queries; it never grants permission to list a new plugin. The validator does not repair files. `--offline` omits remote version checking and cannot substitute for CI's online gate. Remote reads prefer canonical root plugin.json and fall back to the legacy Claude manifest for older releases.

## Workflow transitions and why they matter

1. Triggers serialize through a concurrency group. Checkout fetches history so an existing automation branch can merge current main.
2. The bumper computes desired manifest/README bytes on main. An unchanged source diff ends the update path; existing duplicate trigger policy is not otherwise redesigned here.
3. Online validation runs before any generated change is committed. Failure follows the existing issue-report path; it never publishes an invalid pin.
4. For a changed diff, preserve the validated files temporarily, restore the checkout, create/fetch the deterministic bot branch, and merge remote main. Restore the desired files and validate again against the resulting tree.
5. Commit only if staged generated files changed. Push the branch even if its only new commit is the main merge: strict protection otherwise leaves an open PR permanently behind main.
6. Open a PR only when no open PR already exists for that branch, so a previously merged/closed PR does not suppress the next update.
7. Explicitly dispatch validation on the pushed branch. GITHUB_TOKEN-created PRs do not trigger PR workflows, so relying only on pull_request would leave the required check absent. Dispatch runs against the selected branch commit; a later branch update needs its own check.
8. A human reviews/merges the validated PR. Only the merged manifests establish marketplace publication; a successful bot generation run is not evidence that new pins reached main.

Validation workflow permissions are read-only. The orchestration workflow separately needs contents/pull-requests/actions/issue permissions for its branch push, PR creation, check dispatch and existing failure reporting. Actions PR creation is a repository setting, separate from YAML. Main protection requires PRs, strict `Marketplace validation`, admin enforcement, no force pushes/deletion and no required approving review for the solo maintainer. The bot has no protected-main bypass or automatic merge. Keep required check names aligned with server settings.

## Maintenance and recovery

Keep implementation, code contracts, this design/runbook and agent instructions consistent in one PR. Prefer descriptive code and comments explaining constraints over a second copy of shell logic in a prose example. The regression test extracts the actual workflow step; preserve its scope or update the harness when renaming/restructuring that step.

For command changes, run the isolated test for new/existing/unchanged branches, unrelated main advances and merge-only refreshes. Run online validation and actionlint for workflow changes. The fixture never calls live gh or changes real pins. A live new-version bot publication has not been manufactured as part of the shared-development verification; do not generalize the isolated test into that claim.

If branch merge conflicts, validation fails, PR creation is disabled, or a required check is missing, fix the relevant source/settings and rerun the authorized workflow. Resolve conflicts on the bot branch through ordinary Git review; do not force-push main or remove protection. Preserve validated files and inspect failures before retrying. An offline pass cannot clear an online failure. Do not copy release version/tag/archive logic here: that belongs to [pa-toolkit's shared release runbook](https://github.com/folotp/pa-toolkit/blob/main/skills/plugin-release/references/runbook.md).

Local generic Git guards come from pa-toolkit's stable `skills/plugin-release/scripts/branch-guard.py` checkout. Reinstall them before moving/removing that source; preserve unmanaged hooks. The canonical Organon [architecture guide](https://github.com/folotp/organon-plugin/blob/main/docs/development-architecture.md) maps all three repositories and their shared-development boundaries.
