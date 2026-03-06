"""
Generate chart/agentickube/templates/crd-agent.yaml and crd-orchestrator.yaml from
the operator's Pydantic models (single source of truth).

Usage (from repo root):
  PYTHONPATH=code/operator python code/operator/crd_gen.py
  task operator:generate-crd

After changing code/operator/models.py, run the generator to refresh the CRDs.
Add Field(description=...) and Literal[...] in models to get CRD descriptions and enums.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Type

from pydantic import BaseModel

# Add operator dir for imports when run as script or module
_operator_dir = Path(__file__).resolve().parent
_repo_root = _operator_dir.parents[1]
if str(_operator_dir) not in sys.path:
    sys.path.insert(0, str(_operator_dir))

from models import AgentSpec, OrchestratorSpec  # noqa: E402


def _json_schema_to_openapi(schema: dict) -> dict:
    """Convert Pydantic JSON Schema: $defs -> definitions, fix ref paths."""
    schema = json.loads(json.dumps(schema))  # deep copy
    definitions = schema.pop("$defs", {})
    if definitions:
        schema["definitions"] = definitions

    def fix_ref_paths(obj):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if k == "$ref" and isinstance(v, str) and "#/$defs/" in v:
                    obj[k] = v.replace("#/$defs/", "#/definitions/")
                else:
                    fix_ref_paths(v)
        elif isinstance(obj, list):
            for item in obj:
                fix_ref_paths(item)

    fix_ref_paths(schema)
    if schema.get("definitions"):
        fix_ref_paths(schema["definitions"])
    return schema


def _inline_refs(obj: dict, definitions: dict) -> dict:
    """Recursively replace $ref with a copy of the referenced definition. K8s CRD does not support $ref."""
    if isinstance(obj, dict):
        if list(obj.keys()) == ["$ref"]:
            ref = obj["$ref"]
            if ref.startswith("#/definitions/") and "/" in ref:
                name = ref.split("/")[-1]
                if name in definitions:
                    return _inline_refs(copy.deepcopy(definitions[name]), definitions)
        return {k: _inline_refs(v, definitions) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_inline_refs(item, definitions) for item in obj]
    return obj


def _anyof_null_to_nullable(obj):
    """Convert anyOf: [T, {type: 'null'}] to type T + nullable: true. K8s does not allow type: 'null'."""
    if isinstance(obj, dict):
        if "anyOf" in obj and isinstance(obj["anyOf"], list) and len(obj["anyOf"]) == 2:
            a, b = obj["anyOf"]
            null_schema = {"type": "null"}
            if a == null_schema:
                non_null = b
            elif b == null_schema:
                non_null = a
            else:
                non_null = None
            if non_null is not None:
                out = copy.deepcopy(non_null)
                out["nullable"] = True
                return _anyof_null_to_nullable(out)
        return {k: _anyof_null_to_nullable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_anyof_null_to_nullable(x) for x in obj]
    return obj


def _strip_titles_and_default_null(obj):
    """Remove title keys and default: null to keep CRD small."""
    if isinstance(obj, dict):
        obj.pop("title", None)
        if obj.get("default") is None and "nullable" in obj:
            obj.pop("default", None)
        return {k: _strip_titles_and_default_null(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_titles_and_default_null(x) for x in obj]
    return obj


def _build_openapi_schema(spec_cls: Type[BaseModel], description: str) -> dict:
    """Build Kubernetes-compatible openAPIV3Schema from a Pydantic model."""
    raw = spec_cls.model_json_schema(mode="serialization")
    spec_schema = _json_schema_to_openapi(raw)

    definitions = dict(spec_schema.get("definitions", {}))
    spec_only = {
        k: v for k, v in spec_schema.items() if k not in ("definitions", "$defs")
    }
    spec_key = spec_cls.__name__
    if spec_only:
        definitions[spec_key] = spec_only

    spec_inlined = _inline_refs({"$ref": f"#/definitions/{spec_key}"}, definitions)
    spec_inlined = _anyof_null_to_nullable(spec_inlined)

    root = {
        "type": "object",
        "description": description,
        "properties": {"spec": spec_inlined},
        "required": ["spec"],
    }

    _strip_titles_and_default_null(root)
    return root


# Recommended labels for CRDs (align with operator-created resources)
_CRD_LABELS_PART_OF = "agentickube"


def _crd_document(
    openapi_schema: dict,
    *,
    crd_name: str,
    group: str,
    plural: str,
    singular: str,
    kind: str,
    short_names: list[str],
) -> dict:
    """Full CustomResourceDefinition document."""
    return {
        "apiVersion": "apiextensions.k8s.io/v1",
        "kind": "CustomResourceDefinition",
        "metadata": {
            "name": crd_name,
            "labels": {
                "app.kubernetes.io/name": plural,
                "app.kubernetes.io/part-of": _CRD_LABELS_PART_OF,
            },
            "annotations": {
                "helm.sh/hook": "pre-install",
                "helm.sh/hook-weight": "-1",
            },
        },
        "spec": {
            "group": group,
            "scope": "Namespaced",
            "names": {
                "plural": plural,
                "singular": singular,
                "kind": kind,
                "shortNames": short_names,
            },
            "versions": [
                {
                    "name": "v1",
                    "served": True,
                    "storage": True,
                    "schema": {"openAPIV3Schema": openapi_schema},
                }
            ],
        },
    }


# ── CRD definitions ─────────────────────────────────────────────────────────

CRDS = [
    {
        "spec_cls": AgentSpec,
        "description": "Agent custom resource (ai.juliusharing.com).",
        "crd_name": "agents.ai.juliusharing.com",
        "group": "ai.juliusharing.com",
        "plural": "agents",
        "singular": "agent",
        "kind": "Agent",
        "short_names": ["ag"],
        "output": "chart/agentickube/templates/crd-agent.yaml",
    },
    {
        "spec_cls": OrchestratorSpec,
        "description": "Orchestrator custom resource (ai.juliusharing.com).",
        "crd_name": "orchestrators.ai.juliusharing.com",
        "group": "ai.juliusharing.com",
        "plural": "orchestrators",
        "singular": "orchestrator",
        "kind": "Orchestrator",
        "short_names": ["orch"],
        "output": "chart/agentickube/templates/crd-orchestrator.yaml",
    },
]


def _write_crd(crd_def: dict, yaml_module, *, stdout: bool = False) -> None:
    spec_cls = crd_def["spec_cls"]
    schema = _build_openapi_schema(spec_cls, crd_def["description"])
    crd = _crd_document(
        schema,
        crd_name=crd_def["crd_name"],
        group=crd_def["group"],
        plural=crd_def["plural"],
        singular=crd_def["singular"],
        kind=crd_def["kind"],
        short_names=crd_def["short_names"],
    )

    yaml_str = yaml_module.dump(
        crd,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )

    if stdout:
        print(yaml_str)
    else:
        out_path = Path(crd_def["output"])
        out = out_path if out_path.is_absolute() else _repo_root / out_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(yaml_str, encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Agent and Orchestrator CRDs from Pydantic models"
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write YAML to stdout instead of files",
    )
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 1

    for crd_def in CRDS:
        _write_crd(crd_def, yaml, stdout=args.stdout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
