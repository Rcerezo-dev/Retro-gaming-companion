# CI smoke test

This file exists only to validate the CI + CodeRabbit pipeline on a PR into
`develop`. It is safe to delete once the pipeline has been confirmed working.

Expected on this PR:
- `Lint (ruff)` check runs and passes
- `Tests (pytest) (3.11)` and `(3.12)` run and pass
- CodeRabbit posts an automatic review

Delete this file (and close/merge the PR) after the smoke test.
