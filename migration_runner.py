#!/usr/bin/env python3
"""
Database Migration Runner
Handles versioned database migrations with rollback capabilities
"""

import os
import hashlib
import logging
import psycopg2
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re
from migration_config import *

@dataclass
class MigrationInfo:
    """Information about a migration file"""
    version: str
    filename: str
    filepath: str
    checksum: str
    description: str
    rollback_script: Optional[str] = None

class MigrationRunner:
    """Handles database migration execution and rollback"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.migrations_dir = Path("migrations")
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.INFO if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('migration_runner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_db_connection(self):
        """Get PostgreSQL database connection"""
        try:
            if CLOUD_SQL_CONNECTION_NAME:
                # Use Cloud SQL connector
                conn = psycopg2.connect(
                    host=f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}',
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME
                )
            else:
                # Direct connection
                conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
            return conn
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
    
    def discover_migrations(self) -> List[MigrationInfo]:
        """Discover all migration files in the migrations directory"""
        migrations = []
        
        if not self.migrations_dir.exists():
            self.logger.error(f"Migrations directory not found: {self.migrations_dir}")
            return migrations
            
        # Find all SQL files matching migration pattern (exclude rollback files)
        pattern = re.compile(r'^(\d{3}[a-z]?)_(.+)\.sql$')
        
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            # Skip rollback files
            if file_path.name.endswith('_rollback.sql'):
                continue
                
            match = pattern.match(file_path.name)
            if not match:
                self.logger.warning(f"Skipping non-migration file: {file_path.name}")
                continue
                
            version = match.group(1)
            description = match.group(2).replace('_', ' ').title()
            
            # Calculate file checksum
            checksum = self.calculate_checksum(file_path)
            
            # Look for rollback script
            rollback_script = self.find_rollback_script(file_path)
            
            migrations.append(MigrationInfo(
                version=version,
                filename=file_path.name,
                filepath=str(file_path),
                checksum=checksum,
                description=description,
                rollback_script=rollback_script
            ))
            
        return migrations
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def find_rollback_script(self, migration_file: Path) -> Optional[str]:
        """Look for rollback script (e.g., 001_rollback.sql)"""
        rollback_file = migration_file.parent / f"{migration_file.stem}_rollback.sql"
        if rollback_file.exists():
            try:
                with open(rollback_file, 'r') as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Failed to read rollback script {rollback_file}: {e}")
        return None
    
    def get_applied_migrations(self) -> Dict[str, Dict]:
        """Get list of applied migrations from database"""
        conn = self.get_db_connection()
        if not conn:
            return {}
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT version, filename, applied_at, checksum, description
                FROM schema_migrations
                ORDER BY version
            """)
            
            applied = {}
            for row in cursor.fetchall():
                applied[row[0]] = {
                    'version': row[0],
                    'filename': row[1],
                    'applied_at': row[2],
                    'checksum': row[3],
                    'description': row[4]
                }
            
            return applied
        except Exception as e:
            self.logger.error(f"Failed to get applied migrations: {e}")
            return {}
        finally:
            conn.close()
    
    def validate_migration_integrity(self, migration: MigrationInfo, applied_info: Dict) -> bool:
        """Validate that migration file hasn't been modified since application"""
        if migration.version not in applied_info:
            return True  # New migration, no validation needed
            
        stored_checksum = applied_info[migration.version].get('checksum', '')
        if stored_checksum and stored_checksum != migration.checksum:
            self.logger.error(f"Migration {migration.version} has been modified since application!")
            self.logger.error(f"Stored checksum: {stored_checksum}")
            self.logger.error(f"Current checksum: {migration.checksum}")
            return False
            
        return True
    
    def execute_migration(self, migration: MigrationInfo) -> bool:
        """Execute a single migration"""
        conn = self.get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        try:
            self.logger.info(f"Executing migration {migration.version}: {migration.description}")
            
            # Read migration file
            with open(migration.filepath, 'r') as f:
                migration_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            # Record migration in tracking table
            cursor.execute("""
                INSERT INTO schema_migrations 
                (version, filename, checksum, rollback_script, description)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (version) DO UPDATE SET
                    checksum = EXCLUDED.checksum,
                    rollback_script = EXCLUDED.rollback_script,
                    description = EXCLUDED.description
            """, (
                migration.version,
                migration.filename,
                migration.checksum,
                migration.rollback_script,
                migration.description
            ))
            
            conn.commit()
            self.logger.info(f"Migration {migration.version} executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration {migration.version} failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        conn = self.get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        try:
            # Get migration info
            cursor.execute("""
                SELECT version, filename, rollback_script, description
                FROM schema_migrations
                WHERE version = %s
            """, (version,))
            
            result = cursor.fetchone()
            if not result:
                self.logger.error(f"Migration {version} not found in tracking table")
                return False
                
            version, filename, rollback_script, description = result
            
            if not rollback_script:
                self.logger.error(f"No rollback script available for migration {version}")
                return False
            
            self.logger.info(f"Rolling back migration {version}: {description}")
            
            # Execute rollback script
            statements = [stmt.strip() for stmt in rollback_script.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            # Remove from tracking table
            cursor.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
            
            conn.commit()
            self.logger.info(f"Migration {version} rolled back successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback of migration {version} failed: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def run_pending_migrations(self) -> Tuple[int, int]:
        """Run all pending migrations"""
        self.logger.info("Checking for pending migrations...")
        
        # Discover all migrations
        all_migrations = self.discover_migrations()
        if not all_migrations:
            self.logger.warning("No migration files found")
            return 0, 0
        
        # Get applied migrations
        applied_migrations = self.get_applied_migrations()
        
        # Find pending migrations
        pending_migrations = []
        for migration in all_migrations:
            if migration.version not in applied_migrations:
                pending_migrations.append(migration)
            else:
                # Validate integrity of applied migration
                if not self.validate_migration_integrity(migration, applied_migrations):
                    self.logger.error(f"Migration integrity check failed for {migration.version}")
                    return 0, 0
        
        if not pending_migrations:
            self.logger.info("No pending migrations found")
            return 0, 0
        
        self.logger.info(f"Found {len(pending_migrations)} pending migrations")
        
        # Execute pending migrations
        successful = 0
        failed = 0
        
        for migration in pending_migrations:
            if self.execute_migration(migration):
                successful += 1
            else:
                failed += 1
                break  # Stop on first failure
        
        return successful, failed
    
    def get_migration_status(self) -> Dict:
        """Get current migration status"""
        all_migrations = self.discover_migrations()
        applied_migrations = self.get_applied_migrations()
        
        status = {
            'total_migrations': len(all_migrations),
            'applied_migrations': len(applied_migrations),
            'pending_migrations': 0,
            'migrations': []
        }
        
        for migration in all_migrations:
            is_applied = migration.version in applied_migrations
            status['migrations'].append({
                'version': migration.version,
                'filename': migration.filename,
                'description': migration.description,
                'applied': is_applied,
                'applied_at': applied_migrations.get(migration.version, {}).get('applied_at'),
                'has_rollback': migration.rollback_script is not None
            })
            
            if not is_applied:
                status['pending_migrations'] += 1
        
        return status

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--status', action='store_true', help='Show migration status')
    parser.add_argument('--migrate', action='store_true', help='Run pending migrations')
    parser.add_argument('--rollback', type=str, help='Rollback specific migration version')
    
    args = parser.parse_args()
    
    runner = MigrationRunner(verbose=args.verbose)
    
    if args.status:
        status = runner.get_migration_status()
        print(f"Migration Status:")
        print(f"  Total migrations: {status['total_migrations']}")
        print(f"  Applied migrations: {status['applied_migrations']}")
        print(f"  Pending migrations: {status['pending_migrations']}")
        print()
        
        for migration in status['migrations']:
            status_str = "✓" if migration['applied'] else "○"
            rollback_str = " (rollback available)" if migration['has_rollback'] else ""
            print(f"  {status_str} {migration['version']}: {migration['description']}{rollback_str}")
    
    elif args.migrate:
        successful, failed = runner.run_pending_migrations()
        if failed > 0:
            print(f"Migration failed: {failed} failed, {successful} successful")
            exit(1)
        else:
            print(f"Migration completed: {successful} migrations applied")
    
    elif args.rollback:
        if runner.rollback_migration(args.rollback):
            print(f"Migration {args.rollback} rolled back successfully")
        else:
            print(f"Failed to rollback migration {args.rollback}")
            exit(1)
    
    else:
        parser.print_help()
