"""Defensive cybersecurity tools for authorized engagements."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.services.tool_registry import ToolRegistry


class AssessmentBlueprintSchema(BaseModel):
    target: str = Field(..., description="Target domain or system in scope.")
    objective: str = Field(..., description="Business goal for the assessment.")
    authorization_confirmed: bool = Field(
        ..., description="True only when written authorization is present."
    )
    testing_intensity: Literal["passive", "standard", "careful_active"] = Field(
        "standard",
        description="How invasive checks are allowed to be, based on signed scope.",
    )
    anonymized_routing_requested: bool = Field(
        False,
        description="Whether anonymized routing (for example WireGuard) was requested.",
    )


class ReportSchema(BaseModel):
    target: str = Field(..., description="Target domain or system.")
    summary: str = Field(..., description="Short high-level summary of what was found.")
    findings_markdown: str = Field(
        ..., description="Markdown bullet list of findings with severity and evidence."
    )


def cybersecurity_assessment_blueprint_impl(
    target: str,
    objective: str,
    authorization_confirmed: bool,
    testing_intensity: str = "standard",
    anonymized_routing_requested: bool = False,
) -> str:
    """Create a safe, defensive assessment plan with strict authorization gating."""
    if not authorization_confirmed:
        return (
            "Authorization is required before any security testing.\n\n"
            "I can only help with defensive preparation until written permission is confirmed:\n"
            "1. Define legal scope (hosts, paths, testing window, out-of-scope assets).\n"
            "2. Prepare a rollback and incident response contact list.\n"
            "3. Run internal hardening checks using CIS benchmarks and OWASP ASVS.\n"
            "4. Schedule a formal authorized pentest with signed rules of engagement."
        )

    routing_guidance = (
        "Use transparent, auditable routing from approved tester infrastructure."
    )
    if anonymized_routing_requested:
        routing_guidance = (
            "Do not anonymize tester identity for production targets. "
            "Prefer allowlisted source IPs with full audit logging. "
            "If WireGuard is required, use a company-controlled tunnel endpoint and retain logs."
        )

    intensity_controls = {
        "passive": "Passive-only checks (headers, TLS config, robots, exposed metadata).",
        "standard": "Standard authenticated assessment without exploit execution.",
        "careful_active": "Careful active validation in maintenance window with rollback plan.",
    }

    return (
        f"# Authorized Security Assessment Blueprint\n"
        f"- Target: {target}\n"
        f"- Objective: {objective}\n"
        f"- Testing profile: {testing_intensity}\n\n"
        "## Guardrails\n"
        "- Execute only within signed scope and approved schedule.\n"
        "- No persistence, no privilege escalation attempts, no denial-of-service actions.\n"
        "- Capture evidence safely and redact personal or regulated data.\n\n"
        "## Routing & Identity\n"
        f"- {routing_guidance}\n\n"
        "## Recommended Workflow\n"
        "1. Pre-engagement: validate scope, contacts, backups, and monitoring thresholds.\n"
        f"2. Discovery: {intensity_controls.get(testing_intensity, intensity_controls['standard'])}\n"
        "3. Validation: confirm findings with reproducible low-risk checks.\n"
        "4. Reporting: assign severity (CVSS), business impact, and remediation owner.\n"
        "5. Retest: verify fixes and close findings with evidence.\n\n"
        "## Suggested Defensive Tooling\n"
        "- Surface mapping: amass (authorized), asset inventory, DNS change monitoring.\n"
        "- Web checks: OWASP ZAP baseline scan, Nuclei safe templates, SSLyze.\n"
        "- Hardening: dependency scanning, secret scanning, MFA and rate-limit validation."
    )


def cybersecurity_generate_report_impl(
    target: str,
    summary: str,
    findings_markdown: str,
) -> str:
    """Generate an executive + technical report template from provided findings."""
    return (
        f"# Security Assessment Report\n\n"
        f"## Target\n{target}\n\n"
        f"## Executive Summary\n{summary}\n\n"
        "## Findings\n"
        f"{findings_markdown}\n\n"
        "## Remediation Program\n"
        "1. Fix internet-exposed critical issues within 24-72 hours.\n"
        "2. Add compensating controls (WAF rules, rate limits, temporary ACLs).\n"
        "3. Improve detection (SIEM alerts, anomaly detection, auth abuse alerts).\n"
        "4. Introduce security tests in CI/CD (SAST, dependency, IaC, and secret scans).\n"
        "5. Run a scoped retest and document residual risk accepted by stakeholders.\n\n"
        "## Prevention Checklist\n"
        "- Enforce MFA for admin paths and VPN.\n"
        "- Apply least privilege and short-lived credentials.\n"
        "- Keep patch SLAs by severity.\n"
        "- Protect login and API endpoints with anti-automation controls.\n"
        "- Maintain offline backups and tested incident-response playbooks."
    )


def register_tools(registry: ToolRegistry) -> None:
    """Register cybersecurity skill tools."""
    registry.register(
        name="cybersecurity_assessment_blueprint",
        description=(
            "Create an authorization-gated defensive security assessment blueprint. "
            "Refuses testing guidance when authorization is missing."
        ),
        args_schema=AssessmentBlueprintSchema,
    )(cybersecurity_assessment_blueprint_impl)

    registry.register(
        name="cybersecurity_generate_report",
        description="Create a structured remediation-focused security report.",
        args_schema=ReportSchema,
    )(cybersecurity_generate_report_impl)
