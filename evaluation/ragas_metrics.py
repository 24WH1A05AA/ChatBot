"""
Enhanced RAGAS Evaluation System

Provides advanced RAGAS metric computation with:
- Automatic evaluation runs
- Score analysis and display
- Weakness detection
- Improvement recommendations
- Detailed diagnostics
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
import statistics


class MetricLevel(Enum):
    """Metric performance levels."""
    EXCELLENT = "excellent"  # 0.85-1.0
    GOOD = "good"  # 0.7-0.85
    FAIR = "fair"  # 0.6-0.7
    POOR = "poor"  # 0.4-0.6
    CRITICAL = "critical"  # < 0.4


@dataclass
class RAGASScore:
    """A single RAGAS evaluation result."""
    query: str
    response: str
    context: List[str]
    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "response": self.response,
            "context": self.context,
            "metrics": {
                "faithfulness": self.faithfulness,
                "answer_relevancy": self.answer_relevancy,
                "context_recall": self.context_recall,
                "context_precision": self.context_precision,
            },
            "timestamp": self.timestamp,
        }

    def get_average(self) -> float:
        """Get average of all metrics."""
        scores = [
            self.faithfulness,
            self.answer_relevancy,
            self.context_recall,
            self.context_precision,
        ]
        return sum(scores) / len(scores) if scores else 0.0


@dataclass
class RAGASMetrics:
    """Enhanced RAGAS metrics evaluation."""
    
    scores: List[RAGASScore] = field(default_factory=list)

    def compute_faithfulness(self, answer: str, context: List[str]) -> float:
        """
        Compute faithfulness score (0.0-1.0).
        
        Measures: Whether answer is grounded in provided context
        Method: Word overlap between answer and context
        Target: > 0.7
        """
        if not answer or not context:
            return 0.0

        # Clean and split
        answer_words = set(word.lower() for word in answer.split() if len(word) > 2)
        context_words = set()
        
        for ctx in context:
            context_words.update(word.lower() for word in ctx.split() if len(word) > 2)

        if not answer_words or not context_words:
            return 0.0

        # Calculate overlap ratio
        overlap = len(answer_words & context_words)
        faithfulness = overlap / len(answer_words) if answer_words else 0.0
        
        # Boost for high overlap, penalize for no context usage
        if faithfulness > 0.8:
            faithfulness = min(faithfulness + 0.1, 1.0)
        elif faithfulness < 0.2:
            faithfulness = max(faithfulness - 0.2, 0.0)

        return min(max(faithfulness, 0.0), 1.0)

    def compute_context_precision(self, query: str, context: List[str]) -> float:
        """
        Compute context precision score (0.0-1.0).
        
        Measures: Fraction of retrieved context that is relevant to query
        Method: Query term presence in context documents
        Target: > 0.75
        """
        if not context or not query:
            return 0.0

        # Extract meaningful query terms
        query_terms = set(
            term.lower() for term in query.split()
            if len(term) > 3 and term.lower() not in ['what', 'tell', 'about', 'that']
        )

        if not query_terms:
            return 0.5

        # Count relevant documents
        relevant_count = 0
        for ctx in context:
            ctx_terms = set(word.lower() for word in ctx.split() if len(word) > 3)
            if query_terms & ctx_terms:  # Has overlap
                relevant_count += 1

        precision = relevant_count / len(context) if context else 0.0
        return min(max(precision, 0.0), 1.0)

    def compute_context_recall(self, query: str, context: List[str]) -> float:
        """
        Compute context recall score (0.0-1.0).
        
        Measures: Comprehensiveness of retrieved context
        Method: Total relevant information coverage
        Target: > 0.8
        """
        if not context:
            return 0.0

        # Assess content completeness
        total_length = sum(len(ctx) for ctx in context)
        doc_count = len(context)

        # Heuristic: more content and more documents = better recall
        length_score = min(total_length / 1000, 1.0)  # Max at 1000 chars
        doc_score = min(doc_count / 5, 1.0)  # Max at 5 documents

        # Combine with emphasis on length
        recall = (length_score * 0.7) + (doc_score * 0.3)

        return min(max(recall, 0.0), 1.0)

    def compute_answer_relevancy(self, query: str, answer: str) -> float:
        """
        Compute answer relevancy score (0.0-1.0).
        
        Measures: How directly the answer addresses the query
        Method: Query term coverage in answer
        Target: > 0.85
        """
        if not answer or not query:
            return 0.0

        # Extract query terms
        query_terms = set(
            term.lower() for term in query.split()
            if len(term) > 3 and term.lower() not in ['what', 'tell', 'about', 'that']
        )

        if not query_terms:
            return 0.5

        # Check answer coverage
        answer_words = set(word.lower() for word in answer.split() if len(word) > 3)
        covered = len(query_terms & answer_words)
        relevancy = covered / len(query_terms) if query_terms else 0.0

        # Boost for direct coverage
        if relevancy > 0.7:
            relevancy = min(relevancy + 0.15, 1.0)

        return min(max(relevancy, 0.0), 1.0)

    def evaluate(
        self,
        query: str,
        response: str,
        context: List[str],
    ) -> RAGASScore:
        """Evaluate a single response using all RAGAS metrics."""
        
        faithfulness = self.compute_faithfulness(response, context)
        context_precision = self.compute_context_precision(query, context)
        context_recall = self.compute_context_recall(query, context)
        answer_relevancy = self.compute_answer_relevancy(query, response)

        score = RAGASScore(
            query=query,
            response=response,
            context=context,
            faithfulness=faithfulness,
            context_precision=context_precision,
            context_recall=context_recall,
            answer_relevancy=answer_relevancy,
        )

        self.scores.append(score)
        return score

    def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]],
    ) -> List[RAGASScore]:
        """
        Evaluate multiple cases.
        
        Args:
            test_cases: List of dicts with 'query', 'response', 'context'
        
        Returns:
            List of RAGASScore objects
        """
        results = []
        for case in test_cases:
            score = self.evaluate(
                query=case.get('query', ''),
                response=case.get('response', ''),
                context=case.get('context', []),
            )
            results.append(score)
        return results

    def get_average_scores(self) -> Dict[str, float]:
        """Get average score for each metric."""
        if not self.scores:
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_recall": 0.0,
                "context_precision": 0.0,
                "average": 0.0,
            }

        faithfulness_scores = [s.faithfulness for s in self.scores]
        answer_relevancy_scores = [s.answer_relevancy for s in self.scores]
        context_recall_scores = [s.context_recall for s in self.scores]
        context_precision_scores = [s.context_precision for s in self.scores]

        avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
        avg_answer_relevancy = sum(answer_relevancy_scores) / len(answer_relevancy_scores)
        avg_context_recall = sum(context_recall_scores) / len(context_recall_scores)
        avg_context_precision = sum(context_precision_scores) / len(context_precision_scores)

        avg_all = (
            avg_faithfulness + avg_answer_relevancy +
            avg_context_recall + avg_context_precision
        ) / 4

        return {
            "faithfulness": avg_faithfulness,
            "answer_relevancy": avg_answer_relevancy,
            "context_recall": avg_context_recall,
            "context_precision": avg_context_precision,
            "average": avg_all,
        }

    def get_metric_level(self, score: float) -> MetricLevel:
        """Classify metric score into level."""
        if score >= 0.85:
            return MetricLevel.EXCELLENT
        elif score >= 0.7:
            return MetricLevel.GOOD
        elif score >= 0.6:
            return MetricLevel.FAIR
        elif score >= 0.4:
            return MetricLevel.POOR
        else:
            return MetricLevel.CRITICAL

    def get_weakest_metric(self) -> Tuple[str, float]:
        """Get the weakest metric and its score."""
        averages = self.get_average_scores()
        
        # Remove 'average' key for comparison
        metric_scores = {k: v for k, v in averages.items() if k != 'average'}
        
        weakest_metric = min(metric_scores, key=metric_scores.get)
        weakest_score = metric_scores[weakest_metric]
        
        return (weakest_metric, weakest_score)

    def get_recommendations(self) -> Dict[str, List[str]]:
        """Get improvement recommendations based on metric scores."""
        averages = self.get_average_scores()
        recommendations = {}

        # Faithfulness recommendations
        if averages['faithfulness'] < 0.7:
            recommendations['faithfulness'] = [
                "Ensure responses directly cite retrieved context",
                "Reduce speculation and unsupported claims",
                "Validate answer against source documents",
                "Use context-based language in responses",
            ]

        # Answer Relevancy recommendations
        if averages['answer_relevancy'] < 0.75:
            recommendations['answer_relevancy'] = [
                "Address all key aspects of the query",
                "Include specific terms from the question",
                "Provide direct answers before elaboration",
                "Avoid tangential information",
            ]

        # Context Recall recommendations
        if averages['context_recall'] < 0.75:
            recommendations['context_recall'] = [
                "Retrieve more relevant documents",
                "Improve chunking strategy",
                "Expand knowledge base coverage",
                "Enhance semantic search relevance",
            ]

        # Context Precision recommendations
        if averages['context_precision'] < 0.7:
            recommendations['context_precision'] = [
                "Improve retrieval filtering",
                "Add semantic reranking",
                "Use query expansion techniques",
                "Refine embedding model",
            ]

        return recommendations

    def generate_detailed_report(self) -> Dict[str, Any]:
        """Generate comprehensive RAGAS analysis report."""
        averages = self.get_average_scores()
        weakest_metric, weakest_score = self.get_weakest_metric()
        recommendations = self.get_recommendations()

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "faithfulness": {
                    "score": averages['faithfulness'],
                    "level": self.get_metric_level(averages['faithfulness']).value,
                    "target": 0.8,
                    "status": "✅" if averages['faithfulness'] >= 0.8 else "⚠️",
                },
                "answer_relevancy": {
                    "score": averages['answer_relevancy'],
                    "level": self.get_metric_level(averages['answer_relevancy']).value,
                    "target": 0.85,
                    "status": "✅" if averages['answer_relevancy'] >= 0.85 else "⚠️",
                },
                "context_recall": {
                    "score": averages['context_recall'],
                    "level": self.get_metric_level(averages['context_recall']).value,
                    "target": 0.8,
                    "status": "✅" if averages['context_recall'] >= 0.8 else "⚠️",
                },
                "context_precision": {
                    "score": averages['context_precision'],
                    "level": self.get_metric_level(averages['context_precision']).value,
                    "target": 0.75,
                    "status": "✅" if averages['context_precision'] >= 0.75 else "⚠️",
                },
                "overall": {
                    "score": averages['average'],
                    "level": self.get_metric_level(averages['average']).value,
                },
            },
            "analysis": {
                "total_evaluations": len(self.scores),
                "weakest_metric": weakest_metric,
                "weakest_score": weakest_score,
                "strongest_metric": max(
                    (k, v) for k, v in averages.items() if k != 'average'
                )[0] if averages else "N/A",
            },
            "recommendations": recommendations,
        }

        return report

    def print_score_summary(self) -> None:
        """Print formatted score summary."""
        print("\n" + "=" * 80)
        print("RAGAS EVALUATION SUMMARY")
        print("=" * 80)

        averages = self.get_average_scores()

        print("\nMetric Scores:")
        print(f"{'Metric':<25} {'Score':<10} {'Level':<15} {'Target':<10} {'Status':<5}")
        print("-" * 80)

        metrics_info = [
            ("Faithfulness", averages['faithfulness'], 0.8),
            ("Answer Relevancy", averages['answer_relevancy'], 0.85),
            ("Context Recall", averages['context_recall'], 0.8),
            ("Context Precision", averages['context_precision'], 0.75),
        ]

        for metric_name, score, target in metrics_info:
            level = self.get_metric_level(score)
            status = "✅" if score >= target else "⚠️"
            print(
                f"{metric_name:<25} {score:<10.2f} {level.value:<15} "
                f"{target:<10.2f} {status:<5}"
            )

        print(f"\n{'OVERALL':<25} {averages['average']:<10.2f}")
        print("=" * 80)

        # Highlight weakest metric
        weakest_metric, weakest_score = self.get_weakest_metric()
        print(f"\n⚠️  WEAKEST METRIC: {weakest_metric.upper()} ({weakest_score:.2f})")

        # Show recommendations
        recommendations = self.get_recommendations()
        if recommendations:
            print("\n" + "🔧 IMPROVEMENT RECOMMENDATIONS")
            print("-" * 80)
            for metric, recs in recommendations.items():
                print(f"\n{metric.replace('_', ' ').upper()}:")
                for rec in recs:
                    print(f"  • {rec}")

        print("\n" + "=" * 80 + "\n")

    def export_report(self, filepath: str) -> None:
        """Export detailed report to JSON."""
        report = self.generate_detailed_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
