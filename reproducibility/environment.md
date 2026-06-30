# Environment

Main experiment environment:

- Python: 3.9+ recommended
- Operating system: Linux/EC2 environment used for main runs
- Cloud API: Amazon Bedrock through `boto3`
- AWS region: `us-east-1`
- Dependencies: see `requirements.txt`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Environment variables

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
```

Example model argument:

```bash
--models "us.amazon.nova-2-lite-v1:0"
```

AWS credentials should be configured outside the repository.

Do not commit AWS credentials, `.env` files, PEM files, raw predictions, request IDs, local cloud logs, or unsanitized model outputs.
