# Contract2Tool

Contract2Tool is an experimental framework for learning lightweight tool contracts for tool-augmented LLM agents.

A tool contract contains:

- `requires`: task-state variables needed before a tool can be used
- `produces`: task-state variables produced after successful tool use
- `risk`: coarse risk level such as low, medium, or high
- `cost`: optional coarse cost/latency label

The current experiment evaluates whether Bedrock models can infer tool contracts from tool evidence such as tool name, description, schema, documentation, or traces, then scores predictions against gold contracts.

## Repository contents

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
└── code/
    └── contract2tool_intrinsic_bedrock.py
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

For a public release, prefer `contract_predictions_scored.csv` and `intrinsic_metrics_by_model_evidence.csv` over raw JSONL predictions.

## License

This repository is released under the MIT License.
