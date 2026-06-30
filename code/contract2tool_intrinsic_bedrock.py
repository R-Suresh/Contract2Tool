#!/usr/bin/env python3
"""
Contract2Tool intrinsic experiment.

Loads a tool registry from an existing Python module, asks Bedrock models to infer
lightweight tool contracts from evidence views, normalizes predictions, and scores
them against gold contracts.

Example:
python3 -u code/contract2tool_intrinsic_bedrock.py \
  --module_path /home/ec2-user/scaledExperiment_main.py \
  --models "us.amazon.nova-2-lite-v1:0" \
  --evidence "name,metadata,schema" \
  --out_dir results_contract2tool_intrinsic_smoke
"""

import argparse
import csv
import importlib.util
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import boto3


# -----------------------------
# Helpers: loading tool registry
# -----------------------------

def load_module_from_path(module_path: str):
    module_path = os.path.abspath(module_path)
    spec = importlib.util.spec_from_file_location("source_experiment_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(module_path))
    spec.loader.exec_module(module)
    return module


def first_present(d: Dict[str, Any], keys: List[str], default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def get_tool_name(tool: Dict[str, Any]) -> str:
    return str(first_present(tool, ["name", "tool_name", "id"], "unknown_tool"))


def get_tool_description(tool: Dict[str, Any]) -> str:
    return str(first_present(tool, ["description", "desc", "summary"], ""))


def get_tool_schema(tool: Dict[str, Any]) -> Dict[str, Any]:
    schema = first_present(tool, ["input_schema", "inputSchema", "schema", "parameters"], {})
    if isinstance(schema, dict):
        return schema
    return {"raw_schema": str(schema)}


def get_gold_requires(tool: Dict[str, Any]) -> List[str]:
    value = first_present(
        tool,
        ["requires", "required_state", "required_vars", "preconditions", "required"],
        [],
    )
    return normalize_list_like(value)


def get_gold_produces(tool: Dict[str, Any]) -> List[str]:
    value = first_present(
        tool,
        ["produces", "produced_state", "produced_vars", "effects", "outputs"],
        [],
    )
    return normalize_list_like(value)


def get_gold_risk(tool: Dict[str, Any]) -> str:
    value = first_present(tool, ["risk", "risk_level", "rho"], "low")
    return normalize_risk(str(value))


def get_gold_cost(tool: Dict[str, Any]) -> str:
    value = first_present(tool, ["cost", "cost_level", "latency", "k"], "low")
    return normalize_cost(str(value))


def normalize_list_like(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    if isinstance(value, set):
        return [str(x) for x in value]
    if isinstance(value, tuple):
        return [str(x) for x in value]
    if isinstance(value, str):
        if not value.strip():
            return []
        return [x.strip() for x in value.split(",") if x.strip()]
    return [str(value)]


# -----------------------------
# Normalization
# -----------------------------

def canonicalize_var(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def normalize_risk(s: str) -> str:
    s = canonicalize_var(s)
    if s in {"critical", "dangerous"}:
        return "high"
    if s in {"med", "moderate"}:
        return "medium"
    if s not in {"low", "medium", "high"}:
        return "low"
    return s


def normalize_cost(s: str) -> str:
    s = canonicalize_var(s)
    if s in {"cheap", "small", "fast"}:
        return "low"
    if s in {"med", "moderate"}:
        return "medium"
    if s in {"expensive", "slow"}:
        return "high"
    if s not in {"low", "medium", "high"}:
        return "low"
    return s


def build_vocab(tools: List[Dict[str, Any]]) -> Set[str]:
    vocab = set()
    for t in tools:
        for x in get_gold_requires(t) + get_gold_produces(t):
            vocab.add(canonicalize_var(x))
    return vocab


def normalize_vars(values: Any, vocab: Set[str]) -> Tuple[List[str], List[str]]:
    """Returns (normalized_values, unresolved_values)."""
    raw = normalize_list_like(values)
    normalized = []
    unresolved = []

    for item in raw:
        c = canonicalize_var(item)
        if not c:
            continue
        if c in vocab:
            normalized.append(c)
            continue
        c2 = re.sub(r"_id$", "_id", c)
        if c2 in vocab:
            normalized.append(c2)
            continue
        unresolved.append(c)

    return sorted(set(normalized)), sorted(set(unresolved))


# -----------------------------
# Evidence construction
# -----------------------------

def build_synthetic_doc(tool: Dict[str, Any]) -> str:
    """Synthetic docs deliberately use only public-facing fields, not gold requires/produces."""
    name = get_tool_name(tool)
    desc = get_tool_description(tool)
    schema = get_tool_schema(tool)
    return (
        f"API documentation for `{name}`.\n"
        f"Purpose: {desc}\n"
        f"Input/output schema: {json.dumps(schema, sort_keys=True)}\n"
        "Use this tool only when its operation matches the current workflow step."
    )


def build_evidence(tool: Dict[str, Any], condition: str) -> Dict[str, Any]:
    name = get_tool_name(tool)
    desc = get_tool_description(tool)
    schema = get_tool_schema(tool)

    if condition == "name":
        return {"name": name}
    if condition == "metadata":
        return {"name": name, "description": desc}
    if condition == "schema":
        return {"name": name, "description": desc, "schema": schema}
    if condition == "docs":
        docs = first_present(tool, ["documentation", "docs", "doc"], None)
        if docs is None:
            docs = build_synthetic_doc(tool)
        return {"name": name, "description": desc, "schema": schema, "documentation": docs}
    if condition == "traces":
        traces = first_present(tool, ["traces", "execution_traces"], [])
        return {"name": name, "traces": traces}
    if condition == "hybrid":
        docs = first_present(tool, ["documentation", "docs", "doc"], None)
        if docs is None:
            docs = build_synthetic_doc(tool)
        traces = first_present(tool, ["traces", "execution_traces"], [])
        return {
            "name": name,
            "description": desc,
            "schema": schema,
            "documentation": docs,
            "traces": traces,
        }
    raise ValueError(f"Unknown evidence condition: {condition}")


# -----------------------------
# Bedrock invocation
# -----------------------------

def make_prompt(tool_evidence: Dict[str, Any], vocab: Set[str]) -> str:
    allowed = sorted(vocab)
    return f"""
You are inferring a lightweight tool contract for an LLM agent tool.

A tool contract contains:
- requires: task-state variables that must be known before the tool can be used
- produces: task-state variables produced after successful use
- risk: one of ["low", "medium", "high"]
- cost: one of ["low", "medium", "high"]

Allowed task-state variables:
{json.dumps(allowed)}

Tool evidence:
{json.dumps(tool_evidence, indent=2, sort_keys=True)}

Return ONLY valid JSON with this exact shape:
{{
  "requires": ["..."],
  "produces": ["..."],
  "risk": "low|medium|high",
  "cost": "low|medium|high"
}}

Rules:
- Use only variables from the allowed task-state variable list.
- If no preconditions are needed, use an empty list.
- If no effects can be inferred, use an empty list.
- Do not include explanations or markdown.
""".strip()


def extract_text_from_converse_response(resp: Dict[str, Any]) -> str:
    parts = resp.get("output", {}).get("message", {}).get("content", [])
    texts = []
    for p in parts:
        if "text" in p:
            texts.append(p["text"])
    return "\n".join(texts).strip()


def invoke_bedrock(client, model_id: str, prompt: str, max_tokens: int = 700) -> Tuple[str, Dict[str, Any]]:
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    kwargs = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": 0.0,
        },
    }

    try:
        resp = client.converse(**kwargs)
    except Exception as e:
        msg = str(e)
        if "temperature" in msg.lower() or "inference" in msg.lower() or "extraneous" in msg.lower():
            kwargs["inferenceConfig"] = {"maxTokens": max_tokens}
            resp = client.converse(**kwargs)
        else:
            raise

    return extract_text_from_converse_response(resp), resp.get("usage", {})


def parse_json_contract(raw: str) -> Tuple[Dict[str, Any], bool]:
    text = raw.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        obj = json.loads(text)
        return obj, True
    except Exception:
        pass

    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            return obj, True
        except Exception:
            pass

    return {}, False


# -----------------------------
# Scoring
# -----------------------------

def prf(pred: Set[str], gold: Set[str]) -> Tuple[float, float, float]:
    if not pred and not gold:
        return 1.0, 1.0, 1.0
    if not pred and gold:
        return 0.0, 0.0, 0.0
    if pred and not gold:
        return 0.0, 0.0, 0.0

    tp = len(pred & gold)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def score_row(row: Dict[str, Any]) -> Dict[str, Any]:
    pred_req = set(row["pred_requires"])
    pred_prod = set(row["pred_produces"])
    gold_req = set(row["gold_requires"])
    gold_prod = set(row["gold_produces"])

    req_p, req_r, req_f1 = prf(pred_req, gold_req)
    prod_p, prod_r, prod_f1 = prf(pred_prod, gold_prod)

    risk_acc = 1.0 if row["pred_risk"] == row["gold_risk"] else 0.0
    cost_acc = 1.0 if row["pred_cost"] == row["gold_cost"] else 0.0

    exact = (
        pred_req == gold_req
        and pred_prod == gold_prod
        and row["pred_risk"] == row["gold_risk"]
    )

    return {
        "requires_precision": req_p,
        "requires_recall": req_r,
        "requires_f1": req_f1,
        "produces_precision": prod_p,
        "produces_recall": prod_r,
        "produces_f1": prod_f1,
        "risk_accuracy": risk_acc,
        "cost_accuracy": cost_acc,
        "exact_match": 1.0 if exact else 0.0,
    }


def write_jsonl(path: Path, rows: List[Dict[str, Any]]):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]]):
    if not rows:
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def aggregate(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["evidence"])].append(r)

    out = []
    metric_keys = [
        "requires_precision",
        "requires_recall",
        "requires_f1",
        "produces_precision",
        "produces_recall",
        "produces_f1",
        "risk_accuracy",
        "cost_accuracy",
        "exact_match",
        "valid_json",
        "normalization_ok",
    ]

    for (model, evidence), items in sorted(groups.items()):
        agg = {"model": model, "evidence": evidence, "n": len(items)}
        for k in metric_keys:
            agg[k] = sum(float(x.get(k, 0.0)) for x in items) / len(items)
        out.append(agg)

    return out


# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module_path", required=True, help="Path to Python module containing TOOLS")
    parser.add_argument("--tools_var", default="TOOLS")
    parser.add_argument("--models", required=True, help="Comma-separated Bedrock model IDs/profile IDs")
    parser.add_argument("--evidence", default="name,metadata,schema", help="Comma-separated evidence conditions")
    parser.add_argument("--out_dir", default="results_contract2tool_intrinsic")
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1",
    )
    parser.add_argument("--limit_tools", type=int, default=0, help="For smoke tests. 0 means all tools.")
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    module = load_module_from_path(args.module_path)
    tools = getattr(module, args.tools_var)

    if args.limit_tools and args.limit_tools > 0:
        tools = tools[: args.limit_tools]

    print(f"Loaded tools: {len(tools)}")
    print(f"Region: {args.region}")

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    evidence_conditions = [e.strip() for e in args.evidence.split(",") if e.strip()]

    print("Models:")
    for m in models:
        print(f"  - {m}")

    print("Evidence conditions:")
    for e in evidence_conditions:
        print(f"  - {e}")

    vocab = build_vocab(tools)
    print(f"State-variable vocab size: {len(vocab)}")

    client = boto3.client("bedrock-runtime", region_name=args.region)

    raw_rows = []
    scored_rows = []

    total = len(tools) * len(models) * len(evidence_conditions)
    idx = 0

    for model in models:
        for evidence in evidence_conditions:
            for tool in tools:
                idx += 1
                tool_name = get_tool_name(tool)
                print(f"[{idx}/{total}] model={model} evidence={evidence} tool={tool_name}")

                gold_requires = sorted({canonicalize_var(x) for x in get_gold_requires(tool)})
                gold_produces = sorted({canonicalize_var(x) for x in get_gold_produces(tool)})
                gold_risk = get_gold_risk(tool)
                gold_cost = get_gold_cost(tool)

                tool_evidence = build_evidence(tool, evidence)
                prompt = make_prompt(tool_evidence, vocab)

                error = ""
                raw_text = ""
                usage = {}
                parsed = {}
                valid_json = False

                try:
                    raw_text, usage = invoke_bedrock(client, model, prompt)
                    parsed, valid_json = parse_json_contract(raw_text)
                except Exception as e:
                    error = str(e)

                pred_requires, unresolved_req = normalize_vars(parsed.get("requires", []), vocab)
                pred_produces, unresolved_prod = normalize_vars(parsed.get("produces", []), vocab)
                pred_risk = normalize_risk(str(parsed.get("risk", "low")))
                pred_cost = normalize_cost(str(parsed.get("cost", "low")))

                normalization_ok = 1.0 if not unresolved_req and not unresolved_prod else 0.0

                row = {
                    "model": model,
                    "evidence": evidence,
                    "tool_name": tool_name,
                    "gold_requires": gold_requires,
                    "gold_produces": gold_produces,
                    "gold_risk": gold_risk,
                    "gold_cost": gold_cost,
                    "pred_requires": pred_requires,
                    "pred_produces": pred_produces,
                    "pred_risk": pred_risk,
                    "pred_cost": pred_cost,
                    "unresolved_requires": unresolved_req,
                    "unresolved_produces": unresolved_prod,
                    "valid_json": 1.0 if valid_json else 0.0,
                    "normalization_ok": normalization_ok,
                    "input_tokens": usage.get("inputTokens", ""),
                    "output_tokens": usage.get("outputTokens", ""),
                    "error": error,
                    "raw_output": raw_text,
                }

                score = score_row(row)
                row.update(score)

                raw_rows.append(row)
                scored_rows.append({k: v for k, v in row.items() if k not in {"raw_output"}})

                time.sleep(args.sleep)

    raw_path = out_dir / "contract_predictions_raw.jsonl"
    scored_path = out_dir / "contract_predictions_scored.csv"
    agg_path = out_dir / "intrinsic_metrics_by_model_evidence.csv"

    write_jsonl(raw_path, raw_rows)
    write_csv(scored_path, scored_rows)
    write_csv(agg_path, aggregate(scored_rows))

    print("\nDone.")
    print(f"Wrote raw predictions: {raw_path}")
    print(f"Wrote scored rows:     {scored_path}")
    print(f"Wrote aggregate:       {agg_path}")

    print("\nQuick aggregate:")
    for r in aggregate(scored_rows):
        print(
            f"{r['model'][:45]:45s} | {r['evidence']:8s} | "
            f"req_f1={r['requires_f1']:.2f} prod_f1={r['produces_f1']:.2f} "
            f"risk={r['risk_accuracy']:.2f} exact={r['exact_match']:.2f} "
            f"valid={r['valid_json']:.2f}"
        )


if __name__ == "__main__":
    main()
