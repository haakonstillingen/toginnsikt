#!/usr/bin/env python3
"""
Migration Management CLI Tool
Provides comprehensive migration management capabilities
"""

import argparse
import sys
from datetime import datetime
from migration_runner import MigrationRunner

class MigrationManager:
    """CLI tool for managing database migrations"""
    
    def __init__(self):
        self.runner = MigrationRunner(verbose=True)
    
    def status(self):
        """Show migration status"""
        print("🔍 Migration Status")
        print("=" * 50)
        
        status = self.runner.get_migration_status()
        
        print(f"Total migrations: {status['total_migrations']}")
        print(f"Applied migrations: {status['applied_migrations']}")
        print(f"Pending migrations: {status['pending_migrations']}")
        print()
        
        if status['migrations']:
            print("Migration Details:")
            print("-" * 50)
            
            for migration in status['migrations']:
                status_icon = "✅" if migration['applied'] else "⏳"
                rollback_icon = "🔄" if migration['has_rollback'] else "❌"
                
                applied_at = ""
                if migration['applied_at']:
                    applied_at = f" (applied: {migration['applied_at'].strftime('%Y-%m-%d %H:%M:%S')})"
                
                print(f"{status_icon} {migration['version']:>6} | {migration['description']:<30} | Rollback: {rollback_icon}{applied_at}")
        else:
            print("No migrations found")
    
    def migrate(self, dry_run=False):
        """Run pending migrations"""
        if dry_run:
            print("🔍 Dry Run - Pending Migrations")
            print("=" * 50)
            
            status = self.runner.get_migration_status()
            pending = [m for m in status['migrations'] if not m['applied']]
            
            if not pending:
                print("No pending migrations found")
                return
            
            print(f"Would execute {len(pending)} pending migrations:")
            for migration in pending:
                print(f"  - {migration['version']}: {migration['description']}")
            return
        
        print("🚀 Running Pending Migrations")
        print("=" * 50)
        
        successful, failed = self.runner.run_pending_migrations()
        
        if failed > 0:
            print(f"❌ Migration failed: {failed} failed, {successful} successful")
            sys.exit(1)
        elif successful > 0:
            print(f"✅ Migration completed: {successful} migrations applied")
        else:
            print("ℹ️  No pending migrations found")
    
    def rollback(self, version, confirm=False):
        """Rollback a specific migration"""
        if not confirm:
            print(f"⚠️  WARNING: This will rollback migration {version}")
            print("This action may result in data loss!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Rollback cancelled")
                return
        
        print(f"🔄 Rolling back migration {version}")
        print("=" * 50)
        
        if self.runner.rollback_migration(version):
            print(f"✅ Migration {version} rolled back successfully")
        else:
            print(f"❌ Failed to rollback migration {version}")
            sys.exit(1)
    
    def create_migration(self, name, description=""):
        """Create a new migration file"""
        import re
        from pathlib import Path
        
        # Get next version number
        migrations = self.runner.discover_migrations()
        if migrations:
            last_version = max(int(m.version[:3]) for m in migrations)
            next_version = f"{last_version + 1:03d}"
        else:
            next_version = "001"
        
        # Clean up name for filename
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        filename = f"{next_version}_{clean_name}.sql"
        filepath = Path("migrations") / filename
        
        # Create migration file
        migration_content = f"""-- Migration {next_version}: {name}
-- {description}

-- Add your migration SQL here
-- Example:
-- CREATE TABLE example_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(100) NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- Create indexes if needed
-- CREATE INDEX IF NOT EXISTS idx_example_name ON example_table(name);

-- Add comments for documentation
-- COMMENT ON TABLE example_table IS 'Example table for migration template';
"""
        
        with open(filepath, 'w') as f:
            f.write(migration_content)
        
        # Create rollback file
        rollback_filename = f"{next_version}_{clean_name}_rollback.sql"
        rollback_filepath = Path("migrations") / rollback_filename
        
        rollback_content = f"""-- Rollback script for migration {next_version}_{clean_name}.sql
-- WARNING: This will permanently delete data

-- Add your rollback SQL here
-- Example:
-- DROP TABLE IF EXISTS example_table;
"""
        
        with open(rollback_filepath, 'w') as f:
            f.write(rollback_content)
        
        print(f"✅ Created migration files:")
        print(f"   Migration: {filepath}")
        print(f"   Rollback:  {rollback_filepath}")
        print()
        print("Next steps:")
        print("1. Edit the migration file with your SQL")
        print("2. Edit the rollback file with your rollback SQL")
        print("3. Test the migration with: python migration_manager.py migrate --dry-run")
        print("4. Apply the migration with: python migration_manager.py migrate")
    
    def validate(self):
        """Validate migration integrity"""
        print("🔍 Validating Migration Integrity")
        print("=" * 50)
        
        all_migrations = self.runner.discover_migrations()
        applied_migrations = self.runner.get_applied_migrations()
        
        issues_found = False
        
        for migration in all_migrations:
            if migration.version in applied_migrations:
                stored_checksum = applied_migrations[migration.version].get('checksum', '')
                if stored_checksum and stored_checksum != migration.checksum:
                    print(f"❌ {migration.version}: File has been modified since application")
                    print(f"   Stored checksum: {stored_checksum}")
                    print(f"   Current checksum: {migration.checksum}")
                    issues_found = True
                else:
                    print(f"✅ {migration.version}: Integrity check passed")
            else:
                print(f"⏳ {migration.version}: Not yet applied")
        
        if not issues_found:
            print("\n✅ All applied migrations passed integrity check")
        else:
            print("\n❌ Migration integrity issues found!")
            sys.exit(1)
    
    def history(self):
        """Show migration history"""
        print("📜 Migration History")
        print("=" * 50)
        
        applied_migrations = self.runner.get_applied_migrations()
        
        if not applied_migrations:
            print("No migrations have been applied yet")
            return
        
        # Sort by applied_at
        sorted_migrations = sorted(
            applied_migrations.values(),
            key=lambda x: x['applied_at']
        )
        
        for migration in sorted_migrations:
            applied_at = migration['applied_at'].strftime('%Y-%m-%d %H:%M:%S')
            print(f"{migration['version']:>6} | {migration['description']:<30} | {applied_at}")

def main():
    parser = argparse.ArgumentParser(
        description='Database Migration Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migration_manager.py status                    # Show migration status
  python migration_manager.py migrate                  # Run pending migrations
  python migration_manager.py migrate --dry-run        # Preview pending migrations
  python migration_manager.py rollback 003             # Rollback migration 003
  python migration_manager.py create "add_users_table" # Create new migration
  python migration_manager.py validate                 # Validate migration integrity
  python migration_manager.py history                  # Show migration history
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show migration status')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run pending migrations')
    migrate_parser.add_argument('--dry-run', action='store_true', help='Preview pending migrations without executing')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback a specific migration')
    rollback_parser.add_argument('version', help='Migration version to rollback')
    rollback_parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('name', help='Migration name (e.g., "add_users_table")')
    create_parser.add_argument('--description', help='Migration description', default='')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate migration integrity')
    
    # History command
    subparsers.add_parser('history', help='Show migration history')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = MigrationManager()
    
    try:
        if args.command == 'status':
            manager.status()
        elif args.command == 'migrate':
            manager.migrate(dry_run=args.dry_run)
        elif args.command == 'rollback':
            manager.rollback(args.version, confirm=args.yes)
        elif args.command == 'create':
            manager.create_migration(args.name, args.description)
        elif args.command == 'validate':
            manager.validate()
        elif args.command == 'history':
            manager.history()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
