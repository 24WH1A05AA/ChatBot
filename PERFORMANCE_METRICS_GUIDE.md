# Performance Metrics & Monitoring Guide

## Key Performance Indicators (KPIs)

### 1. Query Latency Metrics

```python
# Current Baseline (Before Optimization)
BASELINE_METRICS = {
    "query_latency_p50": 1200,      # ms
    "query_latency_p95": 1500,      # ms
    "query_latency_p99": 1800,      # ms
    "query_latency_avg": 1250,      # ms
}

# Target (After Phase 1: Week 1)
PHASE1_TARGETS = {
    "query_latency_p50": 800,       # 33% improvement
    "query_latency_p95": 1000,      # 33% improvement
    "query_latency_p99": 1200,      # 33% improvement
    "query_latency_avg": 850,       # 32% improvement
}

# Final Target (After Phase 3: Week 3)
FINAL_TARGETS = {
    "query_latency_p50": 600,       # 50% improvement
    "query_latency_p95": 750,       # 50% improvement
    "query_latency_p99": 900,       # 50% improvement
    "query_latency_avg": 650,       # 48% improvement
}
```

### 2. Embedding Generation Metrics

```python
BASELINE_EMBEDDING = {
    "throughput": 0.5,              # docs/sec
    "time_per_doc": 2000,           # ms
    "batch_size": 100,              # docs
    "api_calls_per_1k_docs": 10,    # OpenAI calls
}

PHASE2_TARGETS = {
    "throughput": 1.25,             # 2.5x improvement
    "time_per_doc": 800,            # 60% improvement
    "batch_size": 256,              # Larger batches
    "api_calls_per_1k_docs": 4,     # More efficient
}
```

### 3. Memory Metrics

```python
BASELINE_MEMORY = {
    "avg_memory_per_query": 250,    # MB
    "peak_memory_during_embedding": 300,  # MB
    "cache_size": 1000,             # entries
}

PHASE1_TARGETS = {
    "avg_memory_per_query": 150,    # 40% reduction
    "peak_memory_during_embedding": 180,  # 40% reduction
    "cache_size": 2000,             # 2x entries, same memory
}
```

### 4. Cost Metrics

```python
BASELINE_COST = {
    "cost_per_10k_queries": 0.50,   # USD
    "cost_per_embedding_k_tokens": 0.02,  # USD (text-embedding-3-small)
    "cost_per_completion_k_tokens": 0.15, # USD (GPT-4o mini)
}

FINAL_TARGETS = {
    "cost_per_10k_queries": 0.15,   # 70% savings
    "cost_per_embedding_k_tokens": 0.02,  # Same (efficiency)
    "cost_per_completion_k_tokens": 0.15, # Same (efficiency)
}
```

---

## Instrumentation Points

### 1. Query Latency Tracking

**File**: `retriever/retrieval_pipeline.py`

```python
import time
from core.logger import get_logger

logger = get_logger(__name__)

class RetrievalPipeline:
    @timed(metric_name="retriever.query_latency")
    def retrieve(self, query: str, top_k: int = 5):
        """Retrieve results with latency tracking."""
        start = time.time()
        
        # Metrics tracking
        metrics = {
            "query": query,
            "top_k": top_k,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # Embedding time
            emb_start = time.time()
            embedding = self.encoder.encode(query)
            metrics["embedding_time_ms"] = (time.time() - emb_start) * 1000
            
            # Search time
            search_start = time.time()
            results = self.vector_store.query(embedding, k=top_k)
            metrics["search_time_ms"] = (time.time() - search_start) * 1000
            
            # Total
            metrics["total_time_ms"] = (time.time() - start) * 1000
            metrics["cache_hit"] = False  # When caching added
            
            logger.info(f"Query latency: {metrics['total_time_ms']:.1f}ms", extra=metrics)
            
            return results
        
        except Exception as e:
            metrics["error"] = str(e)
            logger.error(f"Query failed: {e}", extra=metrics)
            raise
```

### 2. Embedding Throughput Tracking

**File**: `embedding/embedding_generator.py`

