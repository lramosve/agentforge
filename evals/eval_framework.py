"""Evaluation framework for systematic agent testing."""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestCase:
    """A single test case for agent evaluation."""

    id: str
    category: str  # happy_path, edge_case, adversarial, multi_step
    input_query: str
    expected_tools: list[str]
    expected_outcome: str
    pass_criteria: dict = field(default_factory=dict)


@dataclass
class EvalResult:
    """Result of running a single test case."""

    test_id: str
    category: str
    passed: bool
    tools_correct: bool
    outcome_match: bool
    response: str
    confidence: float
    duration: float
    cost: float
    details: dict = field(default_factory=dict)


class EvalFramework:
    """Systematic evaluation for AgentForge."""

    def __init__(self):
        self.test_cases: list[TestCase] = []
        self.results: list[EvalResult] = []

    def load_dataset(self, path: str) -> None:
        """Load test cases from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        for tc in data.get("test_cases", []):
            self.test_cases.append(TestCase(
                id=tc["id"],
                category=tc["category"],
                input_query=tc["input_query"],
                expected_tools=tc.get("expected_tools", []),
                expected_outcome=tc.get("expected_outcome", ""),
                pass_criteria=tc.get("pass_criteria", {}),
            ))

    def add_test_case(self, test_case: TestCase) -> None:
        """Add a single test case."""
        self.test_cases.append(test_case)

    async def run_evaluation(self, agent_fn, verbose: bool = False) -> dict:
        """Run all test cases against the agent.

        Args:
            agent_fn: Async callable(message: str) -> dict with keys:
                      response, tools_used, confidence, metrics.
            verbose: Print per-test results.
        """
        print(f"\n{'='*70}")
        print(f"RUNNING EVALUATION — {len(self.test_cases)} test cases")
        print(f"{'='*70}\n")

        self.results = []

        for i, tc in enumerate(self.test_cases):
            start = time.time()

            try:
                result = await agent_fn(tc.input_query)
                duration = time.time() - start

                tools_used = set(result.get("tools_used", []))
                expected_tools = set(tc.expected_tools)
                tools_correct = expected_tools.issubset(tools_used)

                response_text = result.get("response", "")
                outcome_keywords = tc.expected_outcome.lower().split()
                outcome_match = any(
                    kw in response_text.lower() for kw in outcome_keywords
                ) if outcome_keywords else True

                passed = tools_correct and outcome_match

                # Apply custom pass criteria
                criteria = tc.pass_criteria
                if criteria.get("must_contain_disclaimer"):
                    if "disclaimer" not in response_text.lower() and "not financial advice" not in response_text.lower():
                        passed = False

                if criteria.get("must_refuse"):
                    refusal_words = [
                        "cannot", "can't", "can\u2019t",
                        "won't", "won\u2019t",
                        "don't", "don\u2019t",
                        "unable", "not able", "outside",
                        "i'm not able", "not able to",
                    ]
                    refused = any(w in response_text.lower() for w in refusal_words)
                    if refused:
                        # Agent correctly refused — override outcome_match
                        passed = True
                    else:
                        passed = False

                if criteria.get("max_latency") and duration > criteria["max_latency"]:
                    passed = False

                eval_result = EvalResult(
                    test_id=tc.id,
                    category=tc.category,
                    passed=passed,
                    tools_correct=tools_correct,
                    outcome_match=outcome_match,
                    response=response_text[:500],
                    confidence=result.get("confidence", 0.0),
                    duration=round(duration, 2),
                    cost=result.get("metrics", {}).get("total_cost_usd", 0.0),
                )

            except Exception as e:
                eval_result = EvalResult(
                    test_id=tc.id,
                    category=tc.category,
                    passed=False,
                    tools_correct=False,
                    outcome_match=False,
                    response=f"ERROR: {str(e)}",
                    confidence=0.0,
                    duration=round(time.time() - start, 2),
                    cost=0.0,
                    details={"error": str(e)},
                )

            self.results.append(eval_result)

            status = "PASS" if eval_result.passed else "FAIL"
            if verbose:
                print(f"  [{status}] {tc.id} ({eval_result.duration}s)")
            else:
                print(f"  {'[PASS]' if eval_result.passed else '[FAIL]'} {tc.id}")

        return self._generate_report()

    def _generate_report(self) -> dict:
        """Generate evaluation summary report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        pass_rate = passed / total if total > 0 else 0

        by_category = {}
        for r in self.results:
            cat = r.category
            if cat not in by_category:
                by_category[cat] = {"total": 0, "passed": 0}
            by_category[cat]["total"] += 1
            if r.passed:
                by_category[cat]["passed"] += 1

        for cat in by_category:
            by_category[cat]["rate"] = (
                by_category[cat]["passed"] / by_category[cat]["total"]
            )

        avg_duration = (
            sum(r.duration for r in self.results) / total if total else 0
        )
        avg_confidence = (
            sum(r.confidence for r in self.results) / total if total else 0
        )
        total_cost = sum(r.cost for r in self.results)

        report = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(pass_rate, 3),
            "by_category": by_category,
            "avg_duration_seconds": round(avg_duration, 2),
            "avg_confidence": round(avg_confidence, 3),
            "total_cost_usd": round(total_cost, 4),
        }

        print(f"\n{'='*70}")
        print("EVALUATION RESULTS")
        print(f"{'='*70}")
        print(f"  Pass Rate: {pass_rate:.1%} ({passed}/{total})")
        print(f"  Avg Duration: {avg_duration:.2f}s")
        print(f"  Avg Confidence: {avg_confidence:.3f}")
        print(f"  Total Cost: ${total_cost:.4f}")
        print(f"\n  By Category:")
        for cat, stats in by_category.items():
            print(f"    {cat}: {stats['rate']:.1%} ({stats['passed']}/{stats['total']})")
        print(f"{'='*70}\n")

        return report

    def save_results(self, path: str) -> None:
        """Save evaluation results to JSON."""
        output = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "results": [
                {
                    "test_id": r.test_id,
                    "category": r.category,
                    "passed": r.passed,
                    "tools_correct": r.tools_correct,
                    "outcome_match": r.outcome_match,
                    "confidence": r.confidence,
                    "duration": r.duration,
                    "cost": r.cost,
                    "response_preview": r.response[:200],
                }
                for r in self.results
            ],
            "report": self._generate_report() if self.results else {},
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Results saved to {path}")
