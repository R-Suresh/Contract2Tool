# Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents

**Authors:** Rahul Suresh Babu and Laxmipriya Ganesh Iyer  
**arXiv:** [2606.07904](https://arxiv.org/abs/2606.07904)  
**Repository:** Public reproducibility package for the Contract2Tool arXiv paper  
**License:** MIT

## At a glance

Contract2Tool studies whether large language models can infer lightweight tool contracts from tool evidence such as tool name, metadata, schema, documentation, and execution traces.

A tool contract contains:

- `requires`: task-state variables needed before a tool can be used
- `produces`: task-state variables produced after successful tool use
- `risk`: coarse risk level such as low, medium, or high
- `cost`: optional coarse cost/latency label

## Headline public results

The public artifact release contains curated scored CSVs and aggregate summaries over 100 tools per evaluated model/evidence condition. Raw model completions are intentionally excluded.

Key headline results from the released aggregate artifacts:

- Schema and documentation evidence often recover preconditions very strongly; several evaluated configurations reach `requires_f1 = 1.00`.
- The strongest released configuration is `us.anthropic.claude-opus-4-8` with documentation evidence, reaching `requires_f1 = 1.00`, `produces_f1 = 0.9557`, `risk_accuracy = 0.82`, and `exact_match = 0.75`.
- The strongest schema-based released configuration is also `us.anthropic.claude-opus-4-8`, reaching `requires_f1 = 1.00`, `produces_f1 = 0.9540`, `risk_accuracy = 0.79`, and `exact_match = 0.72`.
- The merged clean aggregate excludes failed or end-of-life model runs; raw JSONL predictions and raw provider metadata are not part of the public release.

## Why this matters

Tool-augmented LLM agents are increasingly deployed with large tool libraries. Contract2Tool provides a way to infer compact precondition/effect contracts that can support safer tool filtering, better orchestration, and more reliable agent execution.

## Repository contents

```text
.
├── README.md
├── REPRODUCIBILITY.md
├── CITATION.cff
├── LICENSE
├── requirements.txt
├── .gitignore
├── code/
│   └── contract2tool_intrinsic_bedrock.py
├── reproducibility/
│   ├── run_config_main.json
│   └── environment.md
└── results/
    ├── contract_predictions_scored_name_metadata_schema_9models.csv
    ├── intrinsic_metrics_name_metadata_schema_9models.csv
    ├── contract_predictions_scored_docs_9models.csv
    ├── intrinsic_metrics_docs_9models.csv
    ├── contract_predictions_scored_traces_hybrid_4models.csv
    ├── intrinsic_metrics_traces_hybrid_4models.csv
    └── results_intrinsic_merged_clean.csv
```

## Main experiment

The main runner is:

```bash
python3 -u code/contract2tool_intrinsic_bedrock.py
```

The script loads a tool registry from an existing Python module containing a `TOOLS` variable. It then asks Bedrock models to infer contracts under one or more evidence conditions and evaluates the predictions against the gold contracts already present in the tool registry.

Supported evidence conditions:

- `name`
- `metadata`
- `schema`
- `docs`
- `traces`
- `hybrid`

## Setup

Create a Python environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

The experiment uses Amazon Bedrock through `boto3`. Configure AWS credentials outside this repository. Do not commit AWS credentials, `.env` files, PEM files, local cloud configuration, raw model traces, or request metadata.

Example region configuration:

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
```

## Smoke test

Example smoke run on five tools:

```bash
python3 -u code/contract2tool_intrinsic_bedrock.py \
  --module_path /home/ec2-user/scaledExperiment_main.py \
  --models "us.amazon.nova-2-lite-v1:0" \
  --evidence "metadata" \
  --limit_tools 5 \
  --out_dir results_smoke_metadata
```

## Full intrinsic experiment

Example full run:

```bash
python3 -u code/contract2tool_intrinsic_bedrock.py \
  --module_path /home/ec2-user/scaledExperiment_main.py \
  --models "us.amazon.nova-2-lite-v1:0" \
  --evidence "name,metadata,schema" \
  --out_dir results_contract2tool_intrinsic
```

The output directory contains:

```text
contract_predictions_raw.jsonl
contract_predictions_scored.csv
intrinsic_metrics_by_model_evidence.csv
```

## Public results

The public repository includes curated scored and aggregate result CSVs.

```text
results/contract_predictions_scored_name_metadata_schema_9models.csv
results/intrinsic_metrics_name_metadata_schema_9models.csv
results/contract_predictions_scored_docs_9models.csv
results/intrinsic_metrics_docs_9models.csv
results/contract_predictions_scored_traces_hybrid_4models.csv
results/intrinsic_metrics_traces_hybrid_4models.csv
results/results_intrinsic_merged_clean.csv
```

These files intentionally exclude raw model completions. The merged clean aggregate excludes failed/end-of-life model runs.

## Citation

If you use this repository or artifact package, please cite:

```text
Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents
Rahul Suresh Babu and Laxmipriya Ganesh Iyer
arXiv: 2606.07904
```

The machine-readable citation metadata is available in `CITATION.cff`.

## Public artifact policy

This repository is intended to contain clean reproducibility code and curated artifacts only.

Do not upload:

- AWS credentials or `.env` files
- PEM/key files
- raw Bedrock request metadata
- unsanitized raw model outputs
- raw `contract_predictions_raw.jsonl` unless carefully inspected and sanitized
- local EC2 paths beyond illustrative run commands
- review-submission metadata

For a public release, prefer scored CSVs and aggregate summaries over raw JSONL predictions.

## License

This repository is released under the MIT License.
