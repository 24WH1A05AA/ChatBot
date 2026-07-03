#!/usr/bin/env python3
"""
Comprehensive Chatbot Evaluation Script

Run this script to perform full evaluation of the chatbot including:
- Automatic test case generation
- Functional testing
- Quality assessment
- Safety verification
- Security testing
- Robustness evaluation
- Performance monitoring
- Context awareness testing
- RAGAS metrics computation
- Report generation (JSON, CSV, HTML, TXT)
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from evaluation.evaluation_orchestrator import EvaluationOrchestrator, create_mock_chatbot_function


def main():
    """Run comprehensive evaluation."""
    print("\n")
    print("=" * 80)
    print("COMPREHENSIVE CHATBOT EVALUATION SYSTEM")
    print("=" * 80)
    print("\nInitializing evaluation system...")

    # Create orchestrator
    orchestrator = EvaluationOrchestrator(output_dir="evaluation_results")

    # Get chatbot function (use mock for demo)
    chatbot_function = create_mock_chatbot_function()

    # Run full evaluation
    results = orchestrator.run_full_evaluation(
        chatbot_function=chatbot_function,
        report_formats=['json', 'csv', 'html', 'text'],
    )

    # Print results summary
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)

    print("\nGenerated Reports:")
    for fmt, filepath in results['report_files'].items():
        print(f"  - {fmt.upper()}: {filepath}")

    print(f"\nStatistics:")
    print(f"  - Test Cases Generated: {results['test_cases_count']}")
    print(f"  - Test Results Collected: {results['results_count']}")

    summary = results['summary']
    print(f"\nOverall Score: {summary['overall']['overall_score']:.2f}")
    print(f"Pass Rate: {summary['overall']['pass_rate'] * 100:.1f}%")

    print("\n" + "=" * 80)
    print("\nTo view the full report, open the HTML file in your browser:")
    print(f"  {results['report_files'].get('html', 'evaluation_report.html')}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
