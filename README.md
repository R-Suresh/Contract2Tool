# Contract2Tool

Contract2Tool is an experimental framework for learning lightweight tool contracts for tool-augmented LLM agents.

A tool contract contains:

- `requires`: task-state variables needed before a tool can be used
- `produces`: task-state variables produced after successful tool use
- `risk`: coarse risk level such as low, medium, or high
- `cost`: optional coarse cost/latency label

The current experiment evaluates whether Bedrock models can infer tool contracts from tool evidence such as tool name, description, and schema, then scores predictions against gold contracts.

## Current experiment

```bash
python3 -u experiments/contract2tool_intrinsic_bedrock.py \
  --module_path /home/ec2-user/scaledExperiment_main.py \
  --models "us.amazon.nova-2-lite-v1:0" \
  --evidence "metadata" \
  --limit_tools 5 \
  --out_dir results_smoke_metadata