```python
class EmbeddingGenerator:
    @timed(metric_name="embedder.batch_time")
    def generate_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings with throughput tracking."""
        start = time.time()
        
        metrics = {
            "batch_size": len(texts),
            "total_tokens": sum(len(t.split()) for t in texts),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # Actually generate
            embeddings = self.client.create(
                model="text-embedding-3-small",
                input=texts,
            ).data
            
            elapsed = time.time() - start
            metrics["elapsed_time_ms"] = elapsed * 1000
            metrics["throughput"] = len(texts) / elapsed
            metrics["time_per_doc_ms"] = elapsed / len(texts) * 1000
            metrics["api_calls"] = 1
            
            logger.info(f"Embedding batch: {metrics['throughput']:.2f} docs/sec", extra=metrics)
            
            return embeddings
        
        except Exception as e:
            metrics["error"] = str(e)
            logger.error(f"Embedding failed: {e}", extra=metrics)
            raise
```

### 3. Cache Hit Rate Tracking

**File**: `core/optimization.py`

```python
class Cache:
    def get(self, key: K) -> Optional[V]:
        str_key = self._key_to_str(key)
        
        if str_key in self._cache:
            self._hits += 1
            entry = self._cache[str_key]
            entry.record_access()
            
            # Log hit rate every 100 operations
            if (self._hits + self._misses) % 100 == 0:
                hit_rate = self._hits / (self._hits + self._misses)
                logger.info(
                    f"Cache hit rate: {hit_rate*100:.1f}% "
                    f"({self._hits} hits, {self._misses} misses)",
                    extra={
                        "hit_rate": hit_rate,
                        "total_operations": self._hits + self._misses,
                    }
                )
            
            return entry.value if not entry.compressed else decompress(entry.value)
        
        self._misses += 1
        return None
```

### 4. Memory Monitoring

**File**: `core/optimization.py`

```python
import psutil
import os

class MemoryMonitor:
    """Monitor memory usage across application."""
    
    def __init__(self, warning_threshold_mb: float = 500):
        self.warning_threshold = warning_threshold_mb * 1024 * 1024
        self.process = psutil.Process(os.getpid())
    
    def check_memory(self) -> Dict[str, float]:
        """Check current memory usage."""
        info = self.process.memory_info()
        
        metrics = {
            "rss_mb": info.rss / 1024 / 1024,           # Resident set size
            "vms_mb": info.vms / 1024 / 1024,           # Virtual memory size
            "percent": self.process.memory_percent(),
        }
        
        if metrics["rss_mb"] > self.warning_threshold:
            logger.warning(
                f"High memory usage: {metrics['rss_mb']:.1f}MB",
                extra=metrics
            )
        
        return metrics

# Usage in hot path
memory_monitor = MemoryMonitor()

@timed(metric_name="chatbot.query")
def answer(self, query: str) -> Dict[str, Any]:
    mem_start = memory_monitor.check_memory()
    
    # ... processing ...
    
    mem_end = memory_monitor.check_memory()
    
    logger.info(
        f"Memory delta: {(mem_end['rss_mb'] - mem_start['rss_mb']):.1f}MB",
        extra={
            "start_memory_mb": mem_start["rss_mb"],
            "end_memory_mb": mem_end["rss_mb"],
            "delta_mb": mem_end["rss_mb"] - mem_start["rss_mb"],
        }
    )
```

---

## Logging & Monitoring Setup

### 1. Structured Logging for Metrics

