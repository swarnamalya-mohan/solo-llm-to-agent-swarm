"""CLI for workshop, e.g. python -m agents.cli --mode swarm."""
import argparse
import asyncio
import json
from pathlib import Path
from .workflow import IncidentWorkshop, benchmark

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["solo", "swarm", "benchmark"], default="swarm")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    incident = json.loads(Path("data/incidents.json").read_text())[0]
    workshop = IncidentWorkshop()
    try:
        if args.mode == "solo":
            print((await workshop.solo(incident)).text)
        elif args.mode == "swarm":
            result = await workshop.swarm(incident)
            for name, output in result["specialists"].items():
                print(f"\n## {name}\n{output.text}")
            print("\n## SYNTHESIS\n", result["synthesis"].text)
            print("\n## VALIDATION\n", result["validation"].text)
            print("\n## MEASUREMENTS\n", json.dumps({k:v for k,v in result.items() if k in ("wall_seconds","requests","input_tokens","output_tokens","deterministic_checks")},indent=2))
        else:
            print(json.dumps(await benchmark(workshop, incident, concurrency=args.concurrency), indent=2))
    finally:
        await workshop.close()

if __name__ == "__main__":
    asyncio.run(main())
