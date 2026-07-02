"""
Streamlit dashboard for the College FAQ Chatbot.

Provides web-based interface for:
- Chatbot interaction
- Document management
- Performance metrics
- Configuration management
"""

import streamlit as st


def main():
    """Main dashboard entry point."""
    st.set_page_config(
        page_title="College FAQ Chatbot",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🎓 College FAQ Chatbot")
    st.write("A production-ready RAG chatbot for college information.")


if __name__ == "__main__":
    main()
