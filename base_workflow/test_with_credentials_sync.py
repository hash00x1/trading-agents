#!/usr/bin/env python3
"""
Synchronous wrapper for Binance Integration Tests with Credentials

This script wraps the async test functions for use with Poetry scripts.
"""

import sys
import asyncio
from pathlib import Path

# Ensure we're using the right module paths for Poetry
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
	"""Synchronous main function that runs the async tests."""
	from base_workflow.test_with_credentials import main as async_main

	try:
		# Run the async main function
		success = asyncio.run(async_main())
		return success
	except Exception as e:
		print(f'❌ Test execution failed: {e}')
		return False


if __name__ == '__main__':
	success = main()
	sys.exit(0 if success else 1)
