#!/usr/bin/env python3
"""
Collection Scheduler
Implements the two-tier collection system:
1. Daily planned departure collection at 03:00 UTC
2. Continuous actual departure collection with adaptive scheduling
"""

import schedule
import time
import logging
from datetime import datetime, timezone
from enhanced_commute_collector_cloud import EnhancedCommuteCollectorCloud

class CollectionScheduler:
    """Schedules and manages the two-tier collection system"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.collector = EnhancedCommuteCollectorCloud(verbose=verbose)
        
        # Setup logging
        self.setup_logging()
        
        # Setup scheduled jobs
        self.setup_schedule()
        
    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.INFO if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('collection_scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_schedule(self):
        """Setup scheduled collection jobs"""
        # Daily planned departure collection at 03:00 UTC
        schedule.every().day.at("03:00").do(self.run_planned_collection)
        
        # Continuous actual departure collection
        schedule.every(15).minutes.do(self.run_actual_collection)
        
        self.logger.info("Collection schedule configured:")
        self.logger.info("- Planned departures: Daily at 03:00 UTC")
        self.logger.info("- Actual departures: Every 15 minutes")
        
    def run_planned_collection(self):
        """Run planned departure collection"""
        self.logger.info("Starting scheduled planned departure collection")
        try:
            self.collector.collect_planned_departures_daily()
            self.logger.info("Planned departure collection completed successfully")
        except Exception as e:
            self.logger.error(f"Planned departure collection failed: {e}")
            
    def run_actual_collection(self):
        """Run actual departure collection"""
        self.logger.info("Starting scheduled actual departure collection")
        try:
            self.collector.collect_actual_departures()
            self.logger.info("Actual departure collection completed successfully")
        except Exception as e:
            self.logger.error(f"Actual departure collection failed: {e}")
            
    def run(self):
        """Run the scheduler"""
        self.logger.info("Starting collection scheduler")
        
        # Run initial planned collection if it's close to 03:00 UTC
        now = datetime.now(timezone.utc)
        if now.hour == 2:  # Run if it's 02:00 UTC (1 hour before scheduled time)
            self.logger.info("Running initial planned departure collection")
            self.run_planned_collection()
            
        # Run initial actual collection
        self.logger.info("Running initial actual departure collection")
        self.run_actual_collection()
        
        # Main scheduling loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Stopping collection scheduler")
                break
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Collection Scheduler')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--planned-only', action='store_true', help='Run only planned departure collection')
    parser.add_argument('--actual-only', action='store_true', help='Run only actual departure collection')
    
    args = parser.parse_args()
    
    scheduler = CollectionScheduler(verbose=args.verbose)
    
    try:
        if args.planned_only:
            scheduler.run_planned_collection()
        elif args.actual_only:
            scheduler.run_actual_collection()
        else:
            scheduler.run()
    finally:
        pass
