import asyncio
import json
import time
from pathlib import Path

from app.graph.claim_graph import claim_graph
from app.models.claim import ClaimRequest

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_CASES_PATH = BASE_DIR / "evaluation" / "test_cases.json"

async def run():
    with open(TEST_CASES_PATH) as file:
        test_cases = json.load(file)

    decision_checks = 0
    decision_passed = 0

    policy_checks = 0
    policy_passed = 0

    manual_review_checks = 0
    manual_review_passed = 0

    total_latency = 0
    total_input_tokens = 0
    total_output_tokens = 0
    llm_calls = 0

    for case in test_cases:
        claim = ClaimRequest(**case["input"])

        start_time = time.perf_counter()

        result = await claim_graph.ainvoke(
            claim.model_dump()
        )

        latency = time.perf_counter() - start_time

        print(f"Latency: {latency:.2f}s")

        total_latency += latency
        
        input_tokens = result.get("input_tokens", 0) or 0
        output_tokens = result.get("output_tokens", 0) or 0

        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        
        if input_tokens or output_tokens:
            llm_calls += 1
            print(
                f"Tokens: "
                f"{input_tokens} input / "
                f"{output_tokens} output"
            )

        expected = case["expected"]

        print(f"\n--- {case['id']} ---")

        # Decision accuracy
        if "decision" in expected:
            decision_checks += 1

            actual_decision = result.get("decision")

            if hasattr(actual_decision, "value"):
                actual_decision = actual_decision.value

            expected_decision = expected["decision"]

            passed = actual_decision == expected_decision

            if passed:
                decision_passed += 1

            print(
                f"Decision: {actual_decision} "
                f"(expected {expected_decision}) "
                f"{'PASS' if passed else 'FAIL'}"
            )

            # Manual review routing accuracy
            if expected_decision == "MANUAL_REVIEW":
                manual_review_checks += 1

                if actual_decision == "MANUAL_REVIEW":
                    manual_review_passed += 1

        # Policy retrieval accuracy
        if "policy_source" in expected:
            policy_checks += 1

            actual_policy = result.get("policy_source")
            expected_policy = expected["policy_source"]

            passed = actual_policy == expected_policy

            if passed:
                policy_passed += 1

            print(
                f"Policy: {actual_policy} "
                f"(expected {expected_policy}) "
                f"{'PASS' if passed else 'FAIL'}"
            )

    decision_accuracy = (
        decision_passed / decision_checks
        if decision_checks else 0
    )

    policy_accuracy = (
        policy_passed / policy_checks
        if policy_checks else 0
    )

    manual_review_accuracy = (
        manual_review_passed / manual_review_checks
        if manual_review_checks else 0
    )

    average_latency = (
        total_latency / len(test_cases)
        if test_cases else 0
    )

    print("\n==============================")
    print("Evaluation Results")
    print("==============================")

    print(
        f"Decision Accuracy: "
        f"{decision_passed}/{decision_checks} "
        f"({decision_accuracy:.2%})"
    )

    print(
        f"Policy Retrieval Accuracy: "
        f"{policy_passed}/{policy_checks} "
        f"({policy_accuracy:.2%})"
    )

    print(
        f"Manual Review Routing Accuracy: "
        f"{manual_review_passed}/{manual_review_checks} "
        f"({manual_review_accuracy:.2%})"
    )

    print(f"\nAverage End-to-End Latency: {average_latency:.2f}s")
    print(f"Total Input Tokens: {total_input_tokens}")
    print(f"Total Output Tokens: {total_output_tokens}")
    print(f"LLM Calls: {llm_calls}")

if __name__ == "__main__":
    asyncio.run(run())