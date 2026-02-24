"""Response verification: fact-checking, hallucination detection, confidence scoring, domain constraints."""

import re

from agent.models import VerificationResult


FINANCIAL_DISCLAIMER_KEYWORDS = [
    "not financial advice",
    "consult",
    "professional",
    "informational purposes",
    "disclaimer",
]

TAX_DISCLAIMER_KEYWORDS = [
    "tax professional",
    "consult",
    "jurisdiction",
    "disclaimer",
    "estimate",
]


class ResponseVerifier:
    """Verifies agent responses before returning to the user."""

    def verify(
        self,
        response_text: str,
        tool_results: list[dict],
        query_type: str = "general",
    ) -> VerificationResult:
        """Run all verification checks on a response.

        Args:
            response_text: The agent's generated response.
            tool_results: List of tool result dicts from the agent's execution.
            query_type: Type of query - 'general', 'tax', 'advice', 'compliance'.

        Returns:
            VerificationResult with pass/fail, confidence, warnings, and errors.
        """
        warnings = []
        errors = []
        sources = []
        checks_passed = 0
        checks_total = 0

        # Check 1: Fact-checking (numbers in response match tool data)
        checks_total += 1
        fact_result = self._check_facts(response_text, tool_results)
        if fact_result["passed"]:
            checks_passed += 1
        else:
            warnings.extend(fact_result.get("warnings", []))
            errors.extend(fact_result.get("errors", []))
        sources.extend(fact_result.get("sources", []))

        # Check 2: Hallucination detection
        checks_total += 1
        hallucination_result = self._check_hallucination(response_text, tool_results)
        if hallucination_result["passed"]:
            checks_passed += 1
        else:
            warnings.extend(hallucination_result.get("warnings", []))

        # Check 3: Domain constraint checks
        checks_total += 1
        constraint_result = self._check_domain_constraints(response_text, query_type)
        if constraint_result["passed"]:
            checks_passed += 1
        else:
            warnings.extend(constraint_result.get("warnings", []))
            errors.extend(constraint_result.get("errors", []))

        # Check 4: Output completeness
        checks_total += 1
        completeness_result = self._check_completeness(response_text, tool_results)
        if completeness_result["passed"]:
            checks_passed += 1
        else:
            warnings.extend(completeness_result.get("warnings", []))

        # Calculate confidence
        confidence = checks_passed / checks_total if checks_total > 0 else 0.0

        # Boost confidence if all tools succeeded
        tool_success_rate = self._tool_success_rate(tool_results)
        confidence = (confidence * 0.7) + (tool_success_rate * 0.3)

        return VerificationResult(
            passed=len(errors) == 0 and confidence >= 0.5,
            confidence=round(confidence, 3),
            warnings=warnings,
            errors=errors,
            sources=sources,
        )

    def _check_facts(self, response: str, tool_results: list[dict]) -> dict:
        """Verify numbers in the response appear in tool result data."""
        # Extract numbers from response (dollar amounts, percentages)
        response_numbers = set()
        for match in re.finditer(r'[\$]?([\d,]+\.?\d*)\s*%?', response):
            try:
                num_str = match.group(1).replace(",", "")
                num = float(num_str)
                if num > 0.01:  # Ignore trivially small numbers
                    response_numbers.add(round(num, 2))
            except ValueError:
                continue

        if not response_numbers:
            return {"passed": True, "sources": ["No numerical claims to verify"]}

        # Extract numbers from tool results
        tool_numbers = set()
        sources = []
        for result in tool_results:
            if result.get("status") == "success" and result.get("data"):
                self._extract_numbers(result["data"], tool_numbers)
                sources.append(f"Tool data: {result.get('message', 'unknown')}")

        # Check how many response numbers are in tool data
        unverified = response_numbers - tool_numbers
        verified_ratio = 1 - (len(unverified) / len(response_numbers)) if response_numbers else 1

        warnings = []
        if unverified and len(unverified) <= 3:
            warnings.append(
                f"Some numbers could not be traced to tool data: {unverified}"
            )

        return {
            "passed": verified_ratio >= 0.5,
            "warnings": warnings,
            "errors": [],
            "sources": sources,
        }

    def _extract_numbers(self, data, numbers_set: set, depth: int = 0):
        """Recursively extract numbers from nested data structures."""
        if depth > 5:
            return
        if isinstance(data, (int, float)):
            numbers_set.add(round(float(data), 2))
            numbers_set.add(round(abs(float(data)), 2))
        elif isinstance(data, dict):
            for v in data.values():
                self._extract_numbers(v, numbers_set, depth + 1)
        elif isinstance(data, list):
            for item in data:
                self._extract_numbers(item, numbers_set, depth + 1)

    def _check_hallucination(self, response: str, tool_results: list[dict]) -> dict:
        """Flag potential hallucinated content."""
        warnings = []

        # Check for specific stock recommendations (agent should not make these)
        buy_sell_patterns = [
            r'\b(you should|I recommend|must) (buy|sell|short)\b',
            r'\bguaranteed\b',
            r'\brisk[- ]?free\b',
            r'\bwill (definitely|certainly|surely) (go up|increase|rise)\b',
        ]
        for pattern in buy_sell_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                warnings.append(
                    f"Potential hallucination: response contains directive financial advice matching '{pattern}'"
                )

        # If no tools were called but response has specific numbers, that's suspicious
        if not tool_results and re.search(r'\$[\d,]+\.?\d*', response):
            warnings.append(
                "Response contains dollar amounts but no tools were called to source data"
            )

        return {"passed": len(warnings) == 0, "warnings": warnings}

    def _check_domain_constraints(self, response: str, query_type: str) -> dict:
        """Enforce domain-specific rules."""
        warnings = []
        errors = []

        # Tax queries must have disclaimer
        if query_type == "tax":
            has_disclaimer = any(
                kw in response.lower() for kw in TAX_DISCLAIMER_KEYWORDS
            )
            if not has_disclaimer:
                errors.append(
                    "Tax-related response missing required disclaimer"
                )

        # Advice queries should have general disclaimer
        if query_type == "advice":
            has_disclaimer = any(
                kw in response.lower() for kw in FINANCIAL_DISCLAIMER_KEYWORDS
            )
            if not has_disclaimer:
                warnings.append(
                    "Financial advice response should include disclaimer"
                )

        return {"passed": len(errors) == 0, "warnings": warnings, "errors": errors}

    def _check_completeness(self, response: str, tool_results: list[dict]) -> dict:
        """Check if the response actually addresses the tool results."""
        warnings = []

        if not response or len(response.strip()) < 20:
            warnings.append("Response is too short — may be incomplete")

        # If tools returned errors, response should acknowledge
        errored_tools = [r for r in tool_results if r.get("status") == "error"]
        if errored_tools and "unable" not in response.lower() and "error" not in response.lower():
            warnings.append(
                "Tools returned errors but response doesn't acknowledge data limitations"
            )

        return {"passed": len(warnings) == 0, "warnings": warnings}

    def _tool_success_rate(self, tool_results: list[dict]) -> float:
        """Calculate the fraction of tools that succeeded."""
        if not tool_results:
            return 0.5  # No tools called is neutral
        successes = sum(1 for r in tool_results if r.get("status") == "success")
        return successes / len(tool_results)
