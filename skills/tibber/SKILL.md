---
name: tibber-energy-optimizer
description: Use this skill when a user asks about Tibber, electricity prices, power consumption patterns, or wants energy-saving recommendations based on hourly usage and cost data.
---

# Tibber Energy Optimizer Skill

## Purpose
Retrieve Tibber electricity data and produce a concise analysis with actionable optimization tips.

## Configuration
Before use, verify these environment variables:

- `TIBBER_API_TOKEN` (personal access token from Tibber Developer settings)

## Workflow
1. Call `get_tibber_energy_analysis` with a relevant `days` window.
2. Return user-facing explanations in Swedish.
3. Keep tool output labels and technical fields in English.
4. Include practical, concrete actions for load shifting and cost reduction.

## Recommended default
- `days: 7`

Use `days: 14` or `days: 30` for broader trend analysis.
