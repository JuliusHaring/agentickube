"""
Generate deploy/crd.yaml from the operator's Pydantic models (single source of truth).

Usage (from repo root):
  PYTHONPATH=code/operator python code/operator/crd_gen.py -o deploy/crd.yaml
  task operator:generate-crd

After changing code/operator/models.py, run the generator to refresh the CRD.
Add Field(description=...) and Literal[...] in models to get CRD descriptions and enums.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

# Add operator dir for imports when run as script or module
_operator_dir = Path(__file__).resolve().parent
_repo_root = _operator_dir.parents[1]
if str(_operator_dir) not in sys.path:
    sys.path.insert(0, str(_operator_dir))

from models import AgentSpec  # noqa: E402 (path must be set before import)


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


def _build_crd_openapi_schema() -> dict:
    """Build Kubernetes-compatible openAPIV3Schema: no $ref, no definitions, no type: null."""
    raw = AgentSpec.model_json_schema(mode="serialization")
    spec_schema = _json_schema_to_openapi(raw)

    definitions = dict(spec_schema.get("definitions", {}))
    agent_spec = {
        k: v for k, v in spec_schema.items() if k not in ("definitions", "$defs")
    }
    if agent_spec:
        definitions["AgentSpec"] = agent_spec

    # Inline spec: replace $ref to AgentSpec with the full schema (and inline all nested $refs)
    spec_inlined = _inline_refs({"$ref": "#/definitions/AgentSpec"}, definitions)

    # Convert anyOf [T, null] -> nullable: true
    spec_inlined = _anyof_null_to_nullable(spec_inlined)

    # Root CR: only spec at top level; no definitions (K8s forbids them)
    root = {
        "type": "object",
        "description": "Agent custom resource (ai.juliusharing.com).",
        "properties": {"spec": spec_inlined},
        "required": ["spec"],
    }

    _strip_titles_and_default_null(root)
    return root


def _crd_document(openapi_schema: dict) -> dict:
    """Full CustomResourceDefinition document."""
    return {
        "apiVersion": "apiextensions.k8s.io/v1",
        "kind": "CustomResourceDefinition",
        "metadata": {
            "name": "agents.ai.juliusharing.com",
        },
        "spec": {
            "group": "ai.juliusharing.com",
            "scope": "Namespaced",
            "names": {
                "plural": "agents",
                "singular": "agent",
                "kind": "Agent",
                "shortNames": ["ag"],
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Agent CRD from Pydantic models"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("deploy/crd.yaml"),
        help="Output path for CRD YAML (default: deploy/crd.yaml)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write YAML to stdout instead of file",
    )
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 1

    openapi_schema = _build_crd_openapi_schema()
    crd = _crd_document(openapi_schema)

    # Kubernetes-style YAML (no flow style, consistent indent)
    yaml_str = yaml.dump(
        crd,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )

    if args.stdout:
        print(yaml_str)
    else:
        out = args.output if args.output.is_absolute() else _repo_root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(yaml_str, encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
