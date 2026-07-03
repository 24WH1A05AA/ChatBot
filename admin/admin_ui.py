"""
Streamlit Admin Dashboard UI

Professional interface for system monitoring and administration.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path

from admin.dashboard import AdminDashboard, AdminMetricsCollector


def configure_page():
    """Configure Streamlit page."""
    st.set_page_config(
        page_title="Admin Dashboard | College FAQ Chatbot",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            margin: 10px 0;
        }
        .metric-title {
            font-size: 14px;
            opacity: 0.9;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-subtext {
            font-size: 12px;
            opacity: 0.8;
        }
        .status-healthy { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-error { color: #e74c3c; }
    </style>
    """, unsafe_allow_html=True)


def display_health_status(health: dict):
    """Display system health status."""
    st.subheader("🏥 System Health")
    
    cols = st.columns(4)
    components = [
        ("Crawling", health.get("crawling", "unknown")),
        ("Embeddings", health.get("embeddings", "unknown")),
        ("Queries", health.get("queries", "unknown")),
        ("Vector DB", health.get("vector_db", "unknown")),
    ]
    
    status_colors = {
        "healthy": "🟢",
        "warning": "🟡",
        "error": "🔴",
        "unknown": "⚪",
    }
    
    for i, (name, status) in enumerate(components):
        with cols[i]:
            icon = status_colors.get(status, "⚪")
            st.metric(name, icon + " " + status.upper())


