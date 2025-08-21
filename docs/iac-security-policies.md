# IaC Security Policies & Controls

## Tools & Scanning
- **Tool:** Terraform v1.0+
- **Scanner:** Trivy (`trivy config ./`)
- **Policy Enforcement:** Fail pipeline on any critical misconfigurations.

## Implemented Security Controls

### 1. Compute (EC2)
- **IMDSv2 Enforcement:** Required to prevent SSRF attacks.
- **Encrypted Root Volume:** Data at rest encryption enabled.
- **No Public IP:** Instances are launched in private subnets.
- **Detailed Monitoring:** Enabled for better visibility.

### 2. Networking (Security Groups)
- **Least Privilege:** Ingress only allowed from the Load Balancer security group on port 5000.
- **Egress Restricted:** Limited to necessary traffic.

### 3. Secrets Management
- **AWS Credentials:** Passed via GitHub Secrets to Terraform.
- **No Hardcoded Secrets:** All sensitive values are parameterized.

## Policy Validation
The Terraform code is validated against these policies automatically in the CI/CD pipeline (`iac-scan` job).