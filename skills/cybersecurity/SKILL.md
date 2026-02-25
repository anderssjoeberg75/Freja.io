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

## Tools

### `cybersecurity_assessment_blueprint`
Input:
- target
- objective
- authorization_confirmed
- testing_intensity
- anonymized_routing_requested

Behavior:
- Refuses offensive guidance without authorization.
- Returns a constrained, auditable testing blueprint when authorization is confirmed.

### `cybersecurity_generate_report`
Input:
- target
- summary
- findings_markdown

Behavior:
- Produces a practical, remediation-first report suitable for technical and business stakeholders.
