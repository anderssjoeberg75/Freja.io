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
    in_scope_assets: list[str] = Field(
        default_factory=list,
        description="Explicit in-scope hosts, domains, APIs, repositories, and cloud accounts.",
    )
    out_of_scope_assets: list[str] = Field(
        default_factory=list,
        description="Assets that must never be touched during testing.",
    )
    authenticated_testing_allowed: bool = Field(
        False,
        description="Whether authenticated testing is allowed for approved accounts.",
    )
    production_target: bool = Field(
        True,
        description="Whether testing is against production assets.",
    )
    primary_stack: list[str] = Field(
        default_factory=list,
        description="Technology hints, e.g. nginx, react, fastapi, aws, postgresql.",
    )


class ReportSchema(BaseModel):
    target: str = Field(..., description="Target domain or system.")
    summary: str = Field(..., description="Short high-level summary of what was found.")
    findings_markdown: str = Field(
        ..., description="Markdown bullet list of findings with severity and evidence."
    )
    overall_risk_rating: Literal["critical", "high", "medium", "low"] = Field(
        "medium",
        description="Overall risk rating based on validated findings.",
    )
    retest_required_within_days: int = Field(
        30,
        ge=1,
        le=365,
        description="Target deadline for fix validation retest.",
    )


def cybersecurity_assessment_blueprint_impl(
    target: str,
    objective: str,
    authorization_confirmed: bool,
    testing_intensity: str = "standard",
    anonymized_routing_requested: bool = False,
    in_scope_assets: list[str] | None = None,
    out_of_scope_assets: list[str] | None = None,
    authenticated_testing_allowed: bool = False,
    production_target: bool = True,
    primary_stack: list[str] | None = None,
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

    in_scope_assets = in_scope_assets or []
    out_of_scope_assets = out_of_scope_assets or []
    primary_stack = primary_stack or []

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

    auth_mode = (
        "Use approved least-privileged test accounts to increase vulnerability coverage "
        "for authorization, session handling, and access-control testing."
        if authenticated_testing_allowed
        else "Unauthenticated-only testing. Expect reduced coverage for access-control issues."
    )

    environment_controls = (
        "Production target detected: enforce strict rate limits, maintenance window, and live monitoring."
        if production_target
        else "Non-production target: broader validation depth is possible with change control."
    )

    stack_focus = ", ".join(primary_stack) if primary_stack else "Not specified"
    in_scope = ", ".join(in_scope_assets) if in_scope_assets else "Not provided"
    out_scope = ", ".join(out_of_scope_assets) if out_of_scope_assets else "Not provided"

    return (
        f"# Authorized Security Assessment Blueprint\n"
        f"- Target: {target}\n"
        f"- Objective: {objective}\n"
        f"- Testing profile: {testing_intensity}\n\n"
        "## Scope Declaration\n"
        f"- In scope: {in_scope}\n"
        f"- Out of scope: {out_scope}\n"
        f"- Primary stack: {stack_focus}\n"
        f"- Authenticated testing: {'Yes' if authenticated_testing_allowed else 'No'}\n"
        f"- Environment: {'Production' if production_target else 'Non-production'}\n\n"
        "## Guardrails\n"
        "- Execute only within signed scope and approved schedule.\n"
        "- No persistence, no privilege escalation attempts, no denial-of-service actions.\n"
        "- Capture evidence safely and redact personal or regulated data.\n\n"
        "## Coverage and Effectiveness Controls\n"
        f"- {auth_mode}\n"
        f"- {environment_controls}\n"
        "- Track test coverage by vulnerability family to reduce blind spots.\n"
        "- Require reproducible proof for each finding and at least one false-positive check.\n"
        "- Map validated findings to OWASP ASVS/CWE to improve remediation precision.\n\n"
        "## Routing & Identity\n"
        f"- {routing_guidance}\n\n"
        "## Recommended Workflow\n"
        "1. Pre-engagement: validate scope, contacts, backups, and monitoring thresholds.\n"
        f"2. Discovery: {intensity_controls.get(testing_intensity, intensity_controls['standard'])}\n"
        "3. Validation: confirm findings with reproducible low-risk checks and confidence rating.\n"
        "4. Reporting: assign severity (CVSS), business impact, and remediation owner.\n"
        "5. Retest: verify fixes and close findings with evidence.\n\n"
        "## Vulnerability Coverage Matrix\n"
        "1. Identity and access: authn/authz flaws, session controls, MFA bypass paths.\n"
        "2. Input and API security: injection, SSRF, deserialization, schema validation gaps.\n"
        "3. Data protection: weak crypto, insecure transport, sensitive data exposure.\n"
        "4. Infrastructure posture: exposed services, TLS weaknesses, cloud misconfiguration.\n"
        "5. Supply chain and secrets: vulnerable dependencies, leaked keys, CI/CD exposure.\n\n"
        "## Suggested Defensive Tooling\n"
        "- Surface mapping: amass (authorized), asset inventory, DNS change monitoring.\n"
        "- Web checks: OWASP ZAP baseline scan, Nuclei safe templates, SSLyze.\n"
        "- Hardening: dependency scanning, secret scanning, MFA and rate-limit validation.\n"
        "- IaC/Cloud: Checkov or tfsec, CSPM controls, IAM policy analyzers."
    )


def cybersecurity_generate_report_impl(
    target: str,
    summary: str,
    findings_markdown: str,
    overall_risk_rating: str = "medium",
    retest_required_within_days: int = 30,
) -> str:
    """Generate an executive + technical report template from provided findings."""
    return (
        f"# Security Assessment Report\n\n"
        f"## Target\n{target}\n\n"
        f"## Executive Summary\n{summary}\n\n"
        f"## Overall Risk Rating\n{overall_risk_rating.capitalize()}\n\n"
        "## Findings\n"
        f"{findings_markdown}\n\n"
        "## Validation Quality Standard\n"
        "- Every finding should include severity, confidence, impacted asset, evidence, and reproduction notes.\n"
        "- Mark findings as `Needs Verification` when confidence is low to prevent noisy remediation work.\n\n"
        "## Remediation Program\n"
        "1. Fix internet-exposed critical issues within 24-72 hours.\n"
        "2. Add compensating controls (WAF rules, rate limits, temporary ACLs).\n"
        "3. Improve detection (SIEM alerts, anomaly detection, auth abuse alerts).\n"
        "4. Introduce security tests in CI/CD (SAST, dependency, IaC, and secret scans).\n"
        f"5. Run a scoped retest within {retest_required_within_days} days and document residual risk accepted by stakeholders.\n\n"
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
