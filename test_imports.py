#!/usr/bin/env python3
"""
Comprehensive import test to check all project modules.
"""

import sys
import traceback

tests = []

def test_module(module_name: str, items: list = None):
    """Test importing a module and its items."""
    try:
        if items:
            exec(f"from {module_name} import {', '.join(items)}")
            print(f"OK: {module_name} -> {', '.join(items)}")
            tests.append((module_name, True, None))
        else:
            exec(f"import {module_name}")
            print(f"OK: {module_name}")
            tests.append((module_name, True, None))
        return True
    except Exception as e:
        print(f"FAIL: {module_name} -> {str(e)}")
        tests.append((module_name, False, str(e)))
        return False

print("=" * 70)
print("COMPREHENSIVE PROJECT IMPORT TEST")
print("=" * 70)

# Core modules
print("\n[1/7] Testing core modules...")
test_module("config", ["Settings", "get_settings"])
test_module("core.logger", ["get_logger", "setup_logging"])
test_module("core.exceptions", [])
test_module("core.models", [])

# Crawler
print("\n[2/7] Testing crawler module...")
test_module("crawler.crawl", ["CrawlerOrchestrator"])
test_module("crawler.parser", [])
test_module("crawler.metadata", [])

# Ingestion
print("\n[3/7] Testing ingestion module...")
test_module("ingestion.chunk_processor", ["ChunkProcessor"])
test_module("ingestion.kb_generators", ["KBGenerator"])
test_module("ingestion.kb_loader", ["KBLoader"])

# Embedding
print("\n[4/7] Testing embedding module...")
test_module("embedding", ["EmbeddingGenerator", "EmbeddingOrchestrator"])

# Vectorstore
print("\n[5/7] Testing vectorstore module...")
test_module("vectorstore", [])
test_module("vectorstore.vectorstore", ["VectorStore"])

# Retriever
print("\n[6/7] Testing retriever module...")
test_module("retriever", [])
test_module("retriever.retrieval_pipeline", ["RetrievalPipeline"])

# Chatbot & Security
print("\n[7/7] Testing chatbot and security...")
test_module("security", ["SecurityManager"])
try:
    from chatbot.chatbot import Chatbot
    print("OK: chatbot.chatbot -> Chatbot")
    tests.append(("chatbot.chatbot", True, None))
except Exception as e:
    print(f"FAIL: chatbot.chatbot -> {str(e)}")
    traceback.print_exc()
    tests.append(("chatbot.chatbot", False, str(e)))

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

passed = sum(1 for _, success, _ in tests if success)
failed = sum(1 for _, success, _ in tests if not success)

print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")

if failed > 0:
    print("\nFailed imports:")
    for name, success, error in tests:
        if not success:
            print(f"  - {name}: {error}")
    sys.exit(1)
else:
    print("\nAll imports successful!")
    sys.exit(0)
