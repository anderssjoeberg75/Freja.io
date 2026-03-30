"""Core helpers for authorized pentest reconnaissance."""

from __future__ import annotations

import asyncio
import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlparse

import requests


COMMON_RISKY_PORTS = {
    21: "FTP may allow weak authentication or clear-text credentials.",
    23: "Telnet transmits credentials in clear text.",
    445: "SMB can expose legacy vulnerabilities and lateral movement paths.",
    3389: "RDP exposure increases brute-force risk.",
    5900: "VNC is often exposed with weak/no authentication.",
}

SECURITY_HEADERS = {
    "Strict-Transport-Security": "Missing HSTS can allow protocol-downgrade attacks.",
    "Content-Security-Policy": "Missing CSP increases XSS impact.",
    "X-Content-Type-Options": "Missing nosniff can enable MIME confusion.",
    "X-Frame-Options": "Missing frame protections can allow clickjacking.",
    "Referrer-Policy": "Missing referrer policy can leak sensitive URL data.",
}


@dataclass(slots=True)
class ReconResult:
    target: str
    ip_address: str
    checked_ports: list[int]
    open_ports: list[int]
    findings: list[str]


def _extract_hostname(target: str) -> str:
    value = target.strip()
    if not value:
        raise ValueError("Target cannot be empty.")

    if "://" in value:
        parsed = urlparse(value)
        if not parsed.hostname:
            raise ValueError("Invalid target URL; cannot extract hostname.")
        return parsed.hostname

    # Allow host:port input.
    if ":" in value and value.count(":") == 1 and value.rsplit(":", 1)[1].isdigit():
        return value.rsplit(":", 1)[0]

    return value


def _parse_ports(port_expression: str) -> list[int]:
    expression = (port_expression or "").strip()
    if not expression:
        raise ValueError("Ports expression cannot be empty.")

    ports: set[int] = set()
    for part in expression.split(","):
        chunk = part.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_text, end_text = chunk.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise ValueError(f"Invalid port range '{chunk}'.")
            ports.update(range(start, end + 1))
        else:
            ports.add(int(chunk))

    filtered = sorted(port for port in ports if 1 <= port <= 65535)
    if not filtered:
        raise ValueError("No valid ports to scan.")

    if len(filtered) > 2048:
        raise ValueError("Port range too large. Limit scans to 2048 ports per request.")

    return filtered


def _scan_ports(ip_address: str, ports: Iterable[int], timeout_seconds: float) -> list[int]:
    open_ports: list[int] = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout_seconds)
            result = sock.connect_ex((ip_address, port))
            if result == 0:
                open_ports.append(port)
    return open_ports


def _run_web_checks(target: str, hostname: str, findings: list[str]) -> None:
    candidate_urls = []
    if target.startswith("http://") or target.startswith("https://"):
        candidate_urls.append(target)
    else:
        candidate_urls.extend([f"https://{hostname}", f"http://{hostname}"])

    response = None
    last_error = None
    for url in candidate_urls:
        try:
            response = requests.get(url, timeout=8, allow_redirects=True)
            break
        except Exception as exc:  # pragma: no cover - network variability
            last_error = exc
            continue

    if response is None:
        findings.append(f"Web checks skipped: could not fetch target URL ({last_error}).")
        return

    for header_name, warning in SECURITY_HEADERS.items():
        if header_name not in response.headers:
            findings.append(f"Missing security header '{header_name}': {warning}")

    if response.url.startswith("http://"):
        findings.append("Application resolved to HTTP without TLS; traffic may be intercepted.")


def _run_tls_checks(hostname: str, findings: list[str]) -> None:
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, 443), timeout=8) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
                not_after = cert.get("notAfter") if isinstance(cert, dict) else None
                if not_after:
                    expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    days_left = (expires - datetime.now(tz=timezone.utc)).days
                    if days_left < 14:
                        findings.append(f"TLS certificate expires soon ({days_left} days).")
    except Exception as exc:  # pragma: no cover - network variability
        findings.append(f"TLS checks not completed: {exc}")


def _format_report(result: ReconResult) -> str:
    lines = [
        "Ethical Pentest Recon Report",
        "Authorization reminder: run scans only against systems you own or are explicitly authorized to test.",
        f"- Target: {result.target}",
        f"- Resolved IP: {result.ip_address}",
        f"- Checked TCP ports: {len(result.checked_ports)}",
        f"- Open TCP ports: {', '.join(str(p) for p in result.open_ports) if result.open_ports else 'None found'}",
    ]

    risky_open = [port for port in result.open_ports if port in COMMON_RISKY_PORTS]
    if risky_open:
        lines.append("- Exposed high-risk services:")
        for port in risky_open:
            lines.append(f"  - {port}/tcp: {COMMON_RISKY_PORTS[port]}")

    if result.findings:
        lines.append("- Findings:")
        for item in result.findings:
            lines.append(f"  - ⚠️ {item}")
    else:
        lines.append("- Findings: No obvious issues detected in this lightweight recon pass.")

    lines.append("- Next step: validate findings with authenticated scans and manual verification.")
    return "\n".join(lines)


def _run_recon_sync(target: str, ports: str, timeout_seconds: float, include_web_checks: bool) -> str:
    hostname = _extract_hostname(target)
    ip_address = socket.gethostbyname(hostname)
    parsed_ports = _parse_ports(ports)
    open_ports = _scan_ports(ip_address=ip_address, ports=parsed_ports, timeout_seconds=timeout_seconds)

    findings: list[str] = []
    for port in open_ports:
        if port in COMMON_RISKY_PORTS:
            findings.append(f"Port {port}/tcp is externally reachable.")

    if include_web_checks:
        _run_web_checks(target=target, hostname=hostname, findings=findings)
        _run_tls_checks(hostname=hostname, findings=findings)

    result = ReconResult(
        target=target,
        ip_address=ip_address,
        checked_ports=parsed_ports,
        open_ports=open_ports,
        findings=findings,
    )
    return _format_report(result)


async def run_pentest_recon(target: str, ports: str, timeout_seconds: float, include_web_checks: bool) -> str:
    """Run an authorized recon pass and summarize potential vulnerabilities."""
    return await asyncio.to_thread(_run_recon_sync, target, ports, timeout_seconds, include_web_checks)
