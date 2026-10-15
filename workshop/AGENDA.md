# Facilitator guide — 60 minutes

| Time | Section | Live action |
|---|---|---|
| 0–5 | One LLM versus a team | Frame the investigation; ask what evidence matters |
| 5–12 | Architecture | Distinguish prompts/roles, asynchronous tasks and independent model instances |
| 12–20 | Solo baseline | Run a solo request; inspect timeline and uncertainty |
| 20–30 | Agent swarm | Run specialists sequentially then concurrently; compare wall time |
| 30–40 | Validation | Inject a false weather-causality claim; run validator and deterministic timeline check |
| 40–50 | vLLM scaling | Run controlled concurrency benchmark 1, 2, 4, 8; inspect server metrics |
| 50–55 | Production trade-offs | Discuss shared-model correlated mistakes, queueing, retries, timezone handling and HITL |
| 55–60 | Q&A | Compare factual quality, latency, tokens and operational cost |

## Interactive questions
- What timestamp contradiction should the model find?
- Why does parallel execution not guarantee three times faster completion?
- Does agreement between two LLM calls constitute independent evidence?
- At what load does queueing overwhelm increased GPU utilization?

## Presentation safety / fallback
- Pre-download model weights and pre-launch the GPU server.
- Run all notebook cells once before presenting; do not invent example speedup figures.
- Prepare screenshots/logs as backup; note that no live production systems are touched.
- Sample incidents are fictional.
- A same-day timeline validator must not be used unmodified for cross-time-zone or overnight shipment events.
