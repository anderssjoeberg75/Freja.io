---
name: ethical-hacking
description: Authorized pentesting reconnaissance for host/URL targets. Use when the user asks Freja to perform ethical hacking, vulnerability discovery, security posture checks, open-port assessment, or web security header/TLS checks in an approved environment.
---

# Ethical Hacking Skill

1. Confirm the scope is explicitly authorized before running any scan.
2. Use `run_pentest_recon` for fast reconnaissance and first-pass vulnerability detection.
3. Prefer narrow port ranges first (critical ports or 1-1024) before broad scans.
4. Report findings as risk indicators, not confirmed exploitation.
5. Recommend manual verification and authenticated security testing as the next step.

## Report checklist

- State target and resolved IP.
- List scanned ports and open ports.
- Flag risky exposed services (e.g., Telnet, SMB, RDP).
- Include web security header/TLS observations when web checks are enabled.
- Add an authorization reminder in the final response.
