# AgenticKube

[![CI](https://github.com/JuliusHaring/agentickube/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/JuliusHaring/agentickube/actions/workflows/ci.yaml)
[![CD](https://github.com/JuliusHaring/agentickube/actions/workflows/cd.yaml/badge.svg?branch=main)](https://github.com/JuliusHaring/agentickube/actions/workflows/cd.yaml)

**AgenticKube** is a Kubernetes operator that runs LLM-powered agents as first-class resources. You define an `Agent` custom resource (model, API, MCP servers, workspace, optional OpenTelemetry); the operator reconciles it into a Deployment that serves the agent workload.

## Installation

Install from the **release zip** and **container images** (GHCR). No clone required.

1. **Download the deploy bundle**  
   From the [latest release](https://github.com/JuliusHaring/agentickube/releases), download `agentickube-deploy.zip`, unzip it, and `cd` into the extracted folder (it contains `crd.yaml`, `example-rbac.yaml`, `operator.yaml`, `example-agent.yaml`).

2. **Images**  
   The operator and agent images are published to GitHub Container Registry:
   - `ghcr.io/juliusharing/agentickube/operator:latest` (and versioned tags)
   - `ghcr.io/juliusharing/agentickube/agent:latest`  
   The YAML in the zip references these; ensure your cluster can pull from GHCR (e.g. public packages, or configure imagePullSecrets if private).

3. **Apply in order**
   ```bash
   kubectl create namespace agentickube-ns
   kubectl apply -f crd.yaml
   kubectl apply -f example-rbac.yaml
   kubectl apply -f operator.yaml
   ```
   All resources use namespace `agentickube-ns`; edit the YAML if you want a different namespace.

4. **Create an Agent**  
   Edit `example-agent.yaml`: set `spec.llm.modelName`, `spec.llm.baseUrl`, and optionally `apiKey` (or `secretName`/`secretKey`). Then:
   ```bash
   kubectl apply -f example-agent.yaml
   ```

**From clone (optional)**  
If you have the repo cloned, apply from the `deploy/` directory: same files and order as above (`crd.yaml` → `example-rbac.yaml` → `operator.yaml` → your Agent CRs). For local dev, see [Developing](#developing).

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
- **CRD and Agent examples (generated from models)**: The [CRD](deploy/crd.yaml) and [example Agent](deploy/example-agent.yaml) (and the Agent CR in `manifests/agent.yaml`) are generated from the operator’s Pydantic models in [`code/operator/models.py`](code/operator/models.py). That way the spec lives in one place: change the models, run `task operator:generate`, and the CRD and example manifests stay in sync. Deploy runs this task automatically; CI and CD run the same `task operator:generate` (CI validates the generated YAML, CD regenerates before building the release zip).
- **Deploy (local)**: `task deploy` runs dev:all, builds the agent and operator images, creates the `agentickube-ns` namespace, applies the CRD, clears and reapplies manifests and the example Agent. Run the operator separately (e.g. `task operator:run`) so it watches for Agent CRs.

**Kubernetes in Docker Desktop**  
For local development you can use the Kubernetes cluster built into [Docker Desktop](https://www.docker.com/products/docker-desktop/): enable it under **Settings → Kubernetes → Enable Kubernetes**, then ensure `kubectl` is available (Docker Desktop adds it to your path); the cluster will pull images from GHCR or use images you build locally (e.g. after `task deploy`).
