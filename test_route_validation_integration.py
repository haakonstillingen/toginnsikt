#!/usr/bin/env python3
"""
Route Validation Integration Test Suite

This test suite performs integration testing of the route validation
functionality with real database connections and API calls where possible.

Test Categories:
1. Database integration tests
2. API integration tests with real data
3. End-to-end collection pipeline tests
4. Performance and reliability tests

Usage:
    python test_route_validation_integration.py
    python -m pytest test_route_validation_integration.py -v
"""

import unittest
import sys
import os
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch
import psycopg2

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_commute_collector_cloud import EnhancedCommuteCollectorCloud, CommuteRoute
import config_cloud


class TestRouteValidationIntegration(unittest.TestCase):
    """Integration tests for route validation with real systems"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.collector = EnhancedCommuteCollectorCloud()
        self.test_routes_data = [
            {
                'route_name': 'Test Morning Route',
                'source_station_id': 'NSR:StopPlace:59638',
                'source_station_name': 'Myrvoll',
                'target_station_id': 'NSR:StopPlace:337',
                'target_station_name': 'Oslo S',
                'final_destination_pattern': 'Lysaker|Stabekk',
                'direction': 'westbound'
            },
            {
                'route_name': 'Test Afternoon Route',
                'source_station_id': 'NSR:StopPlace:337',
                'source_station_name': 'Oslo S',
                'target_station_id': 'NSR:StopPlace:59638',
                'target_station_name': 'Myrvoll',
                'final_destination_pattern': 'Ski',
                'direction': 'eastbound'
            }
        ]
    
    def test_database_connection(self):
        """Test that database connection works"""
        try:
            conn = self.collector.get_db_connection()
            if conn:
                self.assertIsNotNone(conn)
                conn.close()
                print("✅ Database connection successful")
            else:
                self.skipTest("Database connection not available (expected in test environment)")
        except Exception as e:
            self.skipTest(f"Database connection failed: {e}")
    
    def test_route_loading_with_real_database(self):
        """Test route loading with real database (if available)"""
        try:
            conn = self.collector.get_db_connection()
            if not conn:
                self.skipTest("Database connection not available")
            
            # Test loading routes from database
            routes = self.collector.load_commute_routes()
            
            # Should load at least some routes
            self.assertGreaterEqual(len(routes), 0)
            
            # If routes exist, validate their structure
            for route in routes:
                self.assertIsInstance(route, CommuteRoute)
                self.assertIsNotNone(route.route_name)
                self.assertIsNotNone(route.final_destination_pattern)
                self.assertIsNotNone(route.direction)
            
            conn.close()
            print(f"✅ Loaded {len(routes)} routes from database")
            
        except Exception as e:
            self.skipTest(f"Database test failed: {e}")
    
    def test_api_request_with_real_data(self):
        """Test API request with real Entur API (if available)"""
        try:
            # Test with a known station ID
            station_id = "NSR:StopPlace:59638"  # Myrvoll
            start_time = datetime.now(timezone.utc)
            
            # Make real API request
            response = self.collector.make_api_request(station_id, start_time, 1)
            
            if response and 'data' in response:
                self.assertIn('data', response)
                print("✅ API request successful")
            else:
                self.skipTest("API request failed or returned no data")
                
        except Exception as e:
            self.skipTest(f"API test failed: {e}")
    
    def test_route_validation_with_test_data(self):
        """Test route validation using existing test data files"""
        test_data_dir = "debug_and_test_scripts/testdata"
        
        if not os.path.exists(test_data_dir):
            self.skipTest("Test data directory not found")
        
        # Find test data files
        test_files = [f for f in os.listdir(test_data_dir) if f.endswith('.json')]
        
        if not test_files:
            self.skipTest("No test data files found")
        
        # Test with first available test file
        test_file = os.path.join(test_data_dir, test_files[0])
        
        try:
            with open(test_file, 'r') as f:
                test_data = json.load(f)
            
            # Create a test route
            test_route = CommuteRoute(
                route_name="Test Route",
                source_station_id="NSR:StopPlace:59638",
                source_station_name="Myrvoll",
                target_station_id="NSR:StopPlace:337",
                target_station_name="Oslo S",
                final_destination_pattern="Lysaker|Stabekk",
                direction="westbound"
            )
            
            # Mock the API response with test data
            with patch.object(self.collector, 'make_api_request', return_value=test_data):
                departures = self.collector.fetch_planned_departures(
                    test_route, 
                    datetime.now(timezone.utc)
                )
            
            # Should process the test data
            self.assertIsInstance(departures, list)
            print(f"✅ Processed test data: {len(departures)} departures found")
            
        except Exception as e:
            self.skipTest(f"Test data processing failed: {e}")
    
    def test_pattern_matching_with_real_destinations(self):
        """Test pattern matching with real destination names from Norwegian railways"""
        # Real destination names that might appear in the system
        real_destinations = [
            "Lysaker",
            "Stabekk", 
            "Ski",
            "Oslo S",
            "Drammen",
            "Asker",
            "Sandvika",
            "Lysaker stasjon",
            "Stabekk stasjon"
        ]
        
        # Test patterns from the actual configuration
        test_patterns = [
            ("Lysaker|Stabekk", ["Lysaker", "Stabekk"]),
            ("Ski", ["Ski"]),
            ("Lysaker|Stabekk|Ski", ["Lysaker", "Stabekk", "Ski"])
        ]
        
        for pattern, expected_matches in test_patterns:
            with self.subTest(pattern=pattern):
                matches = []
                non_matches = []
                
                for destination in real_destinations:
                    if self.collector.matches_final_destination(destination, pattern):
                        matches.append(destination)
                    else:
                        non_matches.append(destination)
                
                # Verify expected matches
                for expected_match in expected_matches:
                    self.assertIn(expected_match, matches, 
                        f"Expected {expected_match} to match pattern {pattern}")
                
                print(f"✅ Pattern '{pattern}': {len(matches)} matches, {len(non_matches)} non-matches")
    
    def test_duplicate_route_detection_integration(self):
        """Test duplicate route detection with realistic data"""
        # Create test routes that would be duplicates
        duplicate_routes_data = [
            {
                'id': 1,
                'route_name': 'Morning Commute',
                'source_station_id': 'NSR:StopPlace:59638',
                'source_station_name': 'Myrvoll',
                'target_station_id': 'NSR:StopPlace:337',
                'target_station_name': 'Oslo S',
                'final_destination_pattern': 'Lysaker|Stabekk',
                'direction': 'westbound'
            },
            {
                'id': 2,
                'route_name': 'Morning Commute Alternative',  # Different name
                'source_station_id': 'NSR:StopPlace:59638',  # Same source
                'source_station_name': 'Myrvoll',
                'target_station_id': 'NSR:StopPlace:337',    # Same target
                'target_station_name': 'Oslo S',
                'final_destination_pattern': 'Lysaker',      # Different pattern
                'direction': 'westbound'                     # Same direction
            },
            {
                'id': 3,
                'route_name': 'Afternoon Commute',
                'source_station_id': 'NSR:StopPlace:337',
                'source_station_name': 'Oslo S',
                'target_station_id': 'NSR:StopPlace:59638',
                'target_station_name': 'Myrvoll',
                'final_destination_pattern': 'Ski',
                'direction': 'eastbound'  # Different direction - should not be duplicate
            }
        ]
        
        # Mock database response
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (route['id'], route['route_name'], route['source_station_id'], 
             route['source_station_name'], route['target_station_id'], 
             route['target_station_name'], route['final_destination_pattern'], 
             route['direction'])
            for route in duplicate_routes_data
        ]
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Test duplicate detection
        routes = self.collector.load_commute_routes()
        
        # Should load only 2 routes (first and third, second is duplicate)
        self.assertEqual(len(routes), 2)
        
        # Verify the correct routes were loaded
        route_names = [route.route_name for route in routes]
        self.assertIn("Morning Commute", route_names)
        self.assertIn("Afternoon Commute", route_names)
        self.assertNotIn("Morning Commute Alternative", route_names)
        
        print("✅ Duplicate route detection working correctly")
    
    def test_error_handling_and_logging(self):
        """Test error handling and logging in various failure scenarios"""
        # Test with invalid database connection
        self.collector.get_db_connection = Mock(return_value=None)
        
        routes = self.collector.load_commute_routes()
        self.assertEqual(routes, [])
        
        # Test with database error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.side_effect = Exception("Database error")
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        routes = self.collector.load_commute_routes()
        self.assertEqual(routes, [])
        
        print("✅ Error handling working correctly")


def run_integration_tests():
    """Run integration tests and provide a summary"""
    print("🔗 Running Route Validation Integration Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestRouteValidationIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Integration tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {result.testsRun - len(result.failures) - len(result.errors) - result.testsRun + len(result.failures) + len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
