#!/usr/bin/env python
"""
Wrapper script to run Streamlit dashboard from the correct directory.
This ensures all imports work correctly.
"""
import os
import sys
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent
os.chdir(project_root)

# Add project root to Python path
sys.path.insert(0, str(project_root))

# Now import and run streamlit
import streamlit.web.cli as stcli

# Run the dashboard
sys.argv = [
    "streamlit",
    "run",
    str(project_root / "streamlit_ui" / "dashboard.py"),
    "--logger.level=info",
]

sys.exit(stcli.main())
