# Cybersecurity Skill

This skill is designed for **authorized defensive security work**.

## Purpose

- Build a safe assessment blueprint before a penetration test.
- Enforce authorization checks.
- Generate remediation-focused reports after validated findings.

## Included tools

### `cybersecurity_assessment_blueprint`
Creates a legally constrained and operationally safe plan.

**Important behavior**:
- If `authorization_confirmed` is `false`, the tool refuses testing instructions and returns defensive prep steps.
- If anonymized routing is requested, it recommends auditable, company-controlled routing instead of attacker-style anonymity.

### `cybersecurity_generate_report`
Creates a concise report with:
- Executive summary
- Findings section
- Remediation program
- Prevention checklist

## Example workflow

1. Confirm written authorization and in-scope assets.
2. Run `cybersecurity_assessment_blueprint`.
3. Execute approved checks externally (outside this skill).
4. Collect findings and pass them to `cybersecurity_generate_report`.
5. Track remediation and perform retest.
