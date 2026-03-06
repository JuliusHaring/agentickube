"""
Generate example manifests for Agents and Orchestrators from the operator's
Pydantic models (single source of truth).

Usage (from repo root):
  PYTHONPATH=code/operator python code/operator/examples_gen.py
  task operator:generate-examples
"""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import BaseModel

_operator_dir = Path(__file__).resolve().parent
_repo_root = _operator_dir.parents[1]
if str(_operator_dir) not in sys.path:
    sys.path.insert(0, str(_operator_dir))

from models import (  # noqa: E402
    AgentRef,
    AgentSpec,
    ConversationConfig,
    LLMConfig,
    MCPServerConfig,
    OpenTelemetryConfig,
    OrchestratorSpec,
    PromptsConfig,
    PVCConfig,
    StrategyConfig,
    TriggerConfig,
    WorkspaceConfig,
)


# ── YAML helpers ─────────────────────────────────────────────────────────────


def _cr_yaml(kind: str, name: str, spec: BaseModel, comment: str | None = None) -> str:
    import yaml

    doc = {
        "apiVersion": "ai.juliusharing.com/v1",
        "kind": kind,
        "metadata": {"name": name},
        "spec": spec.model_dump(by_alias=True, exclude_none=True),
    }
    out = yaml.dump(
        doc,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )
    if comment:
        out = f"# {comment}\n" + out
    return out


# ── Agent specs ──────────────────────────────────────────────────────────────


def _example_agent_spec() -> AgentSpec:
    return AgentSpec(
        llm=LLMConfig(model_name="", base_url=""),
    )


def _dev_agent_spec() -> AgentSpec:
    return AgentSpec(
        image="agentickube-agent:latest",
        image_pull_policy="Never",
        description="General-purpose development agent",
        llm=LLMConfig(
            model_name="qwen3:1.7b",
            base_url="http://ollama:11434/v1",
        ),
        prompts=PromptsConfig(system_prompt="test"),
        mcp_servers=[
            MCPServerConfig(
                url="https://knowledge-mcp.global.api.aws", type="streamable_http"
            ),
        ],
        workspace=WorkspaceConfig(
            path="/workspace",
            persistent_volume_claim=PVCConfig(claim_name="agent-workspace-pvc"),
        ),
        open_telemetry=OpenTelemetryConfig(
            enabled=True,
            endpoint="http://otel-collector:4318",
            service_name="my-agent",
            sampling_ratio=1.0,
        ),
        conversation=ConversationConfig(
            enabled=True,
            max_history=10,
        ),
    )


def _job_agent_spec() -> AgentSpec:
    return AgentSpec(
        llm=LLMConfig(model_name="", base_url=""),
        trigger=TriggerConfig(
            type="job",
            query="Summarize all pods in the cluster",
            backoff_limit=2,
            ttl_seconds_after_finished=300,
        ),
    )


def _cron_agent_spec() -> AgentSpec:
    return AgentSpec(
        llm=LLMConfig(model_name="", base_url=""),
        trigger=TriggerConfig(
            type="cron",
            query="Check cluster health and report anomalies",
            schedule="0 */6 * * *",
        ),
    )


# ── Orchestrator specs ───────────────────────────────────────────────────────


def _example_orchestrator_spec() -> OrchestratorSpec:
    return OrchestratorSpec(
        llm=LLMConfig(model_name="", base_url=""),
        agents=[
            AgentRef(name="agent-1"),
            AgentRef(name="agent-2"),
        ],
        strategy=StrategyConfig(type="sequence"),
    )


def _dev_orchestrator_spec() -> OrchestratorSpec:
    return OrchestratorSpec(
        image="agentickube-orchestrator:latest",
        image_pull_policy="Never",
        description="Dev orchestrator coordinating my-agent",
        llm=LLMConfig(
            model_name="qwen3:1.7b",
            base_url="http://ollama:11434/v1",
        ),
        agents=[
            AgentRef(name="my-agent", description="General-purpose development agent"),
        ],
        strategy=StrategyConfig(type="sequence"),
    )


