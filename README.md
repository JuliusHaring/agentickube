[![CI](https://github.com/JuliusHaring/agentickube/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/JuliusHaring/agentickube/actions/workflows/ci.yaml)
[![CD](https://github.com/JuliusHaring/agentickube/actions/workflows/cd.yaml/badge.svg?branch=main)](https://github.com/JuliusHaring/agentickube/actions/workflows/cd.yaml)

# AgenticKube

[![Star History Chart](https://api.star-history.com/image?repos=JuliusHaring/agentickube&type=date&legend=bottom-right)](https://www.star-history.com/?repos=JuliusHaring%2Fagentickube&type=date&legend=top-left)

**🤖 Agents in Kubernetes — declarative, yours, no lock-in.**

**Try it:** install with Helm (see below), or peek at the [chart values](chart/agentickube/values.yaml) and [values-dev](chart/agentickube/values-dev.yaml) for examples.

Define an `Agent` in YAML (model, API, optional MCP and workspace); the operator reconciles it into a Deployment, one-off Job, or CronJob. Optionally coordinate multiple agents with an `Orchestrator` (currently sequence or team). Your models, your cluster.

| | |
|---|---|
| 🧩 | **One resource** — one `Agent` = one workload (HTTP, one-off Job, or Cron) |
| 🔌 | **Your LLM** — Ollama, OpenAI, any compatible API |
| 🔧 | **MCP + skills** — [MCP tools & knowledge](https://modelcontextprotocol.io/), [SKILL.md format](code/agent/workspace/skills/create-skills/SKILL.md) |
| 📁 | **Mountable Workspace** — optional PVC for persistent state and files |
| 🤝 | **Orchestrator** — optional multi-agent coordination (sequence, team) |
| 📦 | **Helm OCI** — one command to install CRDs + operator from GHCR |

## Installation

**Prerequisites:** Helm 3.8+, a Kubernetes cluster, and `kubectl` configured.

### Helm (recommended)

Install the operator and CRDs from GitHub Container Registry:

```bash
helm install agentickube oci://ghcr.io/juliusharing/agentickube/chart \
  --namespace agentickube-ns \
  --create-namespace
```

The chart uses the operator image from GHCR by default. To pin a version:

```bash
helm install agentickube oci://ghcr.io/juliusharing/agentickube/chart \
  --namespace agentickube-ns \
  --create-namespace \
  --set operator.image.tag=2.1.0
```

**Optional stack (values):** Enable Ollama (`ollama.enabled`), OpenTelemetry collector (`otel.enabled`), and Jaeger (`jaeger.enabled`) for local or dev clusters. Use `agents: [{ name, spec }, ...]` and `orchestrators: [{ name, spec }, ...]` to create multiple Agent and Orchestrator CRs from the chart. See [chart/agentickube/values.yaml](chart/agentickube/values.yaml) and [chart/agentickube/values-dev.yaml](chart/agentickube/values-dev.yaml) for examples.

**Images** (all on GHCR; chart references these by default):

- `ghcr.io/juliusharing/agentickube/operator:latest` (and versioned tags)
- `ghcr.io/juliusharing/agentickube/agent:latest`
- `ghcr.io/juliusharing/agentickube/orchestrator:latest`

Ensure your cluster can pull from GHCR (e.g. public packages, or configure imagePullSecrets if private).

**Create Agents/Orchestrators** — set `agents` and `orchestrators` in values (see [values-dev.yaml](chart/agentickube/values-dev.yaml)), or `kubectl apply` your own Agent/Orchestrator YAML.

### GitOps (ArgoCD / Flux)

Use the same chart from OCI: point your Application or HelmRelease to `oci://ghcr.io/juliusharing/agentickube/chart`. CRDs are included in the chart with install hooks so they apply before the operator.

### From clone (developers)

From the repo root: `task deploy` builds images, generates CRDs into the chart, and runs `helm upgrade --install` with [values-dev.yaml](chart/agentickube/values-dev.yaml) (Ollama, OTEL, Jaeger, one example Agent and Orchestrator). Run `task operator:run` for an out-of-cluster operator, or `task agent:run` for a local agent. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE).

## Contributing

If you want to contribute feel free to check out [CONTRIBUTING.md](CONTRIBUTING.md)!
