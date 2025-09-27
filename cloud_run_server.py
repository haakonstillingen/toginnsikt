#!/usr/bin/env python3
"""
Cloud Run HTTP Server for Enhanced Commute Collector
Provides health check endpoint for Cloud Run while running the collector in background
"""

import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from collection_scheduler import CollectionScheduler

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler for Cloud Run"""
    
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "togforsinkelse-enhanced-collector",
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/collect':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Trigger collection in background and return immediate response
            threading.Thread(target=self.trigger_collection, daemon=True).start()
            
            response = {
                "status": "collection_triggered",
                "message": "Actual departure collection started",
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def trigger_collection(self):
        """Trigger the actual departure collection process"""
        try:
            from enhanced_commute_collector_cloud import EnhancedCommuteCollectorCloud
            collector = EnhancedCommuteCollectorCloud(verbose=True)
            
            # Run actual departure collection
            collector.collect_actual_departures()
            
            logging.info("Collection triggered successfully via /collect endpoint")
        except Exception as e:
            logging.error(f"Collection error in /collect endpoint: {e}")
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_collector():
    """Run the collection scheduler in background thread"""
    try:
        collector = CollectionScheduler(verbose=True)
        collector.run()
    except Exception as e:
        logging.error(f"Collector error: {e}")

def run_http_server():
    """Run HTTP server for Cloud Run health checks"""
    server = HTTPServer(('', 8080), HealthCheckHandler)
    logging.info("HTTP server starting on port 8080")
    server.serve_forever()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Start collector in background thread
    collector_thread = threading.Thread(target=run_collector, daemon=True)
    collector_thread.start()
    
    # Start HTTP server in main thread
    run_http_server()
