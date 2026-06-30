# Reproducibility Notes

This document describes the public reproducibility package for **Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents**.

The goal of this repository is to provide clean, arXiv-compatible code and curated artifacts for reproducing the Contract2Tool experiments. It is not intended to be a dump of raw internal run traces or cloud execution logs.

## Repository layout

```text
.
├── code/
│   └── contract2tool_intrinsic_bedrock.py
├── reproducibility/
│   ├── run_config_main.json
│   └── environment.md
├── results/
│   ├── contract_predictions_scored_name_metadata_schema_9models.csv
│   ├── intrinsic_metrics_name_metadata_schema_9models.csv
│   ├── contract_predictions_scored_docs_9models.csv
│   ├── intrinsic_metrics_docs_9models.csv
│   ├── contract_predictions_scored_traces_hybrid_4models.csv
│   ├── intrinsic_metrics_traces_hybrid_4models.csv
│   └── results_intrinsic_merged_clean.csv
├── README.md
├── REPRODUCIBILITY.md
├── CITATION.cff
├── LICENSE
├── requirements.txt
└── .gitignore
```

Additional curated folders may be added later if needed:

```text
data/
tables/
figures/
```

## What is included

The repository currently includes:

- Main intrinsic Contract2Tool experiment runner
- README with setup and run commands
- Curated scored result CSVs
- Curated aggregate result CSVs
- Reproducibility notes
- Citation metadata
- Environment documentation
- Git ignore rules that exclude raw traces, credentials, and generated logs

## Public result artifacts

The public result artifacts are:

```text
results/contract_predictions_scored_name_metadata_schema_9models.csv
results/intrinsic_metrics_name_metadata_schema_9models.csv
results/contract_predictions_scored_docs_9models.csv
results/intrinsic_metrics_docs_9models.csv
results/contract_predictions_scored_traces_hybrid_4models.csv
results/intrinsic_metrics_traces_hybrid_4models.csv
results/results_intrinsic_merged_clean.csv
```

The scored CSVs contain normalized predictions and derived metrics but exclude the raw model completion field. The aggregate CSVs summarize metrics by model and evidence condition. The merged clean aggregate excludes failed/end-of-life model runs.

## What is intentionally excluded

The repository should not include unsanitized raw traces or cloud execution logs.

Excluded artifacts include:

- AWS credentials
- `.env` files
- PEM/key files
- Bedrock request IDs
- raw Bedrock/API response metadata
- unsanitized model outputs
- raw `contract_predictions_raw.jsonl` unless carefully inspected and sanitized
- local EC2 shell history
- personal notes
- review-submission metadata
- any double-blind review information

## Main experiment

The main runner is:

```bash
python3 -u code/contract2tool_intrinsic_bedrock.py
```

The runner loads a Python module containing a `TOOLS` variable. Each tool is treated as the gold source for contract fields such as `requires`, `produces`, `risk`, and `cost`.

The model is then asked to infer a contract from one or more evidence conditions:

- `name`
- `metadata`
- `schema`
- `docs`
- `traces`
- `hybrid`

The runner normalizes predicted contracts and scores them against the gold contract fields.

## Environment setup

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

The experiment uses Amazon Bedrock through `boto3`. Configure AWS credentials outside the repository.

Example environment variables:

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
```

## Smoke test

Example smoke test:

```bash
python3 -u code/contract2tool_intrinsic_bedrock.py \
  --module_path /home/ec2-user/scaledExperiment_main.py \
  --models "us.amazon.nova-2-lite-v1:0" \
  --evidence "metadata" \
  --limit_tools 5 \
  --out_dir results_smoke_metadata
```

## Full intrinsic run

Example full run:

```bash
python3 -u code/contract2tool_intrinsic_bedrock.py \
  --module_path /home/ec2-user/scaledExperiment_main.py \
  --models "us.amazon.nova-2-lite-v1:0" \
  --evidence "name,metadata,schema" \
  --out_dir results_contract2tool_intrinsic
```

The run writes:

```text
contract_predictions_raw.jsonl
contract_predictions_scored.csv
intrinsic_metrics_by_model_evidence.csv
```

## Public artifact policy

For public release, prefer curated and derived files such as:

```text
results/contract_predictions_scored_*.csv
results/intrinsic_metrics_*.csv
results/results_intrinsic_merged_clean.csv
reproducibility/run_config_main.json
reproducibility/environment.md
```

Do not upload by default:

```text
contract_predictions_raw.jsonl
results_*/
*.log
.aws/
.env
*.pem
*.key
```

## Sanitizing run artifacts

Before uploading any artifact generated on EC2 or through Bedrock, inspect it for:

- Request IDs
- Account IDs
- ARNs
- access keys
- session tokens
- local file paths
- hostnames
- IP addresses
- raw prompts
- raw model completions
- provider response metadata
- timestamps that reveal internal execution details
- review or submission metadata

For the public reproducibility package, prefer scored CSVs and aggregate summaries over raw JSONL predictions.

## Suggested validation checklist before release

Before tagging a release, check that the repository does not contain sensitive or raw files.

Files that should not be tracked include:

```text
.pem
.key
.env
raw_traces
contract_predictions_raw.jsonl
.aws
.log
```

Search tracked files for common secrets or metadata patterns before release.

## Release target

Recommended release tag:

```text
v1.0-arxiv
```

Recommended release title:

```text
v1.0-arxiv: Reproducibility package for Contract2Tool
```

Recommended release description:

```text
This release contains the public reproducibility package for the arXiv version of Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents.

It includes the intrinsic experiment runner, reproducibility notes, environment documentation, citation metadata, and curated artifacts if available.

Raw traces, raw model outputs, cloud logs, and credentials are intentionally excluded.
```
