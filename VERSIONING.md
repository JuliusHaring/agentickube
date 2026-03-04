# Versioning

Versions are managed by [python-semantic-release](https://python-semantic-release.readthedocs.io/).

- **Bump**: On push to `main`, PSR looks at commit messages (conventional commits) and bumps the version only when there are `feat` (minor), `fix` (patch), or `BREAKING CHANGE` (major) commits since the last tag. No manual edit of `VERSION` is required.
- **VERSION file**: Root file `VERSION` is stamped by PSR (format `version=X.Y.Z`). To read the version in scripts, use the whole line or strip the `version=` prefix.
- **Tag & release**: PSR creates the git tag and GitHub release; the workflow then attaches `deploy/crd.yaml` and `deploy/README.md` to the release.

Local: `task version:current` prints the current version.
