# Contributing to AgenticKube

Thanks for your interest in contributing. This document covers versioning and local development.

## Versioning

Versions are managed by [python-semantic-release](https://python-semantic-release.readthedocs.io/).

- **Bump**: On push to `main`, PSR looks at commit messages (conventional commits) and bumps the version only when there are `feat` (minor), `fix` (patch), or `BREAKING CHANGE` (major) commits since the last tag. No manual edit of `VERSION` is required.
- **VERSION file**: Root file `VERSION` is stamped by PSR (format `version=X.Y.Z`). To read the version in scripts, use the whole line or strip the `version=` prefix.
- **Tag & release**: PSR creates the git tag and GitHub release; the workflow attaches `agentickube-deploy.zip` (CRD, example RBAC, operator, example Agent) to the release.

Local: `task version:current` prints the current version.

## Developing

Use [Task](https://taskfile.dev/) and [uv](https://docs.astral.sh/uv/) for a reproducible dev setup. From the repo root:

- **Setup**:
  ```bash
  uv venv
  source .venv/bin/activate   # Linux/macOS; on Windows: .venv\Scripts\activate
  task dev:install
  ```
  (Installs from `environments/all-requirements.txt`.)
- **Lint/format**: `task dev:all` runs install, format, and lint-fix.
- **CRD and Agent examples (generated from models)**: The [CRD](deploy/crd.yaml) and [example Agent](deploy/example-agent.yaml) (and the Agent CR in `manifests/agent.yaml`) are generated from the operator's Pydantic models in [`code/operator/models.py`](code/operator/models.py). That way the spec lives in one place: change the models, run `task operator:generate`, and the CRD and example manifests stay in sync. Deploy runs this task automatically; CI and CD run the same `task operator:generate` (CI validates the generated YAML, CD regenerates before building the release zip).
- **Deploy (local)**: `task deploy` runs dev:all, builds the agent and operator images, creates the `agentickube-ns` namespace, applies the CRD, clears and reapplies manifests and the example Agent. Run the operator separately (e.g. `task operator:run`) so it watches for Agent CRs.

**Kubernetes in Docker Desktop**  
For local development you can use the Kubernetes cluster built into [Docker Desktop](https://www.docker.com/products/docker-desktop/): enable it under **Settings → Kubernetes → Enable Kubernetes**, then ensure `kubectl` is available (Docker Desktop adds it to your path); the cluster will pull images from GHCR or use images you build locally (e.g. after `task deploy`).
