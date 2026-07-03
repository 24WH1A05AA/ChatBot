"""
Evaluation Orchestrator

Main entry point for running comprehensive evaluations.
Coordinates test generation, execution, evaluation, and reporting.
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import json

from evaluation.test_case_generator import TestCaseGenerator, TestCase
from evaluation.evaluation_engine import EvaluationEngine
from evaluation.report_generator import ReportGenerator


class EvaluationOrchestrator:
    """Orchestrates complete evaluation workflow."""

    def __init__(self, output_dir: str = "evaluation_results") -> None:
        """
        Initialize orchestrator.
        
        Args:
            output_dir: Directory for storing reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.test_generator = TestCaseGenerator()
        self.evaluation_engine = EvaluationEngine()
        self.report_generator = None

        self.test_cases: List[TestCase] = []
        self.execution_log: List[Dict[str, Any]] = []

    def generate_test_cases(self) -> List[TestCase]:
        """Generate all test cases."""
        print("[EVAL] Generating test cases...")

        self.test_cases = self.test_generator.generate_all_tests()
        summary = self.test_generator.summary()

        print(f"[EVAL] Generated {summary['total']} test cases:")
        for category, count in summary["by_category"].items():
            print(f"  - {category}: {count}")

        return self.test_cases

    def run_tests(
        self,
        chatbot_function: Callable[[str], tuple],
    ) -> None:
        """
        Run all test cases against chatbot.
        
        Args:
            chatbot_function: Function that takes query and returns (response, latency_ms)
        """
        print(f"\n[EVAL] Running {len(self.test_cases)} tests...")

        for i, test_case in enumerate(self.test_cases):
            try:
                # Get response from chatbot
                response, latency_ms = chatbot_function(test_case.query)

                # Evaluate result
                result = self.evaluation_engine.evaluate_test(
                    test_case=test_case,
                    response=response,
                    latency_ms=latency_ms,
                )

                # Log execution
                self.execution_log.append({
                    "test_id": test_case.id,
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # Print progress
                if (i + 1) % 5 == 0 or (i + 1) == len(self.test_cases):
                    print(f"  Progress: {i + 1}/{len(self.test_cases)}")

            except Exception as e:
                print(f"  ERROR in test {test_case.id}: {str(e)}")
                self.execution_log.append({
                    "test_id": test_case.id,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                })

        print(f"[EVAL] Test execution complete. {len(self.evaluation_engine.results)} results collected.")

    def generate_reports(self, formats: List[str] = None) -> Dict[str, str]:
        """
        Generate evaluation reports.
        
        Args:
            formats: List of formats to generate (json, csv, html, text)
                    Default: ['json', 'csv', 'html', 'text']
        
        Returns:
            Dictionary mapping format to file path
        """
        if formats is None:
            formats = ['json', 'csv', 'html', 'text']

        print(f"\n[EVAL] Generating reports in formats: {', '.join(formats)}")

        self.report_generator = ReportGenerator(self.evaluation_engine)
        report_files = {}

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if 'json' in formats:
            filepath = self.output_dir / f"evaluation_report_{timestamp}.json"
            self.report_generator.generate_json_report(str(filepath))
            report_files['json'] = str(filepath)
            print(f"  [+] JSON report: {filepath}")

        if 'csv' in formats:
            filepath = self.output_dir / f"evaluation_results_{timestamp}.csv"
            self.report_generator.generate_csv_report(str(filepath))
            report_files['csv'] = str(filepath)
            print(f"  [+] CSV report: {filepath}")

        if 'html' in formats:
            filepath = self.output_dir / f"evaluation_report_{timestamp}.html"
            self.report_generator.generate_html_report(str(filepath))
            report_files['html'] = str(filepath)
            print(f"  [+] HTML report: {filepath}")

        if 'text' in formats:
            filepath = self.output_dir / f"evaluation_report_{timestamp}.txt"
            self.report_generator.generate_text_report(str(filepath))
            report_files['text'] = str(filepath)
            print(f"  [+] Text report: {filepath}")

        # Also generate category summary CSV
        cat_csv_path = self.output_dir / f"evaluation_categories_{timestamp}.csv"
        self.report_generator.generate_category_csv_report(str(cat_csv_path))
        report_files['category_csv'] = str(cat_csv_path)
        print(f"  [+] Category summary: {cat_csv_path}")

        return report_files

    def get_summary(self) -> Dict[str, Any]:
        """Get evaluation summary."""
        return self.evaluation_engine.get_summary()

    def print_summary(self) -> None:
        """Print evaluation summary to console."""
        summary = self.evaluation_engine.get_summary()
        overall = summary['overall']
        category_scores = summary['by_category']

        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)

        print(f"\nOverall Results:")
        print(f"  Score:          {overall['overall_score']:.2f} ({overall['score_level'].upper()})")
        print(f"  Pass Rate:      {overall['pass_rate'] * 100:.1f}%")
        print(f"  Tests Passed:   {overall['tests_passed']}/{overall['tests_run']}")

        print(f"\nResults by Category:")
        print(f"{'Category':<20} {'Tests':<8} {'Passed':<8} {'Pass %':<10} {'Score':<8} {'Level':<12}")
        print("-" * 80)

        for cat in category_scores:
            level = self.evaluation_engine.get_score_level_string(cat['average_score'])
            print(
                f"{cat['category']:<20} {cat['total_tests']:<8} {cat['passed_tests']:<8} "
                f"{cat['pass_rate'] * 100:<9.1f}% {cat['average_score']:<8.2f} {level:<12}"
            )

        print("\n" + "=" * 80)

    def export_execution_log(self) -> None:
        """Export execution log."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"execution_log_{timestamp}.json"

        with open(filepath, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "total_executions": len(self.execution_log),
                "successful": sum(1 for e in self.execution_log if e['status'] == 'completed'),
                "errors": sum(1 for e in self.execution_log if e['status'] == 'error'),
                "log": self.execution_log,
            }, f, indent=2)

        print(f"\n[EVAL] Execution log exported: {filepath}")

    def run_full_evaluation(
        self,
        chatbot_function: Callable[[str], tuple],
        report_formats: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Run complete evaluation pipeline.
        
        Args:
            chatbot_function: Function to test
            report_formats: Report formats to generate
            
        Returns:
            Dictionary with results
        """
        print("\n" + "=" * 80)
        print("STARTING COMPREHENSIVE EVALUATION")
        print("=" * 80)

        # Generate tests
        self.generate_test_cases()

        # Run tests
        self.run_tests(chatbot_function)

        # Export execution log
        self.export_execution_log()

        # Generate reports
        report_files = self.generate_reports(report_formats)

        # Print summary
        self.print_summary()

        # Return results
        return {
            "summary": self.get_summary(),
            "report_files": report_files,
            "test_cases_count": len(self.test_cases),
            "results_count": len(self.evaluation_engine.results),
        }


def create_mock_chatbot_function() -> Callable[[str], tuple]:
    """Create a mock chatbot function for testing."""
    def mock_chatbot(query: str) -> tuple:
        """Mock chatbot that returns simple responses."""
        import time
        import random

        # Simulate latency
        latency = random.uniform(0.5, 2.5)
        time.sleep(latency / 1000)  # Convert ms to seconds

        # Simple response generation
        query_lower = query.lower()

        # Check for attacks
        attack_patterns = [
            "ignore", "drop table", "show", "reveal", "api", "key",
            "dan", "jailbreak", "exploit"
        ]

        if any(pattern in query_lower for pattern in attack_patterns):
            return (
                "I cannot process that request. Please ask about college information.",
                latency
            )

        # Generate simple response
        if "admission" in query_lower:
            response = "The college admission deadline is typically March 31st. Please visit the admissions page for more details."
        elif "fee" in query_lower:
            response = "Tuition fees vary by program. Engineering is $10,000 per year, while arts is $5,000 per year."
        elif "scholarship" in query_lower:
            response = "We offer merit-based scholarships covering 25-100% of tuition. Apply through our financial aid office."
        elif "facility" in query_lower or "facility" in query_lower:
            response = "We have modern laboratories, a well-stocked library, sports facilities, and student hostels."
        elif "department" in query_lower:
            response = "We have departments of Engineering, Arts, Science, and Management."
        else:
            response = "Thank you for your question. Please provide more specific details about what you'd like to know."

        return (response, latency)

    return mock_chatbot
