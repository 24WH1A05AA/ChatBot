"""
Tests for RAGAS evaluation system.
"""

import pytest
from evaluation.ragas_metrics import RAGASMetrics, MetricLevel, RAGASScore
from evaluation.ragas_runner import AutomaticRAGASRunner, create_ragas_test_cases


class TestRAGASMetrics:
    """Tests for RAGAS metrics."""

    def test_compute_faithfulness(self):
        """Test faithfulness computation."""
        metrics = RAGASMetrics()
        
        answer = "The deadline is March 31st"
        context = ["The college admission deadline is March 31st"]
        
        score = metrics.compute_faithfulness(answer, context)
        assert 0 <= score <= 1
        assert score > 0.5  # Should have high overlap

    def test_compute_faithfulness_low(self):
        """Test faithfulness with poor grounding."""
        metrics = RAGASMetrics()
        
        answer = "Purple elephants dance on Thursdays"
        context = ["The college admission deadline is March 31st"]
        
        score = metrics.compute_faithfulness(answer, context)
        assert score < 0.3  # Low overlap

    def test_compute_context_precision(self):
        """Test context precision."""
        metrics = RAGASMetrics()
        
        query = "What is the admission deadline?"
        context = [
            "The admission deadline is March 31st",
            "The campus is beautiful",
        ]
        
        score = metrics.compute_context_precision(query, context)
        assert 0 <= score <= 1
        # First doc is relevant, second not
        assert score == 0.5

    def test_compute_context_recall(self):
        """Test context recall."""
        metrics = RAGASMetrics()
        
        query = "Tell me about facilities"
        context = [
            "We have labs, library, sports facilities, and hostels",
        ]
        
        score = metrics.compute_context_recall(query, context)
        assert 0 <= score <= 1

    def test_compute_answer_relevancy(self):
        """Test answer relevancy."""
        metrics = RAGASMetrics()
        
        query = "What is the tuition fee?"
        answer = "The tuition fee for engineering is $10,000 per year"
        
        score = metrics.compute_answer_relevancy(query, answer)
        assert 0 <= score <= 1
        assert score >= 0.5  # Should address the query

    def test_compute_answer_relevancy_low(self):
        """Test answer relevancy with poor match."""
        metrics = RAGASMetrics()
        
        query = "What is the tuition fee?"
        answer = "The weather is sunny today"
        
        score = metrics.compute_answer_relevancy(query, answer)
        assert score < 0.3  # Doesn't address query

    def test_evaluate_single(self):
        """Test evaluating a single response."""
        metrics = RAGASMetrics()
        
        score = metrics.evaluate(
            query="What is the deadline?",
            response="The deadline is March 31st",
            context=["The admission deadline is March 31st"]
        )
        
        assert isinstance(score, RAGASScore)
        assert 0 <= score.faithfulness <= 1
        assert 0 <= score.answer_relevancy <= 1
        assert 0 <= score.context_recall <= 1
        assert 0 <= score.context_precision <= 1

    def test_evaluate_batch(self):
        """Test batch evaluation."""
        metrics = RAGASMetrics()
        
        cases = [
            {
                "query": "What is the deadline?",
                "response": "March 31st",
                "context": ["Deadline is March 31st"]
            },
            {
                "query": "What are facilities?",
                "response": "We have labs and library",
                "context": ["Labs, library, sports"]
            }
        ]
        
        results = metrics.evaluate_batch(cases)
        assert len(results) == 2
        assert all(isinstance(r, RAGASScore) for r in results)

    def test_get_average_scores(self):
        """Test average score calculation."""
        metrics = RAGASMetrics()
        
        metrics.evaluate(
            "What is the deadline?",
            "March 31st",
            ["Deadline is March 31st"]
        )
        
        averages = metrics.get_average_scores()
        assert 'faithfulness' in averages
        assert 'answer_relevancy' in averages
        assert 'context_recall' in averages
        assert 'context_precision' in averages
        assert 'average' in averages
        assert 0 <= averages['average'] <= 1

    def test_get_metric_level(self):
        """Test metric level classification."""
        metrics = RAGASMetrics()
        
        assert metrics.get_metric_level(0.95) == MetricLevel.EXCELLENT
        assert metrics.get_metric_level(0.75) == MetricLevel.GOOD
        assert metrics.get_metric_level(0.65) == MetricLevel.FAIR
        assert metrics.get_metric_level(0.50) == MetricLevel.POOR
        assert metrics.get_metric_level(0.30) == MetricLevel.CRITICAL

    def test_get_weakest_metric(self):
        """Test getting weakest metric."""
        metrics = RAGASMetrics()
        
        # Add diverse scores
        metrics.evaluate("Q1", "Response with low relevancy", ["Context"])
        metrics.evaluate("Q2", "Response", ["With low recall"])
        
        weakest_metric, weakest_score = metrics.get_weakest_metric()
        assert weakest_metric in ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
        assert 0 <= weakest_score <= 1

    def test_get_recommendations(self):
        """Test recommendation generation."""
        metrics = RAGASMetrics()
        
        # Add poor scores
        metrics.evaluate("Q", "Unrelated answer", ["Context"])
        
        recommendations = metrics.get_recommendations()
        
        # Should have recommendations for poor metrics
        assert isinstance(recommendations, dict)
        assert all(isinstance(v, list) for v in recommendations.values())

    def test_generate_detailed_report(self):
        """Test detailed report generation."""
        metrics = RAGASMetrics()
        
        metrics.evaluate(
            "What is the deadline?",
            "March 31st",
            ["Deadline is March 31st"]
        )
        
        report = metrics.generate_detailed_report()
        
        assert 'timestamp' in report
        assert 'metrics' in report
        assert 'analysis' in report
        assert 'recommendations' in report
        assert report['metrics']['faithfulness']['score'] >= 0


