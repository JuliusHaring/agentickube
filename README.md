[![CI](https://github.com/JuliusHaring/agentickube/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/JuliusHaring/agentickube/actions/workflows/ci.yaml)
[![CD](https://github.com/JuliusHaring/agentickube/actions/workflows/cd.yaml/badge.svg?branch=main)](https://github.com/JuliusHaring/agentickube/actions/workflows/cd.yaml)

# AgenticKube

**🤖 Agents in Kubernetes — declarative, yours, no lock-in.**

Define an `Agent` in YAML (model, API, optional MCP and workspace); the operator reconciles it into a Deployment, one-off Job, or CronJob. Your models, your cluster.

| | |
|---|---|
| 🧩 | **One resource** — one `Agent` = one workload (HTTP, one-off Job, or Cron) |
| 🔌 | **Your LLM** — Ollama, OpenAI, any compatible API |
| 🔧 | **MCP + SKILLS.md** — [tools & knowledge](https://modelcontextprotocol.io/) |
| 📁 | **Mountable Workspace** — optional PVC for persistent state and files |
| 📦 | **Zip → apply** — CRD + operator + example, then you’re live |

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
If you have the repo cloned, apply from the `deploy/` directory: same files and order as above (`crd.yaml` → `example-rbac.yaml` → `operator.yaml` → your Agent CRs).

## Contributing

If you want to contribute feel free to check out [CONTRIBUTING.md](CONTRIBUTING.md)!