"""
Generate deploy/example-agent.yaml and the Agent CR in manifests/agent.yaml
from the operator's Pydantic models (single source of truth).

Usage (from repo root):
  PYTHONPATH=code/operator python code/operator/agent_examples_gen.py
  task operator:generate-examples
"""

from __future__ import annotations

import sys
from pathlib import Path

_operator_dir = Path(__file__).resolve().parent
_repo_root = _operator_dir.parents[1]
if str(_operator_dir) not in sys.path:
    sys.path.insert(0, str(_operator_dir))

from models import (  # noqa: E402
    AgentSpec,
    LLMConfig,
    MCPServerConfig,
    OpenTelemetryConfig,
    PromptsConfig,
    PVCConfig,
    WorkspaceConfig,
)


def _agent_cr_yaml(name: str, spec: AgentSpec, comment: str | None = None) -> str:
    """Single Agent CR document as YAML string (camelCase spec)."""
    import yaml

    doc = {
        "apiVersion": "ai.juliusharing.com/v1",
        "kind": "Agent",
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


def _example_spec() -> AgentSpec:
    """Minimal example for deploy/example-agent.yaml (docs / release zip)."""
    return AgentSpec(
        llm=LLMConfig(model_name="", base_url=""),
    )


def _dev_spec() -> AgentSpec:
    """Dev manifest spec for manifests/agent.yaml (my-agent, ollama, workspace, otel)."""
    return AgentSpec(
        image="agentickube-agent:latest",
        image_pull_policy="Never",
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
    )


# Static PVC and Job appended to manifests/agent.yaml (not from Pydantic).
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

    example_yaml = _agent_cr_yaml(
        "example",
        _example_spec(),
        comment="Generated from code/operator/models.py - task operator:generate-examples",
    )
    dev_yaml = _agent_cr_yaml("my-agent", _dev_spec())

    example_path = _repo_root / "deploy" / "example-agent.yaml"
    example_path.parent.mkdir(parents=True, exist_ok=True)
    example_path.write_text(example_yaml, encoding="utf-8")
    print(f"Wrote {example_path}", file=sys.stderr)

    manifests_agent_path = _repo_root / "manifests" / "agent.yaml"
    manifests_agent_path.parent.mkdir(parents=True, exist_ok=True)
    full_manifests = dev_yaml.rstrip() + "\n" + _MANIFESTS_AGENT_EXTRA.strip() + "\n"
    manifests_agent_path.write_text(full_manifests, encoding="utf-8")
    print(f"Wrote {manifests_agent_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
