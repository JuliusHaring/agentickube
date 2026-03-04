# AgenticKube

**AgenticKube** is a Kubernetes operator that runs LLM-powered agents as first-class resources. You define an `Agent` custom resource (model, API, MCP servers, workspace, optional OpenTelemetry); the operator reconciles it into a Deployment that serves the agent workload.

Install the CRD, run the operator, then create Agent CRs. The operator reconciles each `Agent` into a Deployment running the agent image.

## Quick start

1. **CRD**
   ```bash
   kubectl apply -f crd.yaml
   ```

2. **Operator** (RBAC + Deployment using the operator image)
   - From the repo: apply the manifests in `manifests/` (e.g. `manifests/rbac.yaml` and an operator Deployment that uses `derjulezzz/agentickube-operator:latest`).
   - Or use your own Deployment that runs the operator image with in-cluster config and the same RBAC.

3. **Example Agent**
   ```bash
   kubectl apply -f example-agent.yaml
   ```
   Edit `example-agent.yaml` first: set `spec.llm.modelName` and `spec.llm.baseUrl` (and optionally `apiKey` or `apiKey.secretName`/`secretKey`).

## Assets in releases

GitHub releases (created on push to `main` when version is bumped) include:

- `crd.yaml` — CustomResourceDefinition for `agents.ai.juliusharing.com`
- `example-agent.yaml` — minimal example Agent CR
- This README

## Versioning

Versions are managed by [python-semantic-release](https://python-semantic-release.readthedocs.io/).

- **Bump**: On push to `main`, PSR looks at commit messages (conventional commits) and bumps the version only when there are `feat` (minor), `fix` (patch), or `BREAKING CHANGE` (major) commits since the last tag. No manual edit of `VERSION` is required.
- **VERSION file**: Root file `VERSION` is stamped by PSR (format `version=X.Y.Z`). To read the version in scripts, use the whole line or strip the `version=` prefix.
- **Tag & release**: PSR creates the git tag and GitHub release; the workflow attaches `deploy/crd.yaml`, `deploy/example-agent.yaml`, and `deploy/README.md` to the release.

Local: `task version:current` prints the current version.

## Developing

Use [Task](https://taskfile.dev/) and [uv](https://docs.astral.sh/uv/) for a reproducible dev setup. From the repo root:

- **Setup**: Create a venv and install dev dependencies: `uv venv` then `task dev:install` (installs from `environments/dev-requirements.txt`).
- **Lint/format**: `task dev:all` runs install, format, and lint-fix.
- **Deploy (local)**: `task deploy` runs dev:all, builds the agent and operator images, creates the `test` namespace, applies the CRD, clears and reapplies manifests and the example Agent. Run the operator separately (e.g. `task operator:run`) so it watches for Agent CRs.