def _job_orchestrator_spec() -> OrchestratorSpec:
    return OrchestratorSpec(
        llm=LLMConfig(model_name="", base_url=""),
        agents=[
            AgentRef(name="researcher"),
            AgentRef(name="summarizer"),
        ],
        strategy=StrategyConfig(type="sequence"),
        trigger=TriggerConfig(
            type="job",
            query="Research and summarize latest security advisories",
            backoff_limit=2,
            ttl_seconds_after_finished=300,
        ),
    )


def _cron_orchestrator_spec() -> OrchestratorSpec:
    return OrchestratorSpec(
        llm=LLMConfig(model_name="", base_url=""),
        agents=[
            AgentRef(name="monitor"),
            AgentRef(name="analyst"),
            AgentRef(name="reporter"),
        ],
        strategy=StrategyConfig(type="team"),
        trigger=TriggerConfig(
            type="cron",
            query="Analyze cluster health from multiple perspectives",
            schedule="0 */6 * * *",
        ),
    )


# ── Static extra YAML for manifests/agent.yaml ──────────────────────────────

_MANIFESTS_AGENT_EXTRA = """---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agent-workspace-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: batch/v1
kind: Job
metadata:
  name: agent-workspace-init
spec:
  ttlSecondsAfterFinished: 300
  backoffLimit: 2
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: init
          image: busybox:1.36
          command:
            - sh
            - -c
            - |
              set -e
              mkdir -p /workspace
              cat > /workspace/ws.txt << 'EOF'
              To be, or not to be, that is the question:
              Whether 'tis nobler in the mind to suffer
              The slings and arrows of outrageous fortune,
              Or to take arms against a sea of troubles
              And by opposing end them.
              — Shakespeare, Hamlet
              EOF
              cat > /workspace/eh.txt << 'EOF'
              In the late summer of that year we lived in a house in a village that looked across the river and the plain to the mountains.
              — Hemingway, A Farewell to Arms
              EOF
          volumeMounts:
            - name: workspace
              mountPath: /workspace
      volumes:
        - name: workspace
          persistentVolumeClaim:
            claimName: agent-workspace-pvc
"""


def main() -> int:
    try:
        import yaml  # noqa: F401
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 1

    gen_comment = (
        "Generated from code/operator/models.py - task operator:generate-examples"
    )

    deploy_dir = _repo_root / "deploy"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir = _repo_root / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    # ── Agent examples ───────────────────────────────────────────────────
    for fname, name, spec in [
        ("example-agent.yaml", "example", _example_agent_spec()),
        ("example-agent-job.yaml", "example-job", _job_agent_spec()),
        ("example-agent-cron.yaml", "example-cron", _cron_agent_spec()),
    ]:
        path = deploy_dir / fname
        path.write_text(
            _cr_yaml("Agent", name, spec, comment=gen_comment), encoding="utf-8"
        )
        print(f"Wrote {path}", file=sys.stderr)

    dev_yaml = _cr_yaml("Agent", "my-agent", _dev_agent_spec())
    manifests_agent_path = manifests_dir / "agent.yaml"
    full_manifests = dev_yaml.rstrip() + "\n" + _MANIFESTS_AGENT_EXTRA.strip() + "\n"
    manifests_agent_path.write_text(full_manifests, encoding="utf-8")
    print(f"Wrote {manifests_agent_path}", file=sys.stderr)

    # ── Orchestrator examples ────────────────────────────────────────────
    for fname, name, spec in [
        ("example-orchestrator.yaml", "example-sequence", _example_orchestrator_spec()),
        (
            "example-orchestrator-job.yaml",
            "example-sequence-job",
            _job_orchestrator_spec(),
        ),
        (
            "example-orchestrator-cron.yaml",
            "example-team-cron",
            _cron_orchestrator_spec(),
        ),
    ]:
        path = deploy_dir / fname
        path.write_text(
            _cr_yaml("Orchestrator", name, spec, comment=gen_comment), encoding="utf-8"
        )
        print(f"Wrote {path}", file=sys.stderr)

    dev_orch_yaml = _cr_yaml(
        "Orchestrator", "my-orchestrator", _dev_orchestrator_spec()
    )
    manifests_orch_path = manifests_dir / "orchestrator.yaml"
    manifests_orch_path.write_text(dev_orch_yaml, encoding="utf-8")
    print(f"Wrote {manifests_orch_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
