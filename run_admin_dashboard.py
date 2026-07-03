#!/usr/bin/env python3
"""
Run the admin dashboard with Streamlit.

Usage:
    streamlit run run_admin_dashboard.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the UI
from admin.admin_ui import main

if __name__ == "__main__":
    main()
