# Garmin API Capability Review for Morning Briefing and Health Analysis

Date: 2026-03-17

## Scope

This review compares:

1. What Garmin publicly says is available in the Garmin Connect Developer Program / Health API.
2. What Freja currently fetches from Garmin.
3. What Freja actually uses in:
   - morning briefing context generation,
   - user-facing Garmin health analysis.

## 1) Publicly advertised Garmin Health API data categories

Based on Garmin's public developer pages, the Health API includes all-day summaries and more granular feeds such as:

- steps,
- heart rate,
- sleep,
- stress,
- calories,
- respiration,
- body composition,
- pulse-ox,
- epoch summaries,
- and potentially second-level heart-rate detail during activities.

## 2) Data Freja already fetches from Garmin today

### Core daily report (`get_health_report`)

Freja currently fetches and normalizes:

- date, steps, step goal, distance,
- resting heart rate,
- stress average/max,
- HRV status,
- body battery now/high/low,
- sleep total + stage splits + sleep window + sleep score,
- calories,
- intensity minutes,
- SpO2 average.

### Advanced report (`get_advanced_report`)

Freja also fetches:

- training readiness,
- training status,
- race predictions,
- VO2 max,
- endurance score,
- hill score,
- fitness age,
- HRV nightly + weekly avg + status,
- hydration,
- SpO2 availability flag,
- respiration summary,
- personal records count.

## 3) Data used in current outputs

### Morning briefing currently uses a subset

Morning briefing includes selected Garmin fields:

- steps/goal,
- sleep and sleep score,
- body battery now,
- resting heart rate,
- HRV status,
- stress average,
- calories,
- and selected advanced metrics if available.

### Gaps between fetched data and used data in morning briefing

Freja fetches but does not currently include (or only minimally includes) in briefing text:

- sleep stage breakdown (REM/deep/light/awake),
- sleep start/end regularity trend,
- body battery high/low range,
- stress max and stress duration/rest stress duration,
- distance and intensity minutes,
- floors ascended/goal,
- min/max/avg heart-rate summary,
- respiration values as structured metric (currently only text summary),
- SpO2 levels (currently mostly boolean presence in advanced section),
- hydration trend deltas (only current day values are included).

### Health analysis tool usage

The Garmin tool returns raw health JSON plus advanced metrics to the LLM and instructs it to analyze values. This is strong coverage, but data quality can still improve if more normalized fields are exposed consistently (instead of mixed strings/booleans/text blobs).

## 4) Highest-value additional Garmin data to include next

If Garmin project access allows subscription to these feeds, the following should produce the biggest value for morning briefing and health analysis:

1. **Epoch summaries** (high value)
   - Better daily pattern analysis (when stress peaks, inactivity blocks, recovery windows).
2. **Detailed pulse-ox feed** (high value)
   - Night-time oxygen variability, not just daily average/presence.
3. **Detailed stress timeline** (high value)
   - Time-in-zone and stress episodes improve actionable recommendations.
4. **Body composition from Garmin-compatible devices** (medium value)
   - Could reduce reliance on another provider where Garmin scale data exists.
5. **Second-level heart-rate during activities** (medium-high value)
   - Better exercise load interpretation when paired with Strava activity context.

## 5) Implementation recommendations (prioritized)

### Priority A — no API contract change needed

Use already fetched fields more fully:

- Add sleep stage breakdown and sleep window consistency note in briefing.
- Add distance + intensity minutes + floor progress.
- Add stress max and body battery high/low delta.
- Replace advanced SpO2 boolean with numeric daily avg/low/latest when available.

### Priority B — normalize advanced metrics for better LLM analysis

- Return respiration as numeric fields (`avg`, `low`, `high`) instead of a sentence string.
- Return race predictions in human-readable pace/time format alongside seconds.
- Include trend direction labels for HRV/training readiness where source supports it.

### Priority C — Garmin Health API feed expansion

In Garmin Developer Portal subscription settings, evaluate and enable additional feed types:

- epoch summaries,
- detailed stress,
- detailed pulse-ox,
- body composition,
- high-resolution HR during activities.

Then add ingestion + persistence + briefing usage for top-priority metrics.

## 6) Bottom line

Yes — there is likely more Garmin data to extract and use than Freja currently uses in morning briefing and health analysis. The largest near-term gain comes from **using more of the data Freja already fetches**, followed by enabling **epoch/stress/pulse-ox granular feeds** in the Garmin Health API subscription if not already enabled.
