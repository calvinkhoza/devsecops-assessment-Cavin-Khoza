#!/usr/bin/env python3
"""
Runs Bandit, Trivy, and Gitleaks. Always passes (exit 0) and reports findings.
"""

import subprocess
import json
import sys
import argparse
import os

def run_cmd(cmd):
    """Runs a shell command. Returns output, error, and return code."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout, None, result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode
    except Exception as e:
        return None, str(e), -1

def main():
    parser = argparse.ArgumentParser(description='Multi-Scanner Orchestrator')
    parser.add_argument('--path', default='.', help='Path to scan (default: current directory)')
    parser.add_argument('--format', choices=['json', 'text'], default='json', help='Output format (default: json)')
    args = parser.parse_args()

    scan_path = os.path.abspath(args.path)
    if not os.path.exists(scan_path):
        print(f"Error: Path '{scan_path}' does not exist.")
        sys.exit(1)

    results = {
        'sast': {'findings': [], 'error': None, 'tool': 'bandit'},
        'dependencies': {'findings': [], 'error': None, 'tool': 'trivy'},
        'secrets': {'findings': [], 'error': None, 'tool': 'gitleaks'},
        'pass': True
    }

    # 1. Run Bandit (SAST)
    print("[*] Running sast scan...")
    bandit_cmd = f"bandit -r {scan_path} -f json --quiet"
    bandit_out, bandit_err, bandit_code = run_cmd(bandit_cmd)
    
    # Bandit handling - always try to parse results regardless of exit code
    try:
        bandit_data = json.loads(bandit_out)
        results['sast']['findings'] = bandit_data.get('results', [])
    except json.JSONDecodeError:
        results['sast']['error'] = f"Bandit output not JSON: {bandit_out[:200]}..."
        # If we can't parse JSON, check if there's stderr content
        if bandit_err and "ERROR" in bandit_err:
            results['sast']['error'] = bandit_err

    # 2. Run Trivy (Dependencies)
    print("[*] Running dependencies scan...")
    trivy_cmd = f"trivy fs {scan_path} --severity HIGH,CRITICAL --format json"
    trivy_out, trivy_err, trivy_code = run_cmd(trivy_cmd)
    
    # Trivy handling - always try to parse results
    try:
        trivy_data = json.loads(trivy_out)
        results['dependencies']['findings'] = trivy_data
    except json.JSONDecodeError:
        # If JSON parsing fails, check if there are vulnerabilities in text output
        if "HIGH" in trivy_out or "CRITICAL" in trivy_out:
            results['dependencies']['findings'] = [{"message": "High/Critical vulnerabilities found"}]
        elif trivy_err:
            results['dependencies']['error'] = f"Trivy error: {trivy_err[:200]}..."

    # 3. Run Gitleaks (Secrets)
    print("[*] Running secrets scan...")
    gitleaks_cmd = f"gitleaks detect --source {scan_path} --no-git --format json"
    gitleaks_out, gitleaks_err, gitleaks_code = run_cmd(gitleaks_cmd)
    
    # Gitleaks handling - always try to parse results
    try:
        gitleaks_data = json.loads(gitleaks_out)
        results['secrets']['findings'] = gitleaks_data
    except json.JSONDecodeError:
        # If JSON parsing fails, check if secrets were found in stderr
        if "leak" in gitleaks_err or "secret" in gitleaks_err:
            results['secrets']['findings'] = [{"message": "Secrets detected"}]
        elif gitleaks_err:
            results['secrets']['error'] = f"Gitleaks error: {gitleaks_err[:200]}..."

    # Calculate totals
    total_findings = len(results['sast']['findings']) + len(results['dependencies']['findings']) + len(results['secrets']['findings'])
    has_errors = results['sast']['error'] or results['dependencies']['error'] or results['secrets']['error']
    
    results['total_findings'] = total_findings
    results['has_errors'] = has_errors

    # Output - ALWAYS use text format for clear pipeline logs
    print(f"\n--- Security Scan Summary ---")
    print(f"SAST Issues: {len(results['sast']['findings'])}")
    print(f"Dependency Vulnerabilities: {len(results['dependencies']['findings'])}")
    print(f"Secrets Found: {len(results['secrets']['findings'])}")
    print(f"Total Findings: {total_findings}")
    
    # Show errors as warnings, but don't fail
    if results['sast']['error']:
        print(f"⚠️  SAST Warning: {results['sast']['error']}")
    if results['dependencies']['error']:
        print(f"⚠️  Dependency Warning: {results['dependencies']['error']}")
    if results['secrets']['error']:
        print(f"⚠️  Secrets Warning: {results['secrets']['error']}")
    
    if total_findings > 0:
        print(f"🔍 Security findings detected. Please review the logs.")
    else:
        print(f"✅ No security findings detected.")
    
    print(f"Status: COMPLETED (exit 0)")

    # ALWAYS exit with code 0 - we never fail the pipeline
    # The findings are reported for review, but don't block execution
    sys.exit(0)

if __name__ == '__main__':
    main()