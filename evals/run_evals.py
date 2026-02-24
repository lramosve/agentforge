"""CLI script to run the AgentForge evaluation suite."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "agent" / ".env")

from agent.graph import run_agent
from evals.eval_framework import EvalFramework


async def agent_fn(message: str) -> dict:
    """Wrapper to call the agent for evaluation."""
    return await run_agent(message=message)


async def main():
    parser = argparse.ArgumentParser(description="Run AgentForge evaluations")
    parser.add_argument(
        "--dataset",
        default="evals/datasets/full_suite.json",
        help="Path to test dataset JSON",
    )
    parser.add_argument(
        "--output",
        default="evals/results/latest.json",
        help="Path to save results",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    framework = EvalFramework()
    framework.load_dataset(args.dataset)

    report = await framework.run_evaluation(agent_fn, verbose=args.verbose)

    framework.save_results(args.output)

    # Exit with non-zero if pass rate below 80%
    if report["pass_rate"] < 0.80:
        print(f"\nFAILED: Pass rate {report['pass_rate']:.1%} is below 80% threshold")
        sys.exit(1)
    else:
        print(f"\nPASSED: Pass rate {report['pass_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