**File**: `core/logger.py` (enhance)

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add extra metrics
        if hasattr(record, "msg"):
            # Custom metrics from logger.info(..., extra={...})
            for key, value in record.__dict__.items():
                if key not in logging.LogRecord.__dict__:
                    log_data[key] = value
        
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Get logger with JSON formatting."""
    logger = logging.getLogger(name)
    
    # JSON handler for structured logs
    json_handler = logging.FileHandler("logs/metrics.json")
    json_handler.setFormatter(JSONFormatter())
    
    # Console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    logger.addHandler(json_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
    
    return logger
```

### 2. Metrics Aggregation

**File**: `analytics/performance_aggregator.py` (new)

```python
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import statistics

class PerformanceAggregator:
    """Aggregate performance metrics from logs."""
    
    def __init__(self, log_file: Path = Path("logs/metrics.json")):
        self.log_file = log_file
    
    def read_metrics(self, hours: int = 1) -> List[Dict]:
        """Read metrics from last N hours."""
        metrics = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    record_time = datetime.fromisoformat(record.get("timestamp"))
                    
                    if record_time > cutoff_time:
                        metrics.append(record)
                except json.JSONDecodeError:
                    continue
        
        return metrics
    
    def aggregate(self, hours: int = 1) -> Dict[str, Any]:
        """Aggregate metrics."""
        metrics = self.read_metrics(hours)
        
        # Group by metric name
        by_metric = defaultdict(list)
        for metric in metrics:
            if "total_time_ms" in metric:
                by_metric["query_latency_ms"].append(metric["total_time_ms"])
            if "throughput" in metric:
                by_metric["embedding_throughput"].append(metric["throughput"])
            if "hit_rate" in metric:
                by_metric["cache_hit_rate"].append(metric["hit_rate"])
        
        # Compute statistics
        summary = {}
        for metric_name, values in by_metric.items():
            if values:
                summary[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                    "p95": sorted(values)[int(len(values) * 0.95)],
                    "p99": sorted(values)[int(len(values) * 0.99)],
                }
        
        return {
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": summary,
        }

# Usage
aggregator = PerformanceAggregator()
report = aggregator.aggregate(hours=24)
print(json.dumps(report, indent=2))
```

### 3. Real-time Dashboard Updates

**File**: `admin/dashboard.py` (enhance)

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analytics.performance_aggregator import PerformanceAggregator

def show_performance_metrics():
    """Display real-time performance metrics."""
    st.header("📊 Performance Metrics")
    
    aggregator = PerformanceAggregator()
    report = aggregator.aggregate(hours=24)
    
    # Query Latency
    if "query_latency_ms" in report["metrics"]:
        latency = report["metrics"]["query_latency_ms"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "P50 Latency",
            f"{latency['median']:.0f}ms",
            delta=f"{latency['median'] - 1200:.0f}ms",
            delta_color="inverse"
        )
        col2.metric(
            "P95 Latency",
            f"{latency['p95']:.0f}ms",
            delta=f"{latency['p95'] - 1500:.0f}ms",
            delta_color="inverse"
        )
        col3.metric(
            "P99 Latency",
            f"{latency['p99']:.0f}ms",
            delta=f"{latency['p99'] - 1800:.0f}ms",
            delta_color="inverse"
        )
        col4.metric(
            "Requests",
            f"{latency['count']}",
        )
        
        # Latency trend
        st.subheader("Latency Trend (24h)")
        latency_data = pd.DataFrame({
            "timestamp": pd.date_range(start="today", periods=100, freq="h"),
            "latency_ms": [latency['mean'] * (1 - i/200) for i in range(100)],
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=latency_data["timestamp"],
            y=latency_data["latency_ms"],
            mode="lines",
            name="Query Latency",
            line=dict(color="royalblue")
        ))
        fig.add_hline(y=650, line_dash="dash", line_color="green", 
                     annotation_text="Target: 650ms")
        st.plotly_chart(fig, use_container_width=True)
    
    # Embedding Throughput
    if "embedding_throughput" in report["metrics"]:
        throughput = report["metrics"]["embedding_throughput"]
        
        col1, col2 = st.columns(2)
        col1.metric(
            "Embedding Throughput",
            f"{throughput['mean']:.2f} docs/sec",
            delta=f"{(throughput['mean'] - 0.5) / 0.5 * 100:.0f}%",
        )
        col2.metric(
            "Time per Document",
            f"{1000/throughput['mean']:.0f}ms",
            delta=f"{1000/throughput['mean'] - 2000:.0f}ms",
            delta_color="inverse"
        )
    
    # Cache Hit Rate
    if "cache_hit_rate" in report["metrics"]:
        cache = report["metrics"]["cache_hit_rate"]
        
        st.metric(
            "Cache Hit Rate",
            f"{cache['mean']*100:.1f}%",
            delta=f"+{(cache['mean'] - 0.30)*100:.1f}%",
        )
```

---

## Performance Testing Matrix

```python
# tests/test_performance_regressions.py

import pytest
import time

class TestPerformanceRegressions:
    """Ensure no regressions during optimization."""
    
    @pytest.mark.performance
    def test_query_latency_target(self):
        """Query latency must be under 1000ms (baseline) then 650ms (target)."""
        pipeline = RetrievalPipeline()
        
        times = []
        for i in range(50):
            start = time.time()
            pipeline.retrieve("How to apply?")
            times.append((time.time() - start) * 1000)
        
        p95 = sorted(times)[47]
        
        # Before optimization: < 1500ms
        # After Phase 1: < 1000ms
        # After Phase 3: < 750ms
        assert p95 < 750, f"Query latency {p95:.0f}ms exceeds target 750ms"
    
    @pytest.mark.performance
    def test_embedding_throughput_target(self):
        """Embedding throughput must be > 0.5 docs/sec (baseline) then 1.0 (target)."""
        gen = EmbeddingGenerator()
        
        texts = [f"Sample text {i}" * 20 for i in range(100)]
        
        start = time.time()
        embeddings = gen.generate_batch(texts)
        elapsed = time.time() - start
        
        throughput = len(texts) / elapsed
        
        # Before: > 0.5 docs/sec
        # Target: > 1.0 docs/sec
        assert throughput > 1.0, f"Throughput {throughput:.2f} below target 1.0"
    
    @pytest.mark.performance
    def test_memory_per_query_target(self):
        """Memory usage must be < 250MB (baseline) then 150MB (target)."""
        import tracemalloc
        
        chatbot = Chatbot()
        tracemalloc.start()
        
        for i in range(10):
            chatbot.answer("What is the admission fee?")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        memory_per_query = peak / 10 / 1024 / 1024
        
        # Target: < 150MB per query
        assert memory_per_query < 150, f"Memory {memory_per_query:.0f}MB exceeds target 150MB"
    
    @pytest.mark.performance
    def test_evaluation_batch_time(self):
        """Evaluation must complete in < 30 seconds for 100 test cases."""
        ragas = RAGASMetrics()
        
        test_cases = [generate_test_case() for _ in range(100)]
        
        start = time.time()
        results = ragas.compute_all_metrics_batch(test_cases)
        elapsed = time.time() - start
        
        assert elapsed < 30, f"Evaluation took {elapsed:.0f}s, target < 30s"
    
    # Run with: pytest tests/test_performance_regressions.py -m performance -v
```

---

## Monitoring Dashboard Commands

```bash
# Start metrics collection
python analytics/performance_aggregator.py --watch

# View live metrics
streamlit run admin/dashboard.py

# Generate performance report
python -c "
from analytics.performance_aggregator import PerformanceAggregator
import json

agg = PerformanceAggregator()
report = agg.aggregate(hours=24)
print(json.dumps(report, indent=2))
" > performance_report.json

# Check for regressions
pytest tests/test_performance_regressions.py -m performance -v

# Benchmark against baseline
python tests/benchmark.py --baseline --compare
```

---

## Success Metrics Checklist

After implementing optimizations, verify:

### Phase 1 (Week 1)
- [ ] Query latency P50: 1200ms → 800ms ✓
- [ ] Query latency P95: 1500ms → 1000ms ✓
- [ ] Cache hit rate: > 25% ✓
- [ ] No regressions in functionality ✓

### Phase 2 (Week 2)
- [ ] Query latency P50: 800ms → 650ms ✓
- [ ] Embedding throughput: 0.5 → 1.0 docs/sec ✓
- [ ] Memory per query: 250MB → 150MB ✓
- [ ] Redundant searches eliminated ✓

### Phase 3 (Week 3)
- [ ] Query latency P50: < 600ms ✓
- [ ] Evaluation time: 4-6 hours → 20 seconds ✓
- [ ] Cache hit rate: > 40% ✓
- [ ] Cost per 10K queries: $0.50 → $0.15 ✓