def display_crawling_metrics(metrics: dict):
    """Display crawling metrics and charts."""
    st.subheader("📡 Crawling Statistics")
    
    crawl_data = metrics.get("crawling", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pages", crawl_data.get("total_pages", 0))
    with col2:
        st.metric("Successful", crawl_data.get("successful", 0))
    with col3:
        st.metric("Failed", crawl_data.get("failed", 0))
    with col4:
        success_rate = crawl_data.get("success_rate", 0)
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Domain breakdown
    by_domain = crawl_data.get("by_domain", {})
    if by_domain:
        st.write("**Pages by Domain:**")
        domain_df = pd.DataFrame(
            list(by_domain.items()),
            columns=["Domain", "Count"]
        ).sort_values("Count", ascending=False)
        
        fig = px.pie(
            domain_df,
            values="Count",
            names="Domain",
            title="Crawled Pages by Domain"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent errors
    errors = crawl_data.get("errors", [])
    if errors:
        st.write("**Recent Crawl Errors:**")
        error_df = pd.DataFrame(errors).tail(10)
        st.dataframe(error_df, use_container_width=True)


def display_chunking_metrics(metrics: dict):
    """Display chunking metrics."""
    st.subheader("📚 Chunking Statistics")
    
    chunk_data = metrics.get("chunking", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Chunks", chunk_data.get("total_chunks", 0))
    with col2:
        avg_size = chunk_data.get("avg_size_bytes", 0)
        st.metric("Avg Size", f"{avg_size/1024:.1f} KB")
    with col3:
        min_size = chunk_data.get("min_size", 0)
        st.metric("Min Size", f"{min_size/1024:.1f} KB")
    with col4:
        max_size = chunk_data.get("max_size", 0)
        st.metric("Max Size", f"{max_size/1024:.1f} KB")
    
    # Chunks by type
    by_type = chunk_data.get("by_type", {})
    if by_type:
        type_df = pd.DataFrame(
            list(by_type.items()),
            columns=["Type", "Count"]
        )
        
        fig = px.bar(
            type_df,
            x="Type",
            y="Count",
            title="Chunks by Type"
        )
        st.plotly_chart(fig, use_container_width=True)


def display_embedding_metrics(metrics: dict):
    """Display embedding metrics."""
    st.subheader("🧠 Embedding Statistics")
    
    embed_data = metrics.get("embeddings", {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total", embed_data.get("total", 0))
    with col2:
        st.metric("Successful", embed_data.get("successful", 0))
    with col3:
        st.metric("Failed", embed_data.get("failed", 0))
    with col4:
        success_rate = embed_data.get("success_rate", 0)
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col5:
        latency = embed_data.get("avg_latency_ms", 0)
        st.metric("Avg Latency", f"{latency:.0f}ms")
    
    # Recent errors
    errors = embed_data.get("errors", [])
    if errors:
        st.write("**Recent Embedding Errors:**")
        error_df = pd.DataFrame(errors).tail(10)
        st.dataframe(error_df, use_container_width=True)


def display_query_metrics(metrics: dict):
    """Display query metrics."""
    st.subheader("❓ Query Statistics")
    
    query_data = metrics.get("queries", {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Queries", query_data.get("total", 0))
    with col2:
        st.metric("Successful", query_data.get("successful", 0))
    with col3:
        st.metric("Failed", query_data.get("failed", 0))
    with col4:
        success_rate = query_data.get("success_rate", 0)
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col5:
        latency = query_data.get("avg_latency_ms", 0)
        st.metric("Avg Latency", f"{latency:.0f}ms")
    
    # Queries by category
    by_category = query_data.get("by_category", {})
    if by_category:
        cat_df = pd.DataFrame(
            list(by_category.items()),
            columns=["Category", "Count"]
        ).sort_values("Count", ascending=False)
        
        fig = px.bar(
            cat_df,
            x="Category",
            y="Count",
            title="Queries by Category"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent errors
    errors = query_data.get("errors", [])
    if errors:
        st.write("**Recent Query Errors:**")
        error_df = pd.DataFrame(errors).tail(10)
        st.dataframe(error_df, use_container_width=True)


def display_vector_db_metrics(metrics: dict):
    """Display vector database metrics."""
    st.subheader("🗄️ Vector Database Statistics")
    
    vdb_data = metrics.get("vector_db", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        size = vdb_data.get("size_mb", 0)
        st.metric("Database Size", f"{size:.1f} MB")
    with col2:
        docs = vdb_data.get("documents", 0)
        st.metric("Documents", f"{docs:,}")
    with col3:
        cols = vdb_data.get("collections", 0)
        st.metric("Collections", cols)
    with col4:
        status = vdb_data.get("status", "unknown")
        st.metric("Status", status.upper())


def display_kb_metrics(metrics: dict):
    """Display knowledge base metrics."""
    st.subheader("📖 Knowledge Base Statistics")
    
    kb_data = metrics.get("knowledge_base", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        docs = kb_data.get("total_documents", 0)
        st.metric("Total Documents", f"{docs:,}")
    with col2:
        size = kb_data.get("total_size_mb", 0)
        st.metric("Total Size", f"{size:.1f} MB")
    with col3:
        last_update = kb_data.get("last_update", "Never")
        st.metric("Last Update", last_update.split("T")[0] if "T" in str(last_update) else last_update)
    
    # Documents by category
    by_category = kb_data.get("by_category", {})
    if by_category:
        cat_df = pd.DataFrame(
            list(by_category.items()),
            columns=["Category", "Count"]
        ).sort_values("Count", ascending=False)
        
        fig = px.bar(
            cat_df,
            x="Category",
            y="Count",
            title="Knowledge Base by Category"
        )
        st.plotly_chart(fig, use_container_width=True)


def display_error_summary(metrics: dict):
    """Display error summary."""
    st.subheader("🚨 Error Summary")
    
    # Calculate total errors
    errors = []
    
    crawl_errors = metrics.get("crawling", {}).get("errors", [])
    errors.extend([(e.get("message", "Unknown"), "Crawling") for e in crawl_errors])
    
    embed_errors = metrics.get("embeddings", {}).get("errors", [])
    errors.extend([(e.get("message", "Unknown"), "Embedding") for e in embed_errors])
    
    query_errors = metrics.get("queries", {}).get("errors", [])
    errors.extend([(e.get("message", "Unknown"), "Query") for e in query_errors])
    
    st.write(f"**Total Errors: {len(errors)}**")
    
    if errors:
        error_df = pd.DataFrame(
            errors[:20],
            columns=["Error Message", "Component"]
        )
        st.dataframe(error_df, use_container_width=True)


def display_system_logs(logs: list):
    """Display system logs."""
    st.subheader("📋 System Logs")
    
    if not logs:
        st.info("No logs available yet")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.multiselect(
            "Filter by Level",
            options=["info", "warning", "error", "debug"],
            default=["info", "warning", "error"]
        )
    
    with col2:
        component = st.multiselect(
            "Filter by Component",
            options=set(log["component"] for log in logs if "component" in log),
        )
    
    # Filter logs
    filtered_logs = [
        log for log in logs
        if (log.get("level", "info") in log_level) and
           (not component or log.get("component", "") in component)
    ]
    
    if filtered_logs:
        log_df = pd.DataFrame(filtered_logs[:100])
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No logs match the selected filters")


def main():
    """Main dashboard function."""
    configure_page()
    
    st.title("⚙️ Admin Dashboard")
    st.markdown("**College FAQ Chatbot System Monitoring**")
    
    # Initialize dashboard
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = AdminDashboard()
        
        # Load sample data (in production, this would be loaded from actual system)
        st.session_state.dashboard.collector.update_crawling_metrics(
            pages_crawled=1250,
            successful=1180,
            failed=70,
            by_domain={
                "example.com": 800,
                "api.example.com": 250,
                "docs.example.com": 180,
            },
            errors=[
                {"domain": "example.com", "error": "Timeout", "timestamp": datetime.utcnow().isoformat()},
            ]
        )
        
        st.session_state.dashboard.collector.update_chunking_metrics(
            total_chunks=5240,
            sizes=[500, 1000, 2000, 3000, 1500],
            by_type={
                "text": 3500,
                "json": 1200,
                "html": 540,
            }
        )
        
        st.session_state.dashboard.collector.update_embedding_metrics(
            total=5240,
            successful=5180,
            failed=60,
            latencies=[45.2, 48.5, 42.1, 50.3, 46.7],
            errors=[
                {"chunk_id": "123", "error": "API error", "timestamp": datetime.utcnow().isoformat()},
            ]
        )
        
        st.session_state.dashboard.collector.update_query_metrics(
            total=8523,
            successful=8250,
            failed=273,
            latencies=[350.5, 400.2, 320.1, 450.3, 380.7],
            by_category={
                "admission": 2500,
                "facilities": 1800,
                "academics": 2200,
                "fees": 1520,
                "other": 503,
            },
            errors=[
                {"query": "unknown", "error": "No context", "timestamp": datetime.utcnow().isoformat()},
            ]
        )
        
        st.session_state.dashboard.collector.update_vector_db_metrics(
            size_mb=285.5,
            documents=5240,
            collections=8,
            status="healthy",
        )
        
        st.session_state.dashboard.collector.update_kb_metrics(
            total_documents=1250,
            total_size_mb=45.2,
            by_category={
                "admission": 250,
                "academics": 350,
                "facilities": 200,
                "fees": 150,
                "other": 300,
            },
            last_update=datetime.utcnow().isoformat(),
        )
    
    dashboard = st.session_state.dashboard
    
    # Get metrics
    dashboard.collector.update_system_metrics()
    metrics = dashboard.collector.get_summary()
    health = dashboard.collector.get_health_status()
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Overview",
        "Crawling",
        "Chunking",
        "Embeddings",
        "Queries",
        "Vector DB",
        "Knowledge Base",
        "Logs"
    ])
    
    with tab1:
        display_health_status(health)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Uptime", f"{metrics['system']['uptime_hours']:.1f} hours")
        with col2:
            st.metric("Total Errors", len(metrics['system']['errors']))
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Pages Crawled", metrics['crawling']['total_pages'])
        with col2:
            st.metric("Total Chunks", metrics['chunking']['total_chunks'])
        with col3:
            st.metric("Embeddings", metrics['embeddings']['total'])
        with col4:
            st.metric("Queries", metrics['queries']['total'])
    
    with tab2:
        display_crawling_metrics(metrics)
    
    with tab3:
        display_chunking_metrics(metrics)
    
    with tab4:
        display_embedding_metrics(metrics)
    
    with tab5:
        display_query_metrics(metrics)
    
    with tab6:
        display_vector_db_metrics(metrics)
    
    with tab7:
        display_kb_metrics(metrics)
    
    with tab8:
        display_system_logs(dashboard.logs)
    
    # Export options
    st.sidebar.subheader("📥 Export")
    
    if st.sidebar.button("Export Dashboard Data"):
        export_path = "admin_dashboard_export.json"
        dashboard.export_dashboard(export_path)
        st.sidebar.success(f"Exported to {export_path}")


if __name__ == "__main__":
    main()
