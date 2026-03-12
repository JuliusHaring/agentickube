# Contributing to AgenticKube

Thanks for your interest in contributing. This document covers versioning and local development.

## Versioning

Versions are managed by [python-semantic-release](https://python-semantic-release.readthedocs.io/).

- **Branches**: Name branches after the change type and a short slug, e.g. `feat/feature-a`, `fix/issue-123`, `fix/typo-readme`. This aligns with the conventional types PSR uses for version bumps.
- **Commits**: Use imperative mood in the subject line (e.g. "fix validation to allow empty builtin_skills" or "add CONTRIBUTING section on commits"), not past tense ("fixed validation" / "added section").
- **Bump**: On push to `main`, PSR looks at commit messages (conventional commits) and bumps the version only when there are `feat` (minor), `fix` (patch), or `BREAKING CHANGE` (major) commits since the last tag. No manual edit of `VERSION` is required.
- **VERSION file**: Root file `VERSION` is stamped by PSR (format `version=X.Y.Z`). To read the version in scripts, use the whole line or strip the `version=` prefix.
- **Tag & release**: PSR creates the git tag and GitHub release; the workflow publishes the Helm chart to GHCR OCI (`oci://ghcr.io/juliusharing/agentickube/chart`). Install with `helm install agentickube oci://ghcr.io/juliusharing/agentickube/chart`.

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
- **CRDs (generated from models)**: The Agent CRD is generated from the operator's Pydantic models in [`code/operator/models.py`](code/operator/models.py) into [chart/agentickube/templates/](chart/agentickube/templates/). Change the models, run `task operator:generate`, and the chart CRD stays in sync. Deploy runs this task automatically; CI and CD run the same before validating or publishing the Helm chart.
- **Deploy (local)**: `task deploy` runs dev:all, builds the agent and operator images, creates the `agentickube-ns` namespace, then installs/upgrades the Helm chart with [values-dev.yaml](chart/agentickube/values-dev.yaml) (Ollama, OTEL, Jaeger, example Agents). Run the operator separately (e.g. `task operator:run`) for out-of-cluster watching, or `task agent:run` for a local agent. For a minimal install without the dev stack, use `task chart:install-local`.

**Kubernetes in Docker Desktop**  
For local development you can use the Kubernetes cluster built into [Docker Desktop](https://www.docker.com/products/docker-desktop/): enable it under **Settings → Kubernetes → Enable Kubernetes**, then ensure `kubectl` is available (Docker Desktop adds it to your path); the cluster will pull images from GHCR or use images you build locally (e.g. after `task deploy`).
