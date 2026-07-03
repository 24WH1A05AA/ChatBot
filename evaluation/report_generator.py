"""
Report Generation Module

Generates comprehensive evaluation reports in multiple formats:
- JSON (detailed results)
- CSV (tabular data)
- HTML (visual reports)
- Text (human-readable)
"""

from typing import List, Dict, Any, Optional
from dataclasses import asdict
from datetime import datetime
import json
import csv
from pathlib import Path

from evaluation.evaluation_engine import EvaluationEngine, CategoryScore


class ReportGenerator:
    """Generates evaluation reports."""

    def __init__(self, engine: EvaluationEngine) -> None:
        """Initialize report generator."""
        self.engine = engine
        self.summary = engine.get_summary()

    def generate_json_report(self, filepath: str) -> None:
        """Generate JSON report."""
        self.engine.export_json(filepath)

    def generate_csv_report(self, filepath: str) -> None:
        """Generate CSV report with detailed results."""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Test ID",
                "Category",
                "Query",
                "Response",
                "Latency (ms)",
                "Passed",
                "Score",
                "Notes",
                "Timestamp",
            ])

            # Data rows
            for result in self.engine.results:
                writer.writerow([
                    result.test_id,
                    result.category,
                    result.query,
                    result.response or "",
                    f"{result.latency_ms:.2f}",
                    "Yes" if result.passed else "No",
                    f"{result.score:.2f}",
                    result.notes,
                    result.timestamp,
                ])

    def generate_category_csv_report(self, filepath: str) -> None:
        """Generate CSV report with category summaries."""
        category_scores = self.engine.get_category_scores()

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Category",
                "Total Tests",
                "Passed Tests",
                "Pass Rate (%)",
                "Average Score",
                "Average Latency (ms)",
                "Score Level",
            ])

            # Data rows
            for cs in category_scores:
                writer.writerow([
                    cs.category,
                    cs.total_tests,
                    cs.passed_tests,
                    f"{cs.pass_rate * 100:.1f}",
                    f"{cs.average_score:.2f}",
                    f"{cs.latency_avg_ms:.2f}",
                    self.engine.get_score_level_string(cs.average_score),
                ])

    def generate_text_report(self, filepath: str) -> None:
        """Generate human-readable text report."""
        overall = self.engine.get_overall_score()
        category_scores = self.engine.get_category_scores()

        lines = []
        lines.append("=" * 80)
        lines.append("CHATBOT EVALUATION REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Timestamp
        lines.append(f"Generated: {datetime.utcnow().isoformat()}")
        lines.append("")

        # Overall Results
        lines.append("OVERALL RESULTS")
        lines.append("-" * 80)
        lines.append(f"Overall Score:      {overall['overall_score']:.2f} ({overall['score_level'].upper()})")
        lines.append(f"Pass Rate:          {overall['pass_rate'] * 100:.1f}%")
        lines.append(f"Tests Run:          {overall['tests_run']}")
        lines.append(f"Tests Passed:       {overall['tests_passed']}")
        lines.append(f"Tests Failed:       {overall['tests_failed']}")
        lines.append("")

        # Category Breakdown
        lines.append("RESULTS BY CATEGORY")
        lines.append("-" * 80)
        lines.append(f"{'Category':<20} {'Tests':<10} {'Passed':<10} {'Pass %':<12} {'Score':<10} {'Avg Latency':<15}")
        lines.append("-" * 80)

        for cs in category_scores:
            lines.append(
                f"{cs.category:<20} {cs.total_tests:<10} {cs.passed_tests:<10} "
                f"{cs.pass_rate * 100:<11.1f}% {cs.average_score:<10.2f} {cs.latency_avg_ms:<14.2f}ms"
            )

        lines.append("")

        # Detailed Results (first 20)
        lines.append("SAMPLE DETAILED RESULTS (first 20 tests)")
        lines.append("-" * 80)

        for i, result in enumerate(self.engine.results[:20]):
            lines.append(f"\nTest {i + 1}: {result.test_id}")
            lines.append(f"  Category:  {result.category}")
            lines.append(f"  Query:     {result.query}")
            lines.append(f"  Response:  {result.response or 'None'}")
            lines.append(f"  Latency:   {result.latency_ms:.2f}ms")
            lines.append(f"  Status:    {'PASSED' if result.passed else 'FAILED'}")
            lines.append(f"  Score:     {result.score:.2f}")
            lines.append(f"  Notes:     {result.notes}")

        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        with open(filepath, 'w') as f:
            f.write("\n".join(lines))

    def generate_html_report(self, filepath: str) -> None:
        """Generate HTML report with charts."""
        overall = self.engine.get_overall_score()
        category_scores = self.engine.get_category_scores()

        # Prepare data for charts
        categories_list = [cs.category for cs in category_scores]
        scores_list = [cs.average_score for cs in category_scores]
        pass_rates_list = [cs.pass_rate * 100 for cs in category_scores]

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot Evaluation Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .timestamp {{
            font-size: 12px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .metric {{
            display: inline-block;
            margin-right: 30px;
            margin-bottom: 20px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        .chart-container {{
            position: relative;
            margin: 30px 0;
            height: 400px;
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .table th {{
            background: #f5f5f5;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }}
        .table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        .table tr:hover {{
            background: #f9f9f9;
        }}
        .status-passed {{
            color: #27ae60;
            font-weight: 600;
        }}
        .status-failed {{
            color: #e74c3c;
            font-weight: 600;
        }}
        .score-excellent {{
            background: #27ae60;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .score-good {{
            background: #3498db;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .score-fair {{
            background: #f39c12;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .score-poor {{
            background: #e74c3c;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        section {{
            margin-bottom: 40px;
        }}
        h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Chatbot Evaluation Report</h1>
            <p class="timestamp">Generated: {datetime.utcnow().isoformat()}</p>
        </header>

        <div class="content">
            <!-- Overall Metrics -->
            <section>
                <h2>Overall Performance</h2>
                <div class="metric">
                    <div class="metric-value">{overall['overall_score']:.2f}</div>
                    <div class="metric-label">Overall Score</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{overall['pass_rate'] * 100:.1f}%</div>
                    <div class="metric-label">Pass Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{overall['tests_passed']}/{overall['tests_run']}</div>
                    <div class="metric-label">Tests Passed</div>
                </div>
            </section>

            <!-- Category Scores Chart -->
            <section>
                <h2>Scores by Category</h2>
                <div class="chart-container">
                    <canvas id="categoryScoresChart"></canvas>
                </div>
            </section>

            <!-- Pass Rates Chart -->
            <section>
                <h2>Pass Rates by Category</h2>
                <div class="chart-container">
                    <canvas id="passRatesChart"></canvas>
                </div>
            </section>

            <!-- Category Table -->
            <section>
                <h2>Category Breakdown</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Tests</th>
                            <th>Passed</th>
                            <th>Pass Rate</th>
                            <th>Avg Score</th>
                            <th>Avg Latency (ms)</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        for cs in category_scores:
            score_class = self._get_score_css_class(cs.average_score)
            html += f"""
                        <tr>
                            <td>{cs.category}</td>
                            <td>{cs.total_tests}</td>
                            <td>{cs.passed_tests}</td>
                            <td>{cs.pass_rate * 100:.1f}%</td>
                            <td><span class="{score_class}">{cs.average_score:.2f}</span></td>
                            <td>{cs.latency_avg_ms:.2f}</td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </section>
        </div>

        <footer>
            <p>Chatbot Evaluation System | College FAQ Bot</p>
        </footer>
    </div>

    <script>
        // Category Scores Chart
        const categoryScoresCtx = document.getElementById('categoryScoresChart').getContext('2d');
        new Chart(categoryScoresCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(categories_list) + """,
                datasets: [{
                    label: 'Average Score',
                    data: """ + json.dumps(scores_list) + """,
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#4facfe',
                        '#00f2fe', '#43e97b', '#fa709a', '#fee140'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0
                    }
                }
            }
        });

        // Pass Rates Chart
        const passRatesCtx = document.getElementById('passRatesChart').getContext('2d');
        new Chart(passRatesCtx, {
            type: 'line',
            data: {
                labels: """ + json.dumps(categories_list) + """,
                datasets: [{
                    label: 'Pass Rate (%)',
                    data: """ + json.dumps(pass_rates_list) + """,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

        with open(filepath, 'w') as f:
            f.write(html)

    def _get_score_css_class(self, score: float) -> str:
        """Get CSS class for score."""
        if score >= 0.8:
            return "score-excellent"
        elif score >= 0.7:
            return "score-good"
        elif score >= 0.6:
            return "score-fair"
        else:
            return "score-poor"
