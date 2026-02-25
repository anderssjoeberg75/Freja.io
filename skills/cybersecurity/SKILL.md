---
name: Cybersecurity
description: Authorized defensive security assessment planning and reporting.
---

# Cybersecurity Skill

Use this skill only for authorized security engagements.

## Safety and legal requirements

- Require explicit written authorization before any testing support.
- Never provide stealth, persistence, phishing, credential theft, or exploitation playbooks.
- Keep recommendations focused on risk reduction, validation hygiene, and remediation.

## Effectiveness requirements

- Prefer authenticated testing (with least-privileged approved accounts) when allowed to improve detection of access-control flaws.
- Track explicit in-scope and out-of-scope assets to prevent scope drift.
- Require reproducible evidence and confidence rating per finding to reduce false positives.
- Map findings to recognized standards (OWASP ASVS/CWE/CVSS) for consistent prioritization.

## Tools

### `cybersecurity_assessment_blueprint`
Input:
- target
- objective
- authorization_confirmed
- testing_intensity
- anonymized_routing_requested
- in_scope_assets
- out_of_scope_assets
- authenticated_testing_allowed
- production_target
- primary_stack

Behavior:
- Refuses testing guidance without authorization.
- Returns a constrained, auditable testing blueprint when authorization is confirmed.
- Adds vulnerability coverage controls and stack-aware focus areas.

### `cybersecurity_generate_report`
Input:
- target
- summary
- findings_markdown
- overall_risk_rating
- retest_required_within_days

Behavior:
- Produces a practical, remediation-first report suitable for technical and business stakeholders.
- Enforces quality gates for findings (severity, confidence, evidence, reproducibility).
