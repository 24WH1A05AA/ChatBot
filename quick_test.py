#!/usr/bin/env python3
"""Quick import test with error details."""

import sys
import traceback

try:
    print("Testing chunk_processor...")
    from ingestion.chunk_processor import IntelligentChunker
    print("OK: IntelligentChunker")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

try:
    print("\nTesting kb_generators...")
    from ingestion.kb_generators import JSONKnowledgeBaseGenerator
    print("OK: JSONKnowledgeBaseGenerator")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

try:
    print("\nTesting kb_loader...")
    from ingestion.kb_loader import DocumentLoader
    print("OK: DocumentLoader")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

try:
    print("\nTesting embedding...")
    from embedding.embedding_generator import OpenAIEmbeddingGenerator
    print("OK: OpenAIEmbeddingGenerator")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

try:
    print("\nTesting full dashboard import...")
    from streamlit_ui.dashboard import main
    print("OK: Dashboard imports successfully")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

print("\n✓ Test complete")
