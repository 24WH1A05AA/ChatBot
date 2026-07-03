"""
Streamlit chat interface for the college FAQ chatbot.

Displays chat, sources, metrics, and conversation history.
"""

import streamlit as st
import asyncio
from pathlib import Path
from datetime import datetime

from chatbot.chatbot import Chatbot
from vectorstore.vectorstore import VectorStore
from config import get_settings
from core.logger import get_logger

logger = get_logger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "chatbot" not in st.session_state:
        settings = get_settings()
        
        # Initialize vector store
        vectorstore = VectorStore(
            collection_name="college_faq",
            persist_dir=Path(settings.PERSIST_DIRECTORY) / "vectorstore",
        )
        
        # Initialize chatbot
        st.session_state.chatbot = Chatbot(
            vectorstore=vectorstore,
            llm_model="gpt-4o-mini",
            max_conversation_history=20,
            retrieval_k=5,
            temperature=0.0,
        )
    
    if "messages" not in st.session_state:
        st.session_state.messages = []


def display_message(role: str, content: str, metadata: dict = None):
    """Display a chat message."""
    with st.chat_message(role):
        st.markdown(content)
        
        if metadata:
            if "sources" in metadata and metadata["sources"]:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(metadata["sources"], 1):
                        st.markdown(f"**{i}. {source.get('section', 'Unknown')}**")
                        if source.get("url"):
                            st.markdown(f"   🔗 [{source['url']}]({source['url']})")
                        if source.get("similarity_score"):
                            st.markdown(f"   📊 Relevance: {source['similarity_score']:.0%}")
            
            if "retrieved_chunks" in metadata:
                with st.expander(f"📖 Retrieved Context ({len(metadata['retrieved_chunks'])} chunks)"):
                    for i, chunk in enumerate(metadata["retrieved_chunks"], 1):
                        st.markdown(f"**Chunk {i}: {chunk.get('heading', 'Section')}**")
                        st.markdown(f"```\n{chunk.get('text', '')[:300]}...\n```")
                        st.caption(f"📍 {chunk.get('section')} | 📎 {chunk.get('source_url')}")


def display_metrics(metrics: dict):
    """Display metrics in columns."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Queries", metrics.get("total_queries", 0))
    
    with col2:
        avg_latency = metrics.get("avg_latency_ms", 0)
        st.metric("Avg Latency", f"{avg_latency:.0f}ms")
    
    with col3:
        total_tokens = metrics.get("total_tokens", 0)
        st.metric("Total Tokens", total_tokens)
    
    with col4:
        avg_retrieval = metrics.get("avg_retrieval_ms", 0)
        st.metric("Retrieval Time", f"{avg_retrieval:.0f}ms")


def main():
    """Main Streamlit app."""
    
    # Page configuration
    st.set_page_config(
        page_title="College FAQ Chatbot",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Custom CSS
    st.markdown("""
        <style>
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
            }
            .source-badge {
                background-color: #d9e8f9;
                padding: 0.5rem 1rem;
                border-radius: 0.25rem;
                margin: 0.25rem 0;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🎓 College FAQ Chatbot")
    st.markdown("*Ask me anything about the college - admissions, academics, campus life, and more.*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Filters
        st.subheader("Search Filters")
        section = st.selectbox(
            "Filter by Section",
            ["All", "Admissions", "Academics", "Campus", "Placements", "Student Life"],
            key="section_filter",
        )
        
        department = st.selectbox(
            "Filter by Department",
            ["All", "Computer Science", "Electronics", "Mechanical", "Civil"],
            key="dept_filter",
        )
        
        retrieval_k = st.slider(
            "Number of Sources",
            min_value=1,
            max_value=10,
            value=5,
            key="retrieval_k",
        )
        
        # Update chatbot settings
        st.session_state.chatbot.retrieval_k = retrieval_k
        
        st.divider()
        
        # Display metrics
        st.subheader("📊 Metrics")
        metrics = st.session_state.chatbot.get_metrics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries", metrics.get("total_queries", 0))
        with col2:
            st.metric("Tokens", metrics.get("total_tokens", 0))
        
        avg_latency = metrics.get("avg_latency_ms", 0)
        st.metric("Avg Latency", f"{avg_latency:.0f}ms")
        
        # Response type distribution
        if metrics.get("response_type_distribution"):
            st.subheader("Response Types")
            response_dist = metrics.get("response_type_distribution", {})
            st.bar_chart(response_dist)
        
        st.divider()
        
        # Controls
        st.subheader("🎮 Controls")
        
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.chatbot.clear_conversation()
            st.session_state.messages = []
            st.success("Conversation cleared!")
            st.rerun()
        
        if st.button("💾 Export Conversation", use_container_width=True):
            export_path = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            st.session_state.chatbot.export_conversation(export_path)
            st.success(f"Exported to {export_path}")
    
    # Main chat area
    st.subheader("💬 Chat")
    
    # Display conversation history
    for msg in st.session_state.chatbot.get_conversation_history():
        role = "user" if msg["role"] == "user" else "assistant"
        content = msg["content"]
        metadata = msg.get("metadata", {})
        display_message(role, content, metadata)
    
    # Chat input
    st.divider()
    
    if prompt := st.chat_input("Ask me about the college..."):
        # Add user message
        display_message("user", prompt)
        
        # Process query
        with st.spinner("Processing your question..."):
            try:
                # Determine filters
                section_filter = None if section == "All" else section
                dept_filter = None if department == "All" else department
                
                # Run async chat
                loop = asyncio.new_event_loop()
                response = loop.run_until_complete(
                    st.session_state.chatbot.chat(
                        query=prompt,
                        section=section_filter,
                        department=dept_filter,
                    )
                )
                loop.close()
                
                # Display response
                if response["success"]:
                    metadata = {
                        "sources": response.get("sources", []),
                        "retrieved_chunks": response.get("retrieved_chunks", []),
                    }
                    display_message("assistant", response["response"], metadata)
                    
                    # Display metrics
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    
                    metrics_data = response.get("metrics", {})
                    with col1:
                        st.metric(
                            "Total Latency",
                            f"{metrics_data.get('total_latency_ms', 0):.0f}ms",
                        )
                    with col2:
                        st.metric(
                            "Retrieval Time",
                            f"{metrics_data.get('retrieval_ms', 0):.0f}ms",
                        )
                    with col3:
                        st.metric(
                            "Tokens Used",
                            metrics_data.get("tokens_used", 0),
                        )
                else:
                    st.error(response["response"])
            
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                logger.error(f"Error in chat interface: {e}", exc_info=True)
    
    # Footer
    st.divider()
    st.caption(
        "🎓 College FAQ Chatbot | Powered by GPT-4o Mini | "
        "Retrieved context • Always cited • Hallucination-free"
    )


if __name__ == "__main__":
    main()
