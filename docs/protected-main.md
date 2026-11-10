# Protected main and marketplace updates

The bumper creates or updates `chore/auto-bump-external-plugins` and opens a pull request. It validates the selected manifests and README before pushing, then dispatches `validate.yml` on the exact bot branch. GitHub Actions does not trigger pull_request workflows for PRs created with GITHUB_TOKEN, so the explicit dispatch supplies the validation check.

Validation failure stops publication of the generated changes. Existing validation-failure issue reporting remains in place. A conflict while merging current main into the automation branch fails the workflow for manual resolution; the bot never force-pushes or bypasses protection.

After this workflow change is merged:

1. Enable **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests**. The bot only creates PRs; no approval/merge step is added.
2. Require a PR for main, enforce for administrators, disable force pushes/deletion, and require the `Marketplace validation` check with an up-to-date branch.
3. Review and merge bump PRs. The workflow no longer directly publishes new pins to main. Release executors must report a pending bump PR until the merged manifest is verified.

Do not enable the main PR requirement while the old direct-push workflow is still active. This change does not dispatch the bumper, change plugin pins or publish a plugin release.

Checks: `python3 scripts/validate-marketplace.py`, `python3 -m unittest discover -s tests -v`, and actionlint for the workflow definitions. The isolated shell test exercises new/existing/unchanged bot branches against a disposable remote and verifies remote main does not change.
