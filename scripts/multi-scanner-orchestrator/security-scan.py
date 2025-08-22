#!/usr/bin/env python3
"""
Multi-Scanner Orchestrator
Runs SAST (Bandit), Dependency Check (safety), and Secrets Scan (detect-secrets) on a given path.
Aggregates results into a unified JSON report with a final pass/fail decision.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

# Tool configurations - Simulating a config file for clarity
TOOLS = {
    "sast": {"command": ["bandit", "-r", "-f", "json", "."], "cwd": True},
    "dependencies": {"command": ["safety", "check", "--json"], "cwd": False},
    "secrets": {"command": ["detect-secrets", "scan", "--all-files", "--json"], "cwd": True},
}

def run_command(cmd: List[str], cwd: str = None) -> Dict[str, Any]:
    """Execute a shell command and return its JSON output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300  # 5-minute timeout per tool
        )
        if result.returncode == 0:
            try:
                return {"success": True, "data": json.loads(result.stdout)}
            except json.JSONDecodeError:
                return {"success": True, "data": result.stdout}
        else:
            return {"success": False, "error": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": f"Tool not installed: {cmd[0]}"}

def run_scans(path: str) -> Dict[str, Any]:
    """Run all configured security scans."""
    scan_path = Path(path).absolute()
    results = {}

    for tool_name, config in TOOLS.items():
        print(f"[*] Running {tool_name} scan...")
        tool_cwd = str(scan_path) if config["cwd"] else None
        tool_result = run_command(config["command"], cwd=tool_cwd)
        results[tool_name] = tool_result

    return results

def make_decision(scan_results: Dict[str, Any]) -> str:
    """Make a pass/fail decision based on scan results."""
    # Define failure thresholds
    FAILURE_CONDITIONS = {
        "sast": lambda r: len(r.get('results', [])) > 0, # Fail if any Bandit issues found
        "dependencies": lambda r: len(r.get('vulnerabilities', [])) > 0, # Fail if any vulns
        "secrets": lambda r: len(r.get('results', {})) > 0, # Fail if any secrets found
    }

    for tool, result_data in scan_results.items():
        if not result_data["success"]:
            print(f"[!] {tool} scan failed to run: {result_data.get('error')}")
            return "fail" # Fail the build if a tool errors

        data = result_data.get("data", {})
        check = FAILURE_CONDITIONS.get(tool)
        if check and check(data):
            print(f"[!] {tool} scan found issues.")
            return "fail"

    print("[+] All scans passed.")
    return "pass"

def main():
    parser = argparse.ArgumentParser(description="Multi-Scanner Security Orchestrator")
    parser.add_argument("--path", required=True, help="Path to the codebase to scan")
    parser.add_argument("--format", choices=['json', 'text'], default='json', help="Output format")
    args = parser.parse_args()

    if not Path(args.path).exists():
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)

    # Execute all scans
    all_results = run_scans(args.path)
    # Make the final decision
    decision = make_decision(all_results)

    # Prepare final output
    output = {
        "scan_results": all_results,
        "decision": decision,
        "summary": {
            "sast_issues": len(all_results.get('sast', {}).get('data', {}).get('results', [])),
            "dependency_vulns": len(all_results.get('dependencies', {}).get('data', {}).get('vulnerabilities', [])),
            "secrets_found": len(all_results.get('secrets', {}).get('data', {}).get('results', {})),
        }
    }

    if args.format == 'json':
        print(json.dumps(output, indent=2))
    else:
        print(f"\n--- Security Scan Summary ---")
        print(f"SAST Issues: {output['summary']['sast_issues']}")
        print(f"Dependency Vulnerabilities: {output['summary']['dependency_vulns']}")
        print(f"Secrets Found: {output['summary']['secrets_found']}")
        print(f"Final Decision: {decision.upper()}")

    # Exit with appropriate code for CI/CD
    sys.exit(0 if decision == 'pass' else 1)

if __name__ == "__main__":
    main()