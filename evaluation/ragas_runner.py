"""
Automated RAGAS Evaluation Runner

Automatically runs RAGAS evaluations on chatbot responses
and provides comprehensive analysis with recommendations.
"""

from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
from pathlib import Path
import json

from evaluation.ragas_metrics import RAGASMetrics, MetricLevel


class AutomaticRAGASRunner:
    """Automatically runs RAGAS evaluations."""

    def __init__(self, output_dir: str = "ragas_results") -> None:
        """Initialize runner."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics = RAGASMetrics()
        self.execution_log = []

    def run_evaluation(
        self,
        test_cases: List[Dict[str, Any]],
        chatbot_function: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Run RAGAS evaluation on test cases.
        
        Args:
            test_cases: List of {'query', 'context', 'response'} or just {'query', 'context'}
            chatbot_function: Optional function to generate responses
        
        Returns:
            Complete evaluation results
        """
        print("\n" + "=" * 80)
        print("STARTING AUTOMATIC RAGAS EVALUATION")
        print("=" * 80)

        processed_cases = []

        for i, case in enumerate(test_cases, 1):
            try:
                # Get response if not provided
                if 'response' not in case:
                    if chatbot_function:
                        response = chatbot_function(case['query'])
                    else:
                        response = "Response generation function not provided"
                else:
                    response = case['response']

                # Evaluate
                score = self.metrics.evaluate(
                    query=case['query'],
                    response=response,
                    context=case.get('context', []),
                )

                processed_cases.append(score)

                print(f"[{i}/{len(test_cases)}] Evaluated - Avg: {score.get_average():.2f}")

            except Exception as e:
                print(f"[{i}/{len(test_cases)}] Error: {str(e)}")
                self.execution_log.append({
                    "index": i,
                    "status": "error",
                    "error": str(e),
                })

        print(f"\n✅ Evaluation complete. {len(processed_cases)} cases evaluated.")

        # Display results
        self._display_results()

        # Generate outputs
        results = self._generate_outputs()

        print("\n" + "=" * 80)
        return results

    def _display_results(self) -> None:
        """Display results in console."""
        self.metrics.print_score_summary()

    def _generate_outputs(self) -> Dict[str, Any]:
        """Generate output files and return paths."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Generate detailed report
        report = self.metrics.generate_detailed_report()

        # Save JSON report
        json_path = self.output_dir / f"ragas_report_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Save detailed scores
        scores_path = self.output_dir / f"ragas_detailed_{timestamp}.json"
        with open(scores_path, 'w') as f:
            json.dump([s.to_dict() for s in self.metrics.scores], f, indent=2)

        # Generate text summary
        text_path = self.output_dir / f"ragas_summary_{timestamp}.txt"
        self._generate_text_summary(str(text_path), report)

        # Generate CSV for analysis
        csv_path = self.output_dir / f"ragas_scores_{timestamp}.csv"
        self._generate_csv_report(str(csv_path))

        return {
            "json_report": str(json_path),
            "detailed_scores": str(scores_path),
            "text_summary": str(text_path),
            "csv_scores": str(csv_path),
        }

    def _generate_text_summary(self, filepath: str, report: Dict[str, Any]) -> None:
        """Generate text summary."""
        lines = []
        lines.append("=" * 80)
        lines.append("RAGAS EVALUATION REPORT")
        lines.append("=" * 80)
        lines.append(f"\nGenerated: {report['timestamp']}")
        lines.append(f"Total Evaluations: {report['analysis']['total_evaluations']}")

        # Metrics table
        lines.append("\n" + "-" * 80)
        lines.append(f"{'Metric':<25} {'Score':<10} {'Level':<15} {'Target':<10} {'Status':<5}")
        lines.append("-" * 80)

        for metric, data in report['metrics'].items():
            if metric == 'overall':
                continue
            lines.append(
                f"{metric:<25} {data['score']:<10.2f} {data['level']:<15} "
                f"{data['target']:<10.2f} {data['status']:<5}"
            )

        lines.append(f"\n{'OVERALL':<25} {report['metrics']['overall']['score']:<10.2f}")

        # Analysis
        lines.append("\n" + "-" * 80)
        lines.append("ANALYSIS")
        lines.append("-" * 80)
        lines.append(f"Weakest Metric: {report['analysis']['weakest_metric']}")
        lines.append(f"Weakest Score: {report['analysis']['weakest_score']:.2f}")

        # Recommendations
        if report['recommendations']:
            lines.append("\n" + "-" * 80)
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 80)

            for metric, recs in report['recommendations'].items():
                lines.append(f"\n{metric.replace('_', ' ').upper()}:")
                for rec in recs:
                    lines.append(f"  • {rec}")

        lines.append("\n" + "=" * 80)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _generate_csv_report(self, filepath: str) -> None:
        """Generate CSV report with individual scores."""
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Query",
                "Response",
                "Context Count",
                "Faithfulness",
                "Answer Relevancy",
                "Context Recall",
                "Context Precision",
                "Average",
            ])

            # Data rows
            for score in self.metrics.scores:
                writer.writerow([
                    score.query[:50],
                    score.response[:50],
                    len(score.context),
                    f"{score.faithfulness:.2f}",
                    f"{score.answer_relevancy:.2f}",
                    f"{score.context_recall:.2f}",
                    f"{score.context_precision:.2f}",
                    f"{score.get_average():.2f}",
                ])

    def get_summary(self) -> Dict[str, Any]:
        """Get evaluation summary."""
        averages = self.metrics.get_average_scores()
        weakest_metric, weakest_score = self.metrics.get_weakest_metric()

        return {
            "status": "complete",
            "total_evaluations": len(self.metrics.scores),
            "metrics": averages,
            "weakest_metric": weakest_metric,
            "weakest_score": weakest_score,
            "recommendations": self.metrics.get_recommendations(),
        }


def create_ragas_test_cases() -> List[Dict[str, Any]]:
    """Create sample RAGAS test cases."""
    return [
        {
            "query": "What is the admission deadline?",
            "context": [
                "The college admission deadline is March 31st every year.",
                "Applications must be submitted before the deadline.",
                "Students who miss the deadline cannot apply for that year."
            ],
            "response": "The admission deadline is March 31st. Make sure to submit your application before this date.",
        },
        {
            "query": "Tell me about the campus facilities",
            "context": [
                "Our campus has state-of-the-art laboratories.",
                "We have a comprehensive library with 50,000+ books.",
                "Sports facilities include swimming pool, basketball court, and gym.",
                "Student hostels provide accommodation for 1000+ students.",
            ],
            "response": "Our campus features modern labs, a large library with extensive collections, sports facilities including a pool and gym, and hostels accommodating numerous students.",
        },
        {
            "query": "What scholarships are available?",
            "context": [
                "Merit-based scholarships cover 25-100% of tuition.",
                "Need-based scholarships available for eligible students.",
                "Application deadline for scholarships is June 15th.",
                "Scholarship amounts range from $5,000 to full tuition.",
            ],
            "response": "We offer both merit-based and need-based scholarships. Merit scholarships cover up to 100% of tuition for top performers.",
        },
        {
            "query": "How much does it cost to study engineering?",
            "context": [
                "Engineering tuition is $10,000 per year.",
                "Hostel fees are $3,000 per year.",
                "Laboratory charges are $500 per year.",
                "Total cost of engineering is approximately $13,500 per year.",
            ],
            "response": "Engineering costs $10,000 per year plus $3,000 for hostel and $500 for labs, totaling about $13,500 annually.",
        },
        {
            "query": "Tell me about faculty qualifications",
            "context": [
                "90% of faculty have PhDs from top universities.",
                "Faculty average 15 years of industry experience.",
                "Many faculty have published research papers.",
                "Faculty are actively involved in research projects.",
            ],
            "response": "Most faculty members hold PhDs and have extensive industry experience, actively contributing to research.",
        },
    ]


if __name__ == "__main__":
    # Run example evaluation
    runner = AutomaticRAGASRunner()
    test_cases = create_ragas_test_cases()

    results = runner.run_evaluation(test_cases)

    print("\nResults saved to:")
    for format_type, path in results.items():
        print(f"  {format_type}: {path}")
