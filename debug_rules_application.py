#!/usr/bin/env python3
"""
Debug script to test rule application for postgres_air database.
This will help us understand why only 4/18 files are being modified.
"""

import asyncio

from don_concrete.contextual_rules_engine import create_contextual_rules_engine
from don_concrete.source_type_classifier import SourceTypeClassifier


async def debug_rule_application():
    print("🔍 DEBUGGING RULE APPLICATION FOR POSTGRES_AIR")
    print("═══════════════════════════════════════════════════")

    # Initialize components
    engine = create_contextual_rules_engine()
    classifier = SourceTypeClassifier()
    database_name = "postgres_air"

    # Test files that should be found
    test_files = [
        {
            "path": "README.md",
            "content": """| [Postgres air](#postgres_air-database) | 10 | 67228600 | 1.2 GB |
            
CREATE DATABASE postgres_air;
            
psql -d "postgres://user:password@host/postgres_air" -f postgres_air.sql""",
        },
        {
            "path": "datadog_monitor_postgres_air.yaml",
            "content": """name: "postgres_air-database-connection-monitor"
tags:
  - "database:postgres_air"
query: max(last_30m):max:postgresql.connections.active{database:postgres_air} by {host}""",
        },
        {
            "path": "script_1.py",
            "content": '''# Create Terraform for postgres_air
postgres_air_config = """
resource "azurerm_postgresql_flexible_server" "postgres_air" {
  name = "psql-postgres_air-prod"
}"""
print("Contains: employees, lego, postgres_air databases")''',
        },
        {
            "path": "deploy_scenarios.sh",
            "content": """#!/bin/bash
for db in periodic_table world_happiness titanic pagila chinook netflix employees lego postgres_air; do
    echo "Processing database: $db"
    helm upgrade --install postgres_air helm-charts/postgres_air/
done""",
        },
        {
            "path": "terraform_prod_critical_databases.tf",
            "content": """resource "azurerm_postgresql_flexible_server" "postgres_air" {
  name = "psql-postgres_air-prod"
  database = "postgres_air"
}
output "postgres_air_connection_string" {
  value = "postgresql://postgres_air"
}""",
        },
    ]

    print("📊 TESTING FILE CLASSIFICATION AND RULE APPLICATION:")
    print()

    total_rules_found = 0
    total_changes_made = 0

    for file_info in test_files:
        file_path = file_info["path"]
        file_content = file_info["content"]

        print(f"📁 Testing: {file_path}")

        # 1. Test classification
        classification = classifier.classify_file(file_path, file_content)
        source_type = classification.source_type

        print(f"   🏷️  Source Type: {source_type.value}")
        print(f"   🎯 Confidence: {classification.confidence:.1f}")
        print(f"   🔧 Frameworks: {classification.detected_frameworks}")

        # 2. Test rule loading
        rules = engine._get_applicable_rules(
            source_type, classification.detected_frameworks
        )

        print(f"   📋 Rules Found: {len(rules)}")
        total_rules_found += len(rules)

        if rules:
            print(f"   📝 Available Rules:")
            for rule_id, rule_config in rules.items():
                print(f'     - {rule_id}: {rule_config.get("description", "")}')

        # 3. Test rule application
        try:
            result = await engine.process_file_with_contextual_rules(
                file_path,
                file_content,
                classification,
                database_name,
                None,
                "owner",
                "repo",
            )

            print(f"   ✅ Processing Success: {result.success}")
            print(f"   🔧 Changes Made: {result.total_changes}")
            total_changes_made += result.total_changes

            if result.rules_applied:
                for rule_result in result.rules_applied:
                    status = "✅" if rule_result.applied else "❌"
                    print(
                        f"     {status} {rule_result.rule_id}: {rule_result.changes_made} changes"
                    )
                    if hasattr(rule_result, "warnings") and rule_result.warnings:
                        print(f"       ⚠️  Warnings: {rule_result.warnings}")
                    if hasattr(rule_result, "errors") and rule_result.errors:
                        print(f"       ❌ Errors: {rule_result.errors}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

    print("📊 SUMMARY:")
    print(f"   📁 Files Tested: {len(test_files)}")
    print(f"   📋 Total Rules Found: {total_rules_found}")
    print(f"   🔧 Total Changes Made: {total_changes_made}")

    if total_changes_made == 0:
        print()
        print("🚨 PROBLEM: No changes made - investigating rule patterns...")

        # Debug rule patterns
        doc_rules = engine._load_documentation_rules()
        print("📝 Sample documentation rule patterns:")
        for rule_id, rule_config in doc_rules.items():
            patterns = rule_config.get("patterns", [])
            for pattern in patterns[:2]:  # Show first 2 patterns
                processed = pattern.replace("{{TARGET_DB}}", database_name)
                print(f"   Pattern: {processed}")

        # Test pattern matching manually
        print()
        print("🔍 MANUAL PATTERN MATCHING TEST:")
        test_content = (
            "| [Postgres air](#postgres_air-database) | 10 | 67228600 | 1.2 GB |"
        )
        test_pattern = r"#.*postgres_air.*"
        import re

        if re.search(test_pattern, test_content, re.IGNORECASE):
            print("   ✅ Pattern matches!")
        else:
            print("   ❌ Pattern does not match")
            print(f"   📝 Test content: {test_content}")
            print(f"   🔍 Test pattern: {test_pattern}")


if __name__ == "__main__":
    asyncio.run(debug_rule_application())
