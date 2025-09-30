#!/usr/bin/env python3
"""
Database Migration Runner
Runs database migrations as a separate process from the main application
"""

import sys
import logging
from migration_runner import MigrationRunner

def main():
    """Run database migrations"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('migration_run.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting database migration process")
    
    try:
        # Initialize migration runner
        runner = MigrationRunner(verbose=True)
        
        # Run pending migrations
        successful, failed = runner.run_pending_migrations()
        
        if failed > 0:
            logger.error(f"Migration failed: {failed} failed, {successful} successful")
            sys.exit(1)
        elif successful > 0:
            logger.info(f"Migration completed successfully: {successful} migrations applied")
        else:
            logger.info("No pending migrations found")
            
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
