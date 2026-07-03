"""
Analytics Tracking System

Comprehensive analytics for:
- Popular and failed questions
- Hallucination attempts
- Retrieval quality metrics
- Latency tracking
- RAGAS scores
- Citation usage
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter
import json
from pathlib import Path
import statistics


class QueryStatus(Enum):
    """Query outcome status."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    ERROR = "error"


class HallucinationType(Enum):
    """Type of hallucination detected."""
    FACTUAL_ERROR = "factual_error"
    OUT_OF_CONTEXT = "out_of_context"
    CONTRADICTORY = "contradictory"
    FABRICATED = "fabricated"
    UNSUPPORTED = "unsupported"


@dataclass
class QueryMetrics:
    """Metrics for a single query."""
    query_id: str
    query_text: str
    status: str
    timestamp: str
    latency_ms: float
    
    # Retrieval metrics
    retrieved_chunks: int
    retrieval_quality_score: float  # 0.0-1.0
    
    # RAGAS metrics
    faithfulness_score: float
    answer_relevancy_score: float
    context_recall_score: float
    context_precision_score: float
    ragas_average: float
    
    # Citation metrics
    citations_found: int
    citations_used: int
    citation_accuracy: float  # 0.0-1.0
    
    # Hallucination detection
    hallucination_detected: bool
    hallucination_type: Optional[str] = None
    hallucination_severity: float = 0.0  # 0.0-1.0
    
    # Response quality
    response_length: int = 0
    user_satisfaction: Optional[float] = None  # 0.0-1.0 if provided
    
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnalyticsSession:
    """Session-level analytics."""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    query_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    avg_ragas_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AnalyticsCollector:
    """Collects and aggregates analytics data."""

    def __init__(self, data_file: str = "analytics_data.json") -> None:
        """Initialize collector."""
        self.data_file = Path(data_file)
        self.queries: List[QueryMetrics] = self._load_queries()
        self.sessions: List[AnalyticsSession] = []
        self.current_session: Optional[AnalyticsSession] = None

    def _load_queries(self) -> List[QueryMetrics]:
        """Load previous queries from file."""
        if not self.data_file.exists():
            return []

        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return [QueryMetrics(**q) for q in data.get("queries", [])]
        except Exception as e:
            print(f"Error loading queries: {e}")
            return []

    def _save_queries(self) -> None:
        """Save queries to file."""
        try:
            with open(self.data_file, 'w') as f:
                data = {
                    "queries": [q.to_dict() for q in self.queries[-1000:]],  # Last 1000
                    "timestamp": datetime.utcnow().isoformat(),
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving queries: {e}")

    def start_session(self) -> str:
        """Start a new analytics session."""
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = AnalyticsSession(
            session_id=session_id,
            start_time=datetime.utcnow().isoformat(),
        )
        return session_id

    def end_session(self) -> Optional[AnalyticsSession]:
        """End current session."""
        if self.current_session:
            self.current_session.end_time = datetime.utcnow().isoformat()
            self.sessions.append(self.current_session)
            session = self.current_session
            self.current_session = None
            return session
        return None

    def record_query(self, metrics: QueryMetrics) -> None:
        """Record a query's metrics."""
        self.queries.append(metrics)

        # Update current session
        if self.current_session:
            self.current_session.query_count += 1
            self.current_session.total_latency_ms += metrics.latency_ms

            if metrics.status == QueryStatus.SUCCESS.value:
                self.current_session.success_count += 1
            elif metrics.status == QueryStatus.FAILED.value:
                self.current_session.failure_count += 1

        self._save_queries()

    def get_popular_questions(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently asked questions."""
        question_counts = Counter(q.query_text for q in self.queries)
        return question_counts.most_common(limit)

    def get_failed_questions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get frequently failed questions."""
        failed = [q for q in self.queries if q.status == QueryStatus.FAILED.value]
        failed_text_counts = Counter(q.query_text for q in failed)

        results = []
        for query_text, count in failed_text_counts.most_common(limit):
            failure_examples = [q for q in failed if q.query_text == query_text]
            results.append({
                "query": query_text,
                "failure_count": count,
                "total_attempts": sum(
                    1 for q in self.queries if q.query_text == query_text
                ),
                "failure_rate": count / sum(
                    1 for q in self.queries if q.query_text == query_text
                ),
                "latest_failure": failure_examples[0].to_dict() if failure_examples else None,
            })

        return results

    def get_hallucination_stats(self) -> Dict[str, Any]:
        """Get hallucination detection statistics."""
        hallucinated = [q for q in self.queries if q.hallucination_detected]

        hallucination_types = Counter(
            q.hallucination_type for q in hallucinated if q.hallucination_type
        )

        severity_scores = [q.hallucination_severity for q in hallucinated]

        return {
            "total_hallucinations": len(hallucinated),
            "hallucination_rate": len(hallucinated) / len(self.queries) if self.queries else 0,
            "by_type": dict(hallucination_types),
            "avg_severity": statistics.mean(severity_scores) if severity_scores else 0,
            "max_severity": max(severity_scores) if severity_scores else 0,
            "recent": [q.to_dict() for q in hallucinated[-5:]],
        }

    def get_retrieval_quality_stats(self) -> Dict[str, float]:
        """Get retrieval quality statistics."""
        if not self.queries:
            return {}

        scores = [q.retrieval_quality_score for q in self.queries]

        return {
            "avg_score": statistics.mean(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "median": statistics.median(scores),
        }

    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics (in milliseconds)."""
        if not self.queries:
            return {}

        latencies = [q.latency_ms for q in self.queries]

        return {
            "avg_latency_ms": statistics.mean(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "p50_latency_ms": statistics.median(latencies),
            "p95_latency_ms": (
                sorted(latencies)[int(len(latencies) * 0.95)]
                if latencies else 0
            ),
            "p99_latency_ms": (
                sorted(latencies)[int(len(latencies) * 0.99)]
                if latencies else 0
            ),
        }

    def get_ragas_stats(self) -> Dict[str, Any]:
        """Get RAGAS metrics statistics."""
        if not self.queries:
            return {}

        faithfulness = [q.faithfulness_score for q in self.queries]
        relevancy = [q.answer_relevancy_score for q in self.queries]
        recall = [q.context_recall_score for q in self.queries]
        precision = [q.context_precision_score for q in self.queries]
        average = [q.ragas_average for q in self.queries]

        return {
            "faithfulness": {
                "avg": statistics.mean(faithfulness),
                "min": min(faithfulness),
                "max": max(faithfulness),
                "median": statistics.median(faithfulness),
            },
            "answer_relevancy": {
                "avg": statistics.mean(relevancy),
                "min": min(relevancy),
                "max": max(relevancy),
                "median": statistics.median(relevancy),
            },
            "context_recall": {
                "avg": statistics.mean(recall),
                "min": min(recall),
                "max": max(recall),
                "median": statistics.median(recall),
            },
            "context_precision": {
                "avg": statistics.mean(precision),
                "min": min(precision),
                "max": max(precision),
                "median": statistics.median(precision),
            },
            "overall_average": {
                "avg": statistics.mean(average),
                "min": min(average),
                "max": max(average),
                "median": statistics.median(average),
            },
        }

    def get_citation_stats(self) -> Dict[str, Any]:
        """Get citation usage statistics."""
        if not self.queries:
            return {}

        citations_found = [q.citations_found for q in self.queries]
        citations_used = [q.citations_used for q in self.queries]
        accuracies = [q.citation_accuracy for q in self.queries if q.citations_found > 0]

        return {
            "avg_citations_found": statistics.mean(citations_found),
            "avg_citations_used": statistics.mean(citations_used),
            "citation_usage_rate": (
                statistics.mean(citations_used) / statistics.mean(citations_found)
                if statistics.mean(citations_found) > 0 else 0
            ),
            "avg_citation_accuracy": statistics.mean(accuracies) if accuracies else 0,
            "queries_with_citations": sum(1 for q in self.queries if q.citations_found > 0),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        return {
            "total_queries": len(self.queries),
            "success_rate": (
                sum(1 for q in self.queries if q.status == QueryStatus.SUCCESS.value) / 
                len(self.queries) if self.queries else 0
            ),
            "popular_questions": self.get_popular_questions(5),
            "failed_questions": self.get_failed_questions(5),
            "hallucination_stats": self.get_hallucination_stats(),
            "retrieval_quality": self.get_retrieval_quality_stats(),
            "latency_stats": self.get_latency_stats(),
            "ragas_stats": self.get_ragas_stats(),
            "citation_stats": self.get_citation_stats(),
        }

    def export_analytics(self, filepath: str) -> None:
        """Export all analytics to JSON."""
        summary = self.get_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)


class AnalyticsQueryBuilder:
    """Helper to build analytics queries easily."""

    @staticmethod
    def create_query_metrics(
        query_id: str,
        query_text: str,
        status: str,
        latency_ms: float,
        retrieved_chunks: int,
        retrieval_quality: float,
        faithfulness: float,
        answer_relevancy: float,
        context_recall: float,
        context_precision: float,
        citations_found: int,
        citations_used: int,
        citation_accuracy: float,
        hallucination_detected: bool = False,
        hallucination_type: Optional[str] = None,
        hallucination_severity: float = 0.0,
        response_length: int = 0,
        user_satisfaction: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QueryMetrics:
        """Build a QueryMetrics object."""
        ragas_average = (
            faithfulness + answer_relevancy + context_recall + context_precision
        ) / 4

        return QueryMetrics(
            query_id=query_id,
            query_text=query_text,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            latency_ms=latency_ms,
            retrieved_chunks=retrieved_chunks,
            retrieval_quality_score=retrieval_quality,
            faithfulness_score=faithfulness,
            answer_relevancy_score=answer_relevancy,
            context_recall_score=context_recall,
            context_precision_score=context_precision,
            ragas_average=ragas_average,
            citations_found=citations_found,
            citations_used=citations_used,
            citation_accuracy=citation_accuracy,
            hallucination_detected=hallucination_detected,
            hallucination_type=hallucination_type,
            hallucination_severity=hallucination_severity,
            response_length=response_length,
            user_satisfaction=user_satisfaction,
            metadata=metadata or {},
        )
