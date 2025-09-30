#!/usr/bin/env python3
"""
Test script for the migration system
Tests various scenarios including rollback and edge cases
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from migration_runner import MigrationRunner
from migration_manager import MigrationManager

def test_migration_discovery():
    """Test migration file discovery"""
    print("🔍 Testing migration discovery...")
    
    runner = MigrationRunner(verbose=True)
    migrations = runner.discover_migrations()
    
    print(f"Found {len(migrations)} migration files:")
    for migration in migrations:
        print(f"  - {migration.version}: {migration.description}")
        print(f"    File: {migration.filename}")
        print(f"    Checksum: {migration.checksum[:16]}...")
        print(f"    Has rollback: {migration.rollback_script is not None}")
        print()
    
    return len(migrations) > 0

def test_migration_status():
    """Test migration status checking"""
    print("📊 Testing migration status...")
    
    manager = MigrationManager()
    status = manager.runner.get_migration_status()
    
    print(f"Total migrations: {status['total_migrations']}")
    print(f"Applied migrations: {status['applied_migrations']}")
    print(f"Pending migrations: {status['pending_migrations']}")
    print()
    
    for migration in status['migrations']:
        status_icon = "✅" if migration['applied'] else "⏳"
        print(f"{status_icon} {migration['version']}: {migration['description']}")
    
    return True

def test_migration_validation():
    """Test migration integrity validation"""
    print("🔒 Testing migration validation...")
    
    manager = MigrationManager()
    
    try:
        manager.validate()
        print("✅ Migration validation passed")
        return True
    except SystemExit:
        print("❌ Migration validation failed")
        return False

def test_dry_run():
    """Test dry run functionality"""
    print("🔍 Testing dry run...")
    
    manager = MigrationManager()
    manager.migrate(dry_run=True)
    
    print("✅ Dry run completed")
    return True

def test_migration_creation():
    """Test creating a new migration"""
    print("📝 Testing migration creation...")
    
    manager = MigrationManager()
    
    # Create a test migration
    test_name = "test_migration_creation"
    manager.create_migration(test_name, "Test migration for validation")
    
    # Check if files were created
    migration_file = Path("migrations") / "010_test_migration_creation.sql"
    rollback_file = Path("migrations") / "010_test_migration_creation_rollback.sql"
    
    if migration_file.exists() and rollback_file.exists():
        print("✅ Migration files created successfully")
        
        # Clean up test files
        migration_file.unlink()
        rollback_file.unlink()
        print("🧹 Test files cleaned up")
        return True
    else:
        print("❌ Migration files not created")
        return False

def test_rollback_simulation():
    """Test rollback functionality (simulation)"""
    print("🔄 Testing rollback simulation...")
    
    runner = MigrationRunner(verbose=True)
    
    # Get applied migrations
    applied = runner.get_applied_migrations()
    
    if not applied:
        print("ℹ️  No applied migrations found for rollback test")
        return True
    
    # Test rollback for the first applied migration
    first_version = list(applied.keys())[0]
    print(f"Testing rollback for migration {first_version}")
    
    # Note: We won't actually execute the rollback in tests
    # Just verify the rollback script exists
    migrations = runner.discover_migrations()
    target_migration = next((m for m in migrations if m.version == first_version), None)
    
    if target_migration and target_migration.rollback_script:
        print(f"✅ Rollback script found for migration {first_version}")
        return True
    else:
        print(f"❌ No rollback script found for migration {first_version}")
        return False

def test_error_handling():
    """Test error handling scenarios"""
    print("⚠️  Testing error handling...")
    
    # Test with invalid database connection
    original_config = None
    try:
        # Temporarily break the database configuration
        import config_cloud
        original_config = config_cloud.DB_HOST
        config_cloud.DB_HOST = "invalid_host"
        
        runner = MigrationRunner(verbose=True)
        conn = runner.get_db_connection()
        
        if conn is None:
            print("✅ Error handling works - invalid connection rejected")
            return True
        else:
            print("❌ Error handling failed - invalid connection accepted")
            return False
            
    except Exception as e:
        print(f"✅ Error handling works - exception caught: {e}")
        return True
    finally:
        # Restore original configuration
        if original_config is not None:
            config_cloud.DB_HOST = original_config

def run_all_tests():
    """Run all migration system tests"""
    print("🧪 Running Migration System Tests")
    print("=" * 50)
    
    tests = [
        ("Migration Discovery", test_migration_discovery),
        ("Migration Status", test_migration_status),
        ("Migration Validation", test_migration_validation),
        ("Dry Run", test_dry_run),
        ("Migration Creation", test_migration_creation),
        ("Rollback Simulation", test_rollback_simulation),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
