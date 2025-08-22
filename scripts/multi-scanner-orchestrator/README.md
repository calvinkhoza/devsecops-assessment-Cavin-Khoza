# Multi-Scanner Orchestrator

A script to orchestrate multiple security tools (SAST, SCA, Secrets) into a single scan with a unified pass/fail output. Ideal for integrating into CI/CD pipelines.

## Prerequisites

1. **Python 3.8+**
2. Install the required tools system-wide or in your virtual environment:
    ```bash
    pip install bandit safety detect-secrets
    ```

## Usage

Run the script against a target directory:

```bash
# Basic run with JSON output (for CI/CD)
python3 security-scan.py --path /path/to/your/code --format json

# Human-readable output
python3 security-scan.py --path ./app --format text