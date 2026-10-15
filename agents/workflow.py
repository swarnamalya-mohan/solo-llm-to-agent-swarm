"""Async vLLM-backed solo and multi-agent incident investigation.

Use an OpenAI-compatible vLLM endpoint. No API key is sent to a public provider.
A verifier is a fallible LLM; deterministic checks complement its judgment.
"""
from __future__ import annotations
import asyncio
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any
from openai import AsyncOpenAI

MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
BASE_URL = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000/v1")
PROMPTS = {
    "tracking": "You are a tracking analyst. Look ONLY for chronological inconsistencies and missing events. Cite exact event times. Distinguish evidence and speculation.",
    "weather": "You are a weather analyst. Assess whether weather CAUSED the delay based only on supplied evidence. Do not confuse an advisory issued after an event with an earlier cause.",
    "routing": "You are a routing analyst. Analyze exceptions and plausible hypotheses, but do not assert an unproven root cause. List missing evidence.",
}
SYNTHESIS = "Combine specialist reports. Return FACTS, HYPOTHESES, UNSUPPORTED CLAIMS, NEXT ACTIONS. Preserve uncertainty; do not invent records."
VALIDATOR = "Independently audit the proposed report against ORIGINAL incident evidence. Return PASS or FAIL, then any unsupported claims, conflicting timestamps and missing evidence. Do not rubber-stamp."
SOLO = "Investigate this shipment, identify data quality issues and possible causes, then recommend operational next actions. Clearly separate verified facts from hypotheses."

@dataclass
class Outcome:
    text: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int

class IncidentWorkshop:
    def __init__(self, base_url: str = BASE_URL, model: str = MODEL, max_concurrency: int = 8):
        self.client = AsyncOpenAI(base_url=base_url, api_key=os.getenv("VLLM_API_KEY", "EMPTY"), timeout=120, max_retries=1)
        self.model = model
        self.limit = asyncio.Semaphore(max_concurrency)

    async def call(self, system: str, user: str, max_tokens: int = 350) -> Outcome:
        start = time.perf_counter()
        async with self.limit:
            response = await self.client.chat.completions.create(
                model=self.model, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0, max_tokens=max_tokens,
            )
        usage = response.usage
        return Outcome(response.choices[0].message.content or "", time.perf_counter() - start,
                       usage.prompt_tokens if usage else 0, usage.completion_tokens if usage else 0)

    async def solo(self, incident: dict[str, Any]) -> Outcome:
        return await self.call(SOLO, json.dumps(incident, indent=2))

    async def specialists(self, incident: dict[str, Any], parallel: bool = True) -> dict[str, Outcome]:
        payload = json.dumps(incident, indent=2)
        if parallel:
            results = await asyncio.gather(*(self.call(prompt, payload) for prompt in PROMPTS.values()))
        else:
            results = []
            for prompt in PROMPTS.values():
                results.append(await self.call(prompt, payload))
        return dict(zip(PROMPTS, results))

    async def swarm(self, incident: dict[str, Any], verify: bool = True, parallel: bool = True) -> dict[str, Any]:
        start = time.perf_counter()
        specialists = await self.specialists(incident, parallel=parallel)
        reports = "\n\n".join(f"{name}: {out.text}" for name, out in specialists.items())
        synthesis = await self.call(SYNTHESIS, "SOURCE:\n" + json.dumps(incident) + "\nREPORTS:\n" + reports)
        validation = None
        if verify:
            validation = await self.call(VALIDATOR, "ORIGINAL:\n" + json.dumps(incident) + "\nDRAFT:\n" + synthesis.text)
        all_calls = list(specialists.values()) + [synthesis] + ([validation] if validation else [])
        return {
            "specialists": specialists, "synthesis": synthesis, "validation": validation,
            "deterministic_checks": check_timeline(incident),
            "wall_seconds": time.perf_counter() - start,
            "requests": len(all_calls), "input_tokens": sum(x.input_tokens for x in all_calls),
            "output_tokens": sum(x.output_tokens for x in all_calls),
        }

    async def close(self) -> None:
        await self.client.close()

def check_timeline(incident: dict[str, Any]) -> dict[str, Any]:
    """Simple same-day chronology checker; not suitable for overnight/multi-zone production logs."""
    events = incident.get("events", [])
    times = [e.get("time", "") for e in events]
    valid = all(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t) for t in times)
    if not valid:
        return {"status": "unknown", "reason": "Invalid or missing HH:MM timestamps"}
    minutes = [int(t[:2])*60 + int(t[3:]) for t in times]
    inversions = [{"previous": events[i-1], "next": events[i]} for i in range(1, len(events)) if minutes[i] < minutes[i-1]]
    return {"status": "contradiction" if inversions else "consistent", "inversions": inversions,
            "limitation": "Assumes same-day timestamps in one timezone"}

async def benchmark(workshop: IncidentWorkshop, incident: dict[str, Any], requests: int = 20, concurrency: int = 4) -> dict[str, float]:
    gate = asyncio.Semaphore(concurrency)
    async def one(i: int) -> Outcome:
        async with gate:
            return await workshop.call("Summarize the evidence in exactly two sentences.", json.dumps(incident) + f"\nCase replicate {i}", max_tokens=100)
    start = time.perf_counter()
    outcomes = await asyncio.gather(*(one(i) for i in range(requests)))
    elapsed = time.perf_counter() - start
    return {"concurrency": concurrency, "requests": requests, "elapsed_s": round(elapsed, 3),
            "requests_per_second": round(requests / elapsed, 3),
            "output_tokens_per_second": round(sum(x.output_tokens for x in outcomes) / elapsed, 2),
            "mean_request_latency_s": round(sum(x.latency_seconds for x in outcomes) / requests, 3)}
