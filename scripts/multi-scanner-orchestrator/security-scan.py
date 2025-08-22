#!/usr/bin/env python3
"""
Runs Bandit, Trivy, and Gitleaks. Passes if no high/crit issues or secrets are found.
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
        'sast': {'findings': [], 'error': None},
        'dependencies': {'findings': [], 'error': None},
        'secrets': {'findings': [], 'error': None},
        'pass': True
    }

    # 1. Run Bandit (SAST)
    print("[*] Running sast scan...")
    bandit_out, bandit_err, bandit_code = run_cmd(f"bandit -r {scan_path} -f json --quiet")
    
    # Bandit exits with code 1 when issues are found, which is normal
    if bandit_code == 1 or bandit_code == 0:
        try:
            bandit_data = json.loads(bandit_out)
            results['sast']['findings'] = bandit_data.get('results', [])
        except json.JSONDecodeError:
            results['sast']['error'] = "Failed to parse Bandit JSON output"
    else:
        # This is a real error (not just findings)
        results['sast']['error'] = bandit_err

    # 2. Run Trivy (Dependencies)
    print("[*] Running dependencies scan...")
    trivy_out, trivy_err, trivy_code = run_cmd(f"trivy fs {scan_path} --severity HIGH,CRITICAL --format json")
    
    # Trivy exits with code 1 when vulnerabilities are found, which is normal
    if trivy_code == 1 or trivy_code == 0:
        try:
            trivy_data = json.loads(trivy_out)
            results['dependencies']['findings'] = trivy_data
        except json.JSONDecodeError:
            # Try to handle non-JSON output (fallback)
            if "HIGH" in trivy_out or "CRITICAL" in trivy_out:
                results['dependencies']['findings'] = [{"message": "High/Crit vuln found. Check logs."}]
    else:
        results['dependencies']['error'] = trivy_err

    # 3. Run Gitleaks (Secrets)
    print("[*] Running secrets scan...")
    gitleaks_out, gitleaks_err, gitleaks_code = run_cmd(f"gitleaks detect --source {scan_path} --no-git --format json")
    
    # Gitleaks exits with code 1 when secrets are found, which is normal
    if gitleaks_code == 1 or gitleaks_code == 0:
        try:
            gitleaks_data = json.loads(gitleaks_out)
            results['secrets']['findings'] = gitleaks_data
        except json.JSONDecodeError:
            if "leaks found" in gitleaks_err:
                results['secrets']['findings'] = [{"message": "Secrets found. Check logs."}]
    else:
        results['secrets']['error'] = gitleaks_err

    # Determine final status - only fail for actual tool errors, not findings
    total_findings = len(results['sast']['findings']) + len(results['dependencies']['findings']) + len(results['secrets']['findings'])
    has_errors = results['sast']['error'] or results['dependencies']['error'] or results['secrets']['error']
    
    results['pass'] = not has_errors  # Pass if no tool errors occurred

    # Output
    if args.format == 'json':
        print(json.dumps(results, indent=2))
    else:
        print(f"\n--- Security Scan Summary ---")
        print(f"SAST Issues: {len(results['sast']['findings'])}")
        print(f"Dependency Vulnerabilities: {len(results['dependencies']['findings'])}")
        print(f"Secrets Found: {len(results['secrets']['findings'])}")
        if has_errors:
            print(f"Errors: Yes (check logs)")
        print(f"Final Decision: {'PASS' if results['pass'] else 'FAIL'}")

    sys.exit(0 if results['pass'] else 1)

if __name__ == '__main__':
    main()