class TestAutomaticRAGASRunner:
    """Tests for automatic RAGAS runner."""

    def test_creates_runner(self, tmp_path):
        """Test runner creation."""
        runner = AutomaticRAGASRunner(output_dir=str(tmp_path))
        assert runner is not None

    def test_run_evaluation(self, tmp_path):
        """Test running evaluation."""
        runner = AutomaticRAGASRunner(output_dir=str(tmp_path))
        
        test_cases = create_ragas_test_cases()
        # Run evaluation silently (suppress print statements)
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            results = runner.run_evaluation(test_cases)
        finally:
            sys.stdout = old_stdout
        
        assert 'json_report' in results
        assert 'csv_scores' in results
        assert 'text_summary' in results

    def test_get_summary(self, tmp_path):
        """Test summary generation."""
        runner = AutomaticRAGASRunner(output_dir=str(tmp_path))
        
        test_cases = create_ragas_test_cases()
        # Run evaluation silently
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            runner.run_evaluation(test_cases)
        finally:
            sys.stdout = old_stdout
        
        summary = runner.get_summary()
        
        assert summary['status'] == 'complete'
        assert summary['total_evaluations'] > 0
        assert 'metrics' in summary
        assert 'weakest_metric' in summary
        assert 'recommendations' in summary

    def test_create_test_cases(self):
        """Test test case creation."""
        cases = create_ragas_test_cases()
        
        assert len(cases) > 0
        assert all('query' in c for c in cases)
        assert all('context' in c for c in cases)
        assert all('response' in c for c in cases)


class TestRAGASScore:
    """Tests for RAGAS score data class."""

    def test_to_dict(self):
        """Test conversion to dict."""
        score = RAGASScore(
            query="Test query",
            response="Test response",
            context=["Context 1", "Context 2"],
            faithfulness=0.8,
            answer_relevancy=0.85,
            context_recall=0.75,
            context_precision=0.7,
        )
        
        result = score.to_dict()
        assert result['query'] == "Test query"
        assert result['response'] == "Test response"
        assert result['metrics']['faithfulness'] == 0.8

    def test_get_average(self):
        """Test average calculation."""
        score = RAGASScore(
            query="Q",
            response="R",
            context=["C"],
            faithfulness=0.8,
            answer_relevancy=0.8,
            context_recall=0.8,
            context_precision=0.8,
        )
        
        avg = score.get_average()
        assert avg == 0.8

    def test_get_average_diverse(self):
        """Test average with diverse scores."""
        score = RAGASScore(
            query="Q",
            response="R",
            context=["C"],
            faithfulness=1.0,
            answer_relevancy=0.5,
            context_recall=0.75,
            context_precision=0.75,
        )
        
        avg = score.get_average()
        assert abs(avg - 0.75) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
