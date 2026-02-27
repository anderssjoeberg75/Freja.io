---
description: Kör ett komplett cybersecurity-test mot en domän
---

# Hacka-workflow

Utförs när användaren skriver något i stil med "hacka <domän>" eller "testa säkerheten på <domän>".

Extrahera domännamnet från meddelandet och kör följande steg i ordning:

## Steg 1 – Säkerhetsplan
Anropa `cybersecurity_assessment_blueprint` med:
- `target` = domännamnet
- `authorization_confirmed` = true (förutsätt att användaren äger/har tillstånd för sin egen domän)
- `testing_intensity` = "standard"
- `production_target` = true om det inte är uppenbart lokalt (t.ex. `.local`-suffix → false)
- `objective` = "Identifiera säkerhetsbrister och öppna tjänster"

## Steg 2 – Passiv Recon
Anropa `cybersecurity_run_passive_recon` med:
- `target` = domännamnet
- `authorization_confirmed` = true
- `fetch_http_headers` = true

## Steg 3 – Tolka recon och poängsätt fynd
Baserat på recon-resultatet, identifiera de viktigaste fynden och anropa `cybersecurity_calculate_cvss` för varje signifikant fynd (t.ex. öppna databas-portar, saknad HTTPS, saknade säkerhetsheaders). Presentera resultaten i en tabell.

## Steg 4 – Generera rapport
Anropa `cybersecurity_generate_report` med:
- `target` = domännamnet
- `summary` = en kort sammanfattning baserad på recon och CVSS-resultat
- `findings_markdown` = en Markdown-lista med alla fynd och deras CVSS-scores
- `overall_risk_rating` = baserat på det högsta CVSS-poänget (≥9.0=critical, ≥7.0=high, ≥4.0=medium, annars low)
- `retest_required_within_days` = 30

Avsluta med att berätta för användaren var rapporten sparades och ge en sammanfattning av de tre viktigaste åtgärderna.
