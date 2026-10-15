# From Solo LLM to Agent Swarm

A hands-on 60-minute workshop showing how a solo LLM becomes a specialist agent team with concurrency, verification, and vLLM serving.

## Quickstart

**Prerequisites:** Python 3.10+, a compatible GPU host running vLLM (or a secured remote vLLM endpoint). A model server is required for live inference; CPU environments can run the unit tests.

Install client dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install [vLLM](https://docs.vllm.ai/) on a supported GPU machine separately, then start:

```bash
vllm serve Qwen/Qwen2.5-1.5B-Instruct --host 127.0.0.1 --port 8000
```

Use a secure network tunnel for remote connections. Never expose an unauthenticated vLLM endpoint to the internet.

Set `VLLM_BASE_URL` and `VLLM_MODEL` if using a different endpoint/model.

From the repository root:

```bash
python -m agents.cli --mode solo
python -m agents.cli --mode swarm
python -m agents.cli --mode benchmark --concurrency 4
pytest -q
jupyter notebook notebooks/01_live_workshop.ipynb
```

## Workshop materials

- [Master notebook](notebooks/01_live_workshop.ipynb): solo baseline, three specialized agents, sequential vs concurrent calls, synthesis, validation, and vLLM benchmark
- [Agent implementation](agents/workflow.py): reusable asynchronous Python library
- [CLI](agents/cli.py): easy-to-run modes
- [Dataset](data/incidents.json): fictional incidents and answer-key facts
- [Facilitator agenda](workshop/AGENDA.md): detailed 60-minute pacing and discussion prompts
- [Tests](tests/test_timeline.py): deterministic sample timestamp checking

The tracking, routing, and weather agents all use the **same served model** with different role instructions; the notebook illustrates agent-level concurrency and shared inference serving. An LLM validator is not an independent source of truth: the demo also includes a deterministic timeline check. Any production incident system needs timezone-aware records, grounded evidence and human review for consequential actions.

## Measuring results

For one incident, the solo baseline makes 1 model request. Three specialists plus synthesis require 4 requests; validation raises this to 5, excluding retries. More agents may increase cost and latency and do not guarantee better accuracy.

The notebook measures observed throughput and latency across concurrency settings 1, 2, 4 and 8. On a private vLLM server, inspect `/metrics` for running and queued requests and memory pressure. Benchmark repeated, warmed executions before drawing performance conclusions.

**Status:** The project includes unit-testable code and a complete notebook, but live GPU execution has not been verified in this environment.
