# PostHog Self-driving setup report

## Summary

PostHog Self-driving is configured for StoryBuilder. Session Replay, Error Tracking, and Support were already enabled; the required native signal sources were also already enabled, so no source needed a new write. The focused scout troop, two StoryBuilder-specific scouts, and two Replay Vision monitors are active. Findings should start appearing in the [Self-driving inbox](https://us.posthog.com/project/322783/inbox) within about 30 minutes.

## AI data processing

Approved by the organization-level wizard gate.

## GitHub

Connected before this run through the PostHog GitHub App. The existing GitHub Issues responder remains enabled.

## Products enabled

| Product | Result | Notes |
| --- | --- | --- |
| Session Replay | Already enabled | This repository has no `posthog-js` client initialization; its Python SDK does not create browser recordings. Existing project recordings show Replay is active from a web source. |
| Error Tracking | Already enabled | StoryBuilder's Python client enables exception autocapture. |
| Support (Conversations) | Already enabled | The responder is armed, but tickets require an inbound Support channel. |

## Signal sources

| Source product | Source type | Action |
| --- | --- | --- |
| `health_checks` | `health_issue` | Already enabled. |
| `error_tracking` | `issue_created` | Already enabled. |
| `error_tracking` | `issue_reopened` | Already enabled. |
| `error_tracking` | `issue_spiking` | Already enabled. |
| `conversations` | `ticket` | Already enabled. |
| `signals_scout` | `cross_source_issue` | No config row exists; the scout gate is on by default. |
| `session_replay` | `session_analysis_cluster` | Deliberately skipped; this retired route is replaced by Replay Vision monitors. |
| `replay_vision` | scanner configuration | Deliberately skipped as a source row; each monitor authorizes its own inbox findings with `emits_signals: true`. |

Existing enabled responders retained without change: `github` / `issue` and `llm_analytics` / `evaluation_report`.

## Connected tools

The connected-tools prompt was shown and no additional tool was selected. No warehouse source or responder was added in this run. GitHub Issues was already connected and its responder was already enabled.

## Scout troop

**Verified budget:** 100 runs/day; 17 had run today and 83 remained at configuration time. Early-access banner: “Scouts are in early access. Each project gets up to 100 scout runs a day. Contact <team-self-driving@posthog.com> if you need more.”

### Active scouts (6)

| Scout | Coverage |
| --- | --- |
| General | Cross-product correlations and unassigned surfaces. |
| AI observability | LLM cost, latency, reliability, volume, and evaluation regressions. |
| Observability gaps | Important event streams missing insight, dashboard, or alert coverage. |
| Web analytics | Traffic, attribution, landing-page health, bounce, and 404 regressions. |
| `signals-scout-download-pipeline-health` | Story-download pipeline outcomes. |
| `signals-scout-tts-generation-health` | Text-to-speech batch outcomes. |

### Disabled built-in scouts (23)

| Scouts | Reason |
| --- | --- |
| Anomaly detection; Insight alerts | No evidence of a saved monitoring/alert surface to justify a separate recurring check. |
| APM; CSP violations; Logs; Web vitals | No confirmed product instrumentation for these surfaces. |
| Conversations; Customer analytics; Experiments; Feature flags; Revenue analytics; Surveys | No confirmed active use in this project. |
| Data pipelines; Data warehouse | No matching active pipeline or warehouse surface was found for this repository. |
| Error tracking | Covered by the enabled native Error Tracking responders. |
| Session replay | Covered by the two Replay Vision monitors below. |
| Replay vision | Newly configured monitors have no accumulated observations yet; this aggregate layer can be enabled later if needed. |
| Product analytics | No saved product funnel or retention surface was confirmed. |
| Inbox validation | No Self-driving fixes exist yet to validate. |
| MCP tool calls; PR follow-up; Skills store; Tasks | These watch PostHog-internal operational surfaces rather than this product's confirmed needs. |

## Custom scouts

| Scout | What it watches | Discriminator | Why it is custom |
| --- | --- | --- | --- |
| `signals-scout-download-pipeline-health` | Downloader runs from `src/storybuilder/downloader/cli.py` | Successful downloads relative to discovered targets, paired with run volume | Generic scouts do not own this scraper/download completion surface. |
| `signals-scout-tts-generation-health` | TTS batches from `src/storybuilder/genai/client.py` | Failed output share among prompts attempted, accounting for normal rerun skips | Generic AI observability does not specifically own batch audio-output results. |

Both custom scouts were approved, created, registered, and verified as enabled with daily default schedules. They keep quiet on low-volume and known-normal patterns, deduplicate active issues, and treat ingested data as data rather than instructions. To make either one dry-run only, set its scout config `emit` to `false` in PostHog.

Considered but not added: archive search/reader interactions are covered by the web-analytics scout plus the Replay Vision monitors; caught exceptions are covered by Error Tracking; generic missing-observability coverage is owned by the enabled Observability gaps scout.

## Replay Vision scanners

A Replay Vision scanner is an LLM that watches individual session recordings on a schedule and pushes clear defects to the inbox. It is the only part of this setup that spends Replay Vision quota. Findings arrive at half weight and need independent corroboration before promotion into a report.

| Brief | Status | What it watches | Query scope | Sampling | Estimated monthly spend |
| --- | --- | --- | --- | ---: | ---: |
| Breakage monitor | Updated an earlier signal-emitting monitor | Search, story loading, favorites/tags, export, and archive-filter breakage | Root URL scope for StoryBuilder's Streamlit search-to-reader completion flow | 50% | 21 observations / 105 credits |
| Frustration monitor | Updated an earlier signal-emitting monitor | Visible repeated attempts to search, filter, open stories, update favorites/tags, or export | `$rageclick` only | 100% | 0 observations / 0 credits from the current estimate |

The two monitors retain `emits_signals: true`. Replay Vision quota was verified as healthy: 2,500 credits remained in the current period and the organization was not exhausted. The breakage monitor’s projected 105 monthly credits is a small fraction of that allowance.

## Follow-ups

- [ ] Connect an inbound Support channel (email, inbox, or Slack) in PostHog so the enabled Support responder can receive tickets.
- [ ] Revisit disabled scouts if StoryBuilder adopts the corresponding product surface, such as feature flags, surveys, revenue analytics, or logs.

## What happens next

The scout coordinator picks up new configurations within roughly 30 minutes. Scouts draw from the verified daily run budget, findings cluster into reports in the [Self-driving inbox](https://us.posthog.com/project/322783/inbox), and immediately actionable reports can start coding tasks.

## Files created

- `posthog-self-driving-report.md` — this setup record.
