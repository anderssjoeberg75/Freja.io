# Cybersecurity Skill

This skill is designed for **authorized defensive security work**.

## Purpose

- Build a safe assessment blueprint before a penetration test.
- Enforce authorization checks.
- Improve finding quality and vulnerability coverage.
- Generate remediation-focused reports after validated findings.

## Included tools

### `cybersecurity_assessment_blueprint`
Creates a legally constrained and operationally safe plan.

**Important behavior**:
- If `authorization_confirmed` is `false`, the tool refuses testing instructions and returns defensive prep steps.
- If anonymized routing is requested, it recommends auditable, company-controlled routing instead of attacker-style anonymity.
- Supports explicit scoping (`in_scope_assets`, `out_of_scope_assets`) and depth controls for production/non-production testing.
- Improves effectiveness by adding a vulnerability coverage matrix across access control, API/input, data protection, infrastructure, and supply chain.

### `cybersecurity_generate_report`
Creates a concise report with:
- Executive summary
- Overall risk rating
- Findings section
- Validation quality standard
- Remediation program
- Prevention checklist

## Recommended usage pattern

1. Confirm written authorization and in-scope assets.
2. Run `cybersecurity_assessment_blueprint` with scope details and allowed testing mode.
3. Execute approved checks externally (outside this skill).
4. Collect findings with severity + confidence + evidence.
5. Run `cybersecurity_generate_report` and set a retest deadline.
6. Track remediation and perform retest closure.
