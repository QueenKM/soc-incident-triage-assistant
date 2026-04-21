# Architecture Notes

## Goal

Create a recruiter-friendly incident triage demo that feels like a real analyst acceleration tool instead of a toy chatbot.

## MVP Shape

The starter is intentionally split into three layers:

1. `sample alert input`
2. `deterministic triage engine`
3. `browser presentation`

This keeps the first version:

- easy to run locally
- easy to test
- easy to later replace with a cloud-backed enrichment or LLM layer

## Current Flow

1. User selects a sample alert from the web UI.
2. The local server loads the alert payload from `data/sample_alerts.json`.
3. `triage_engine.py` scores the alert and maps it into:
   - executive summary
   - attack story
   - recommended analyst actions
   - containment steps
   - suggested KQL
4. The browser renders a readable incident brief.
5. Analysts can update case status, owner, and decision notes in a persisted local history.

## Planned Expansion

### Security data adapters

- Sentinel incident export
- Defender XDR alert export
- Entra ID risky sign-in data

### AI layer

- grounded prompt using alert evidence and entity context
- structured JSON response contract
- analyst feedback labels for good / weak triage

### Product polish

- incident queue and saved triage history
- entity relationship graph
- watchlist enrichment
- markdown / PDF export for incident handoff
