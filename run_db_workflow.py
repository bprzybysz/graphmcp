#!/usr/bin/env python3
"""
Simple Database Decommissioning Workflow Runner

This script runs the database decommissioning workflow using the cleaned-up
modular structure without the removed demo components.

Usage:
    python run_db_workflow.py --database postgres_air --repo https://github.com/bprzybysz/postgres-sample-dbs
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, '.')

from concrete.db_decommission import run_decommission


async def main():
    parser = argparse.ArgumentParser(description='Run database decommissioning workflow')
    parser.add_argument('--database', required=True, help='Database name to decommission')
    parser.add_argument('--repo', default='https://github.com/bprzybysz/postgres-sample-dbs', help='Target repository')
    parser.add_argument('--slack-channel', default='demo-channel', help='Slack channel for notifications')
    parser.add_argument('--mock', action='store_true', help='Use mock data from tests/data/ directory')
    
    args = parser.parse_args()
    
    # Check for cached mock data first
    if args.mock:
        # Check both tmp/<database-name>/ and tests/data/ for existing data
        tmp_repo_pack_path = Path(f"tmp/{args.database}/{args.database}_repo_pack.xml")
        tests_repo_pack_path = Path(f"tests/data/{args.database}_mock_repo_pack.xml")
        
        if tmp_repo_pack_path.exists():
            print(f"✅ Using cached repo pack: {tmp_repo_pack_path}")
        elif tests_repo_pack_path.exists():
            print(f"✅ Using cached mock repo pack: {tests_repo_pack_path}")
        else:
            print(f"⚠️  Mock data not found, falling back to real data")
            args.mock = False
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print(f"🚀 Starting decommission workflow for database: {args.database}")
    print(f"📦 Target repository: {args.repo}")
    print(f"💬 Slack channel: {args.slack_channel}")
    print("-" * 80)
    
    try:
        result = await run_decommission(
            database_name=args.database,
            target_repos=[args.repo],
            slack_channel=args.slack_channel,
            mock_mode=args.mock
        )
        
        print("\n" + "=" * 80)
        print("✅ Workflow completed successfully!")
        print(f"📊 Status: {result.status}")
        print(f"⏱️  Duration: {result.duration_seconds:.1f} seconds")
        print(f"📈 Success Rate: {result.success_rate:.1f}%")
        print(f"🔧 Steps Completed: {result.steps_completed}")
        print(f"❌ Steps Failed: {result.steps_failed}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Workflow failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))