#!/usr/bin/env python3
"""
Simple runner for database decommission workflow.
"""

import asyncio
import sys
import logging

# Add current directory to path
sys.path.insert(0, '.')

from concrete.db_decommission import run_decommission

async def main():
    """Run the database decommission workflow."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 Starting Database Decommission Workflow")
    print("=" * 50)
    
    try:
        result = await run_decommission('postgres_air')
        print(f"\n✅ Workflow completed!")
        if hasattr(result, 'status'):
            print(f"Status: {result.status}")
        return result
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())