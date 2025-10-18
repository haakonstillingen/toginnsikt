#!/usr/bin/env python3
"""
Comprehensive Route Validation Test Suite

This test suite validates the route pattern validation functionality
introduced in PR #30. It tests all aspects of the route validation system
including pattern matching, duplicate detection, and error handling.

Test Categories:
1. Unit tests for matches_final_destination()
2. Unit tests for route loading validation
3. Integration tests with mock data
4. Error handling and edge cases

Usage:
    python test_route_validation.py
    python -m pytest test_route_validation.py -v
"""

import unittest
import sys
import os
import re
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the classes we need to test
from enhanced_commute_collector_cloud import EnhancedCommuteCollectorCloud, CommuteRoute, PlannedDeparture, CollectionStatus


class TestRouteValidation(unittest.TestCase):
    """Test suite for route validation functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.collector = EnhancedCommuteCollectorCloud()
        # Mock the database connection to avoid real DB calls in unit tests
        self.collector.get_db_connection = Mock(return_value=None)
        self.collector.logger = Mock()
    
    def test_matches_final_destination_basic_patterns(self):
        """Test basic pattern matching functionality"""
        # Test single destination
        self.assertTrue(self.collector.matches_final_destination("Lysaker", "Lysaker"))
        self.assertTrue(self.collector.matches_final_destination("Stabekk", "Stabekk"))
        self.assertFalse(self.collector.matches_final_destination("Ski", "Lysaker"))
        
        # Test pipe-separated patterns (regex alternation)
        self.assertTrue(self.collector.matches_final_destination("Lysaker", "Lysaker|Stabekk"))
        self.assertTrue(self.collector.matches_final_destination("Stabekk", "Lysaker|Stabekk"))
        self.assertFalse(self.collector.matches_final_destination("Ski", "Lysaker|Stabekk"))
        
        # Test case insensitive matching
        self.assertTrue(self.collector.matches_final_destination("LYSAKER", "Lysaker"))
        self.assertTrue(self.collector.matches_final_destination("lysaker", "Lysaker"))
        self.assertTrue(self.collector.matches_final_destination("Lysaker", "LYSAKER"))
    
    def test_matches_final_destination_edge_cases(self):
        """Test edge cases and error conditions"""
        # Test empty strings
        self.assertFalse(self.collector.matches_final_destination("", "Lysaker"))
        self.assertFalse(self.collector.matches_final_destination("Lysaker", ""))
        
        # Test None values (should not crash)
        with self.assertRaises(TypeError):
            self.collector.matches_final_destination(None, "Lysaker")
        with self.assertRaises(TypeError):
            self.collector.matches_final_destination("Lysaker", None)
        
        # Test special regex characters
        self.assertTrue(self.collector.matches_final_destination("Lysaker", "Lysaker"))
        self.assertTrue(self.collector.matches_final_destination("Lysaker Station", "Lysaker.*"))
    
    def test_matches_final_destination_complex_patterns(self):
        """Test complex regex patterns"""
        # Test multiple destinations
        self.assertTrue(self.collector.matches_final_destination("Lysaker", "Lysaker|Stabekk|Ski"))
        self.assertTrue(self.collector.matches_final_destination("Stabekk", "Lysaker|Stabekk|Ski"))
        self.assertTrue(self.collector.matches_final_destination("Ski", "Lysaker|Stabekk|Ski"))
        self.assertFalse(self.collector.matches_final_destination("Oslo S", "Lysaker|Stabekk|Ski"))
        
        # Test partial matches (should not match)
        self.assertFalse(self.collector.matches_final_destination("Lysaker Station", "Lysaker"))
        self.assertFalse(self.collector.matches_final_destination("Lysaker", "Lysaker Station"))
    
    def test_route_validation_empty_patterns(self):
        """Test that routes with empty patterns are properly handled"""
        # Mock database response with empty pattern
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "Test Route", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "", "westbound")
        ]
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Test that empty pattern routes are skipped
        routes = self.collector.load_commute_routes()
        
        # Should return empty list (route skipped)
        self.assertEqual(len(routes), 0)
        
        # Should log warning about empty pattern
        self.collector.logger.warning.assert_called()
        warning_call = self.collector.logger.warning.call_args[0][0]
        self.assertIn("Missing or empty final_destination_pattern", warning_call)
    
    def test_route_validation_duplicate_detection(self):
        """Test duplicate route detection logic"""
        # Mock database response with duplicate routes
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, "Route 1", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Lysaker", "westbound"),
            (2, "Route 2", "NSR:StopPlace:59638", "Myrvoll", 
             "NSR:StopPlace:337", "Oslo S", "Stabekk", "westbound"),  # Same source/target/direction
            (3, "Route 3", "NSR:StopPlace:337", "Oslo S", 
             "NSR:StopPlace:59638", "Myrvoll", "Ski", "eastbound")  # Different direction
        ]
        
        self.collector.get_db_connection = Mock(return_value=mock_conn)
        
        # Test duplicate detection
        routes = self.collector.load_commute_routes()
        
        # Should only load 2 routes (first and third, second is duplicate)
        self.assertEqual(len(routes), 2)
        
        # Should log warning about duplicate
        self.collector.logger.warning.assert_called()
        warning_calls = [call[0][0] for call in self.collector.logger.warning.call_args_list]
        duplicate_warning = any("duplicate route" in call.lower() for call in warning_calls)
        self.assertTrue(duplicate_warning)
    
    def test_route_validation_valid_routes(self):
        """Test that valid routes are loaded correctly"""
        # Mock database response with valid routes
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
        
        # Test valid route loading
        routes = self.collector.load_commute_routes()
        
        # Should load both routes
        self.assertEqual(len(routes), 2)
        
        # Check route properties
        morning_route = routes[0]
        self.assertEqual(morning_route.route_name, "Morning Route")
        self.assertEqual(morning_route.final_destination_pattern, "Lysaker|Stabekk")
        self.assertEqual(morning_route.direction, "westbound")
        
        afternoon_route = routes[1]
        self.assertEqual(afternoon_route.route_name, "Afternoon Route")
        self.assertEqual(afternoon_route.final_destination_pattern, "Ski")
        self.assertEqual(afternoon_route.direction, "eastbound")
    
    def test_fetch_planned_departures_pattern_validation(self):
        """Test that fetch_planned_departures properly validates patterns"""
        # Create a test route
        route = CommuteRoute(
            route_name="Test Route",
            source_station_id="NSR:StopPlace:59638",
            source_station_name="Myrvoll",
            target_station_id="NSR:StopPlace:337",
            target_station_name="Oslo S",
            final_destination_pattern="Lysaker|Stabekk",
            direction="westbound"
        )
        
        # Mock API response
        mock_api_response = {
            'data': {
                'stopPlace': {
                    'estimatedCalls': [
                        {
                            'serviceJourney': {
                                'line': {'publicCode': 'L2'},
                                'id': 'journey1'
                            },
                            'aimedDepartureTime': '2025-01-15T08:00:00Z',
                            'destinationDisplay': {'frontText': 'Lysaker'}
                        },
                        {
                            'serviceJourney': {
                                'line': {'publicCode': 'L2'},
                                'id': 'journey2'
                            },
                            'aimedDepartureTime': '2025-01-15T08:15:00Z',
                            'destinationDisplay': {'frontText': 'Ski'}  # Should be filtered out
                        }
                    ]
                }
            }
        }
        
        # Mock the API call
        with patch.object(self.collector, 'make_api_request', return_value=mock_api_response):
            departures = self.collector.fetch_planned_departures(route, datetime.now(timezone.utc))
        
        # Should only return the Lysaker departure (Ski should be filtered)
        self.assertEqual(len(departures), 1)
        self.assertEqual(departures[0].final_destination, "Lysaker")
        self.assertEqual(departures[0].service_journey_id, "journey1")
    
    def test_fetch_planned_departures_empty_pattern_handling(self):
        """Test handling of routes with empty patterns in fetch_planned_departures"""
        # Create a route with empty pattern (should not happen after validation, but test defensive code)
        route = CommuteRoute(
            route_name="Test Route",
            source_station_id="NSR:StopPlace:59638",
            source_station_name="Myrvoll",
            target_station_id="NSR:StopPlace:337",
            target_station_name="Oslo S",
            final_destination_pattern="",  # Empty pattern
            direction="westbound"
        )
        
        # Mock API response
        mock_api_response = {
            'data': {
                'stopPlace': {
                    'estimatedCalls': [
                        {
                            'serviceJourney': {
                                'line': {'publicCode': 'L2'},
                                'id': 'journey1'
                            },
                            'aimedDepartureTime': '2025-01-15T08:00:00Z',
                            'destinationDisplay': {'frontText': 'Lysaker'}
                        }
                    ]
                }
            }
        }
        
        # Mock the API call
        with patch.object(self.collector, 'make_api_request', return_value=mock_api_response):
            departures = self.collector.fetch_planned_departures(route, datetime.now(timezone.utc))
        
        # Should return empty list and log error
        self.assertEqual(len(departures), 0)
        self.collector.logger.error.assert_called()
        error_call = self.collector.logger.error.call_args[0][0]
        self.assertIn("has no pattern", error_call)


class TestRouteValidationIntegration(unittest.TestCase):
    """Integration tests for route validation with real data patterns"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.collector = EnhancedCommuteCollectorCloud()
        self.collector.logger = Mock()
    
    def test_real_world_pattern_scenarios(self):
        """Test with real-world pattern scenarios from the project"""
        # Test the actual patterns used in the project
        test_cases = [
            # (destination, pattern, should_match)
            ("Lysaker", "Lysaker|Stabekk", True),
            ("Stabekk", "Lysaker|Stabekk", True),
            ("Ski", "Lysaker|Stabekk", False),
            ("Ski", "Ski", True),
            ("Oslo S", "Lysaker|Stabekk", False),
            ("Oslo S", "Ski", False),
            ("Lysaker stasjon", "Lysaker", False),  # Partial match should not work
            ("Lysaker", "Lysaker stasjon", False),  # Partial match should not work
        ]
        
        for destination, pattern, should_match in test_cases:
            with self.subTest(destination=destination, pattern=pattern):
                result = self.collector.matches_final_destination(destination, pattern)
                self.assertEqual(result, should_match, 
                    f"Expected {destination} {'to match' if should_match else 'not to match'} {pattern}")


def run_tests():
    """Run all tests and provide a summary"""
    print("🧪 Running Route Validation Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRouteValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestRouteValidationIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
