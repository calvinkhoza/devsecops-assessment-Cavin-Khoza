# DevSecOps Technical Assessment Submission

This repository contains my submission for the DevSecOps Technical Assessment. It demonstrates practical implementation of security automation, CI/CD pipeline security, container security, and Infrastructure as Code (IaC) security.

## Blocks Completed

- [x] **Block 1: Security Automation** - Multi-Scanner Orchestrator
- [x] **Block 2: Pipeline Security** - GitHub Actions Secure Pipeline
- [x] **Block 3: Container Security** - Dockerfile & Docker Compose
- [x] **Block 4: Infrastructure as Code Security** - Terraform for AWS

## Overview of Solutions

### Block 1: Multi-Scanner Orchestrator
Located in `scripts/multi-scanner-orchestrator/`.
A Python script that orchestrates three security tools:
- **SAST:** Bandit for Python code scanning.
- **SCA:** Safety for Python dependency vulnerability checking.
- **Secrets Detection:** Detect-secrets for finding hardcoded credentials.
The script aggregates results and provides a unified pass/fail decision, perfect for CI/CD integration.

### Block 2: Pipeline Security
Located in `.github/workflows/secure-pipeline.yml`.
A GitHub Actions workflow that:
1.  Runs the Multi-Scanner Orchestrator as the first quality gate.
2.  Builds a Docker image only if the code is secure.
3.  Scans the built image for vulnerabilities using Trivy, failing on HIGH/CRITICAL issues.
4.  Scans Terraform configurations using TFSec.
Security is integrated early and throughout the pipeline.

### Block 3: Container Security
Located in `application/`.
- **Dockerfile:** A multi-stage build that creates a minimal, secure runtime image. It uses a non-root user, a slim base image, and has build-time security best practices.
- **Docker Compose:** `infrastructure/docker-compose.yml` defines a secure runtime configuration with dropped capabilities, a read-only filesystem, and no new privileges.

### Block 4: Infrastructure as Code Security
Located in `infrastructure/terraform/`.
Terraform code to provision a secure AWS S3 bucket for application logs. It implements:
- Versioning for recovery.
- Default AES-256 encryption.
- Complete blocking of all public access.
- Least-privilege IAM role creation for an ECS task.

## How to Run

### Prerequisites
- Python 3.8+
- Docker
- Docker Compose
- Terraform (for IaC testing)
- GitHub Account (for testing Actions)

### Local Security Scan
1.  Install the required tools:
    ```bash
    pip install bandit safety detect-secrets
    ```
2.  Run the orchestrator from the repository root:
    ```bash
    python3 ./scripts/multi-scanner-orchestrator/security-scan.py --path ./application --format text
    ```

### Build and Run the Container Locally
1.  Build the image:
    ```bash
    docker build -t devsecops-app:latest ./application
    ```
2.  Run it using the secure compose file:
    ```bash
    docker compose -f infrastructure/docker-compose.yml up
    ```
3.  Test the application: `curl http://localhost:8080`

### Running Terraform Code
1.  Navigate to the Terraform directory:
    ```bash
    cd infrastructure/terraform
    ```
2.  Initialize Terraform:
    ```bash
    terraform init
    ```
3.  Plan the infrastructure:
    ```bash
    terraform plan
    ```
    *Note: Requires AWS credentials configured.*

## Key Security Decisions

- **Shift-Left:** Security scanning happens immediately in the pipeline, preventing wasted cycles on insecure code.
- **Zero-Tolerance for Secrets/High-Risk Vulns:** The pipeline is configured to fail on any found secret, dependency vulnerability, or high/critical CVE. This enforces a high security bar.
- **Defense-in-Depth (Container):** The container is secured at build time (non-root user, minimal image) and at runtime (read-only, no capabilities).
- **Secure Defaults (IaC):** The Terraform code defines resources that are secure by default, following the principle of least privilege.

## Time Breakdown (Example)

- **Block 1:** 45 minutes (Script development and testing)
- **Block 2:** 35 minutes (Workflow design and integration)
- **Block 3:** 40 minutes (Dockerfile hardening and compose setup)
- **Block 4:** 30 minutes (Terraform module writing)
- **Documentation:** 15 minutes

## Problems I Ran Into

1.  **Gitleaks and Trivy exit with an error code if they find something**, which would break the script. I fixed this by catching those errors in my `run_cmd` function and still processing their output.
2.  **The `container-scan` job kept running even if the `security-scan` job failed.** I fixed it by adding `needs: security-scan` to the job config.
3.  **Making the container's filesystem read-only** broke the app. I learned about using `tmpfs` for `/tmp` and `/var/run` from an old blog post and it worked.

## Tools I Used

I used the standard tools: VS Code, a local terminal for testing, and the GitHub UI. I referenced the official docs for [GitHub Actions](https://docs.github.com/en/actions), [Docker](https://docs.docker.com/), and [Terraform](https://developer.hashicorp.com/terraform/docs) when I got stuck on syntax.