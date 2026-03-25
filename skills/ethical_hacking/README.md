# Ethical Hacking Skill

## What this skill does

The Ethical Hacking skill enables Freja to run lightweight, authorized penetration-testing recon against a target host or URL. It focuses on fast vulnerability signal detection, not exploitation.

## Registered Freja tool

- `run_pentest_recon`

## How to use it via Freja

### Natural language examples

- `Run a pentest recon against https://example.com and check common web vulnerabilities.`
- `Scan 22,80,443,3389 on corp.example.org and tell me what looks risky.`
- `Perform an authorized vulnerability check for 10.0.0.25.`

### Direct tool call (internal)

```json
{
  "tool": "run_pentest_recon",
  "args": {
    "target": "https://example.com",
    "ports": "1-1024",
    "timeout_seconds": 0.5,
    "include_web_checks": true
  }
}
```

## Safety notes

- Use only with explicit authorization from the system owner.
- This skill performs reconnaissance checks only; findings require manual verification.
- Missing headers or open ports are indicators, not definitive proof of exploitable vulnerabilities.
