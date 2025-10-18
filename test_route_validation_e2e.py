#!/usr/bin/env python3
"""
Route Validation End-to-End Test Suite

This test suite performs end-to-end testing of the route validation
functionality by simulating the complete collection pipeline with
various scenarios including edge cases and error conditions.

Test Scenarios:
1. Normal collection with valid routes
2. Collection with routes having empty patterns
3. Collection with duplicate routes
4. Collection with mixed valid/invalid routes
5. Error recovery and logging verification

Usage:
    python test_route_validation_e2e.py
    python -m pytest test_route_validation_e2e.py -v
"""

import unittest
import sys
import os
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_commute_collector_cloud import EnhancedCommuteCollectorCloud, CommuteRoute, CollectionStatus


class TestRouteValidationE2E(unittest.TestCase):
    """End-to-end tests for route validation in collection pipeline"""
    
    def setUp(self):
        """Set up E2E test fixtures"""
        self.collector = EnhancedCommuteCollectorCloud()
        
        # Set up logging to capture log messages
        self.log_capture = []
        self.original_logger = self.collector.logger
        
        # Create a mock logger that captures messages
        self.mock_logger = Mock()
        self.mock_logger.info = Mock(side_effect=lambda msg: self.log_capture.append(('INFO', msg)))
        self.mock_logger.warning = Mock(side_effect=lambda msg: self.log_capture.append(('WARNING', msg)))
        self.mock_logger.error = Mock(side_effect=lambda msg: self.log_capture.append(('ERROR', msg)))
        self.mock_logger.debug = Mock(side_effect=lambda msg: self.log_capture.append(('DEBUG', msg)))
        
        self.collector.logger = self.mock_logger
    
    def tearDown(self):
        """Clean up after each test"""
        self.collector.logger = self.original_logger
        self.log_capture.clear()
    
    def create_mock_api_response(self, departures_data):
        """Create a mock API response with the given departure data"""
        return {
            'data': {
                'stopPlace': {
                    'estimatedCalls': departures_data
                }
            }
        }
    
    def test_e2e_valid_routes_collection(self):
        """Test end-to-end collection with valid routes"""
        # Mock database with valid routes
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "Morning Route", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Lysaker|Stabekk", "westbound"),
            (2, "Afternoon Route", "NSR:StopPlace:337", "Oslo S", 
             "NSR:StopPlace:59638", "Myrvoll", "Ski", "eastbound")
        ]
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Mock API responses for both routes
        morning_api_response = self.create_mock_api_response([
            {
                'serviceJourney': {'line': {'publicCode': 'L2'}, 'id': 'journey1'},
                'aimedDepartureTime': '2025-01-15T08:00:00Z',
                'destinationDisplay': {'frontText': 'Lysaker'}
            },
            {
                'serviceJourney': {'line': {'publicCode': 'L2'}, 'id': 'journey2'},
                'aimedDepartureTime': '2025-01-15T08:15:00Z',
                'destinationDisplay': {'frontText': 'Ski'}  # Should be filtered out
            }
        ])
        
        afternoon_api_response = self.create_mock_api_response([
            {
                'serviceJourney': {'line': {'publicCode': 'L2'}, 'id': 'journey3'},
                'aimedDepartureTime': '2025-01-15T17:00:00Z',
                'destinationDisplay': {'frontText': 'Ski'}
            },
            {
                'serviceJourney': {'line': {'publicCode': 'L2'}, 'id': 'journey4'},
                'aimedDepartureTime': '2025-01-15T17:15:00Z',
                'destinationDisplay': {'frontText': 'Lysaker'}  # Should be filtered out
            }
        ])
        
        # Mock API calls to return different responses based on station
        def mock_api_request(station_id, start_time, hours_ahead):
            if station_id == "NSR:StopPlace:59638":  # Myrvoll
                return morning_api_response
            elif station_id == "NSR:StopPlace:337":  # Oslo S
                return afternoon_api_response
            return None
        
        with patch.object(self.collector, 'make_api_request', side_effect=mock_api_request):
            # Load routes
            routes = self.collector.load_commute_routes()
            
            # Should load both routes
            self.assertEqual(len(routes), 2)
            
            # Test collection for each route
            all_departures = []
            for route in routes:
                departures = self.collector.fetch_planned_departures(route, datetime.now(timezone.utc))
                all_departures.extend(departures)
            
            # Should collect 2 departures total (1 from each route)
            self.assertEqual(len(all_departures), 2)
            
            # Verify correct filtering
            destinations = [dep.final_destination for dep in all_departures]
            self.assertIn("Lysaker", destinations)
            self.assertIn("Ski", destinations)
            self.assertNotIn("Ski", [dep.final_destination for dep in all_departures if "Lysaker" in destinations])
            
            print("✅ E2E test: Valid routes collection successful")
    
    def test_e2e_empty_pattern_routes_handling(self):
        """Test E2E collection with routes having empty patterns"""
        # Mock database with mixed valid/invalid routes
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "Valid Route", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Lysaker|Stabekk", "westbound"),
            (2, "Invalid Route", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "", "westbound"),  # Empty pattern
            (3, "Another Valid Route", "NSR:StopPlace:337", "Oslo S", 
             "NSR:StopPlace:59638", "Myrvoll", "Ski", "eastbound")
        ]
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Load routes
        routes = self.collector.load_commute_routes()
        
        # Should only load 2 routes (empty pattern route skipped)
        self.assertEqual(len(routes), 2)
        
        # Verify warning was logged for empty pattern
        warning_logs = [msg for level, msg in self.log_capture if level == 'WARNING']
        empty_pattern_warning = any("Missing or empty final_destination_pattern" in msg for msg in warning_logs)
        self.assertTrue(empty_pattern_warning, "Should log warning for empty pattern route")
        
        print("✅ E2E test: Empty pattern routes handled correctly")
    
    def test_e2e_duplicate_routes_handling(self):
        """Test E2E collection with duplicate routes"""
        # Mock database with duplicate routes
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "Route 1", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Lysaker|Stabekk", "westbound"),
            (2, "Route 2", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Lysaker", "westbound"),  # Duplicate
            (3, "Route 3", "NSR:StopPlace:337", "Oslo S", 
             "NSR:StopPlace:59638", "Myrvoll", "Ski", "eastbound")
        ]
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Load routes
        routes = self.collector.load_commute_routes()
        
        # Should only load 2 routes (duplicate skipped)
        self.assertEqual(len(routes), 2)
        
        # Verify warning was logged for duplicate
        warning_logs = [msg for level, msg in self.log_capture if level == 'WARNING']
        duplicate_warning = any("duplicate route" in msg.lower() for msg in warning_logs)
        self.assertTrue(duplicate_warning, "Should log warning for duplicate route")
        
        print("✅ E2E test: Duplicate routes handled correctly")
    
    def test_e2e_mixed_scenarios(self):
        """Test E2E collection with mixed valid/invalid/duplicate routes"""
        # Mock database with complex scenario
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "Valid Route 1", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Lysaker|Stabekk", "westbound"),
            (2, "Empty Pattern Route", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "", "westbound"),  # Should be skipped
            (3, "Duplicate Route", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Lysaker", "westbound"),  # Should be skipped
            (4, "Valid Route 2", "NSR:StopPlace:337", "Oslo S", 
             "NSR:StopPlace:59638", "Myrvoll", "Ski", "eastbound"),
            (5, "Another Empty Pattern", "NSR:StopPlace:337", "Oslo S", 
             "NSR:StopPlace:59638", "Myrvoll", "   ", "eastbound"),  # Whitespace only - should be skipped
        ]
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Load routes
        routes = self.collector.load_commute_routes()
        
        # Should only load 2 valid routes
        self.assertEqual(len(routes), 2)
        
        # Verify correct routes were loaded
        route_names = [route.route_name for route in routes]
        self.assertIn("Valid Route 1", route_names)
        self.assertIn("Valid Route 2", route_names)
        self.assertNotIn("Empty Pattern Route", route_names)
        self.assertNotIn("Duplicate Route", route_names)
        self.assertNotIn("Another Empty Pattern", route_names)
        
        # Verify appropriate warnings were logged
        warning_logs = [msg for level, msg in self.log_capture if level == 'WARNING']
        empty_pattern_warnings = sum(1 for msg in warning_logs if "Missing or empty final_destination_pattern" in msg)
        duplicate_warnings = sum(1 for msg in warning_logs if "duplicate route" in msg.lower())
        
        self.assertEqual(empty_pattern_warnings, 2, "Should log 2 empty pattern warnings")
        self.assertEqual(duplicate_warnings, 1, "Should log 1 duplicate warning")
        
        print("✅ E2E test: Mixed scenarios handled correctly")
    
    def test_e2e_error_recovery(self):
        """Test E2E error recovery and logging"""
        # Test database connection failure
        self.collector.get_db_connection = Mock(return_value=None)
        
        routes = self.collector.load_commute_routes()
        self.assertEqual(routes, [])
        
        # Test database error
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.side_effect = Exception("Database connection lost")
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        routes = self.collector.load_commute_routes()
        self.assertEqual(routes, [])
        
        # Test API error during collection
        valid_route = CommuteRoute(
            route_name="Test Route",
            source_station_id="NSR:StopPlace:59638",
            source_station_name="Myrvoll",
            target_station_id="NSR:StopPlace:337",
            target_station_name="Oslo S",
            final_destination_pattern="Lysaker|Stabekk",
            direction="westbound"
        )
        
        with patch.object(self.collector, 'make_api_request', side_effect=Exception("API error")):
            departures = self.collector.fetch_planned_departures(valid_route, datetime.now(timezone.utc))
            self.assertEqual(departures, [])
        
        print("✅ E2E test: Error recovery working correctly")
    
    def test_e2e_performance_and_reliability(self):
        """Test E2E performance and reliability with multiple routes"""
        # Mock database with multiple routes
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Create 10 test routes
        routes_data = []
        for i in range(10):
            routes_data.append((
                i + 1, f"Route {i + 1}", f"NSR:StopPlace:{59638 + i}", f"Station {i + 1}",
                f"NSR:StopPlace:{337 + i}", f"Target {i + 1}", "Lysaker|Stabekk", "westbound"
            ))
        
        mock_cursor.fetchall.return_value = routes_data
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Mock API responses
        def mock_api_request(station_id, start_time, hours_ahead):
            return self.create_mock_api_response([
                {
                    'serviceJourney': {'line': {'publicCode': 'L2'}, 'id': f'journey_{station_id}'},
                    'aimedDepartureTime': '2025-01-15T08:00:00Z',
                    'destinationDisplay': {'frontText': 'Lysaker'}
                }
            ])
        
        with patch.object(self.collector, 'make_api_request', side_effect=mock_api_request):
            # Load routes
            routes = self.collector.load_commute_routes()
            self.assertEqual(len(routes), 10)
            
            # Test collection for all routes
            start_time = datetime.now(timezone.utc)
            all_departures = []
            
            for route in routes:
                departures = self.collector.fetch_planned_departures(route, start_time)
                all_departures.extend(departures)
            
            # Should collect 10 departures (1 per route)
            self.assertEqual(len(all_departures), 10)
            
            # Verify all departures are valid
            for dep in all_departures:
                self.assertEqual(dep.final_destination, "Lysaker")
                self.assertEqual(dep.collection_status, CollectionStatus.PENDING)
        
        print("✅ E2E test: Performance and reliability verified")


def run_e2e_tests():
    """Run end-to-end tests and provide a summary"""
    print("🚀 Running Route Validation End-to-End Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestRouteValidationE2E))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"E2E tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
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
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
