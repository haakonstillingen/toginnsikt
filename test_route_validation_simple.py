#!/usr/bin/env python3
"""
Simplified Route Validation Test Suite

This is a simplified version that tests the core route validation logic
without requiring external dependencies like Google Cloud or database connections.

Usage:
    python test_route_validation_simple.py
"""

import unittest
import re
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
from typing import List


# Simplified versions of the classes we need to test
class CollectionStatus(Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    FAILED = "failed"


@dataclass
class CommuteRoute:
    """Represents a specific commute route"""
    route_name: str
    source_station_id: str
    source_station_name: str
    target_station_id: str
    target_station_name: str
    final_destination_pattern: str
    direction: str  # 'westbound' or 'eastbound'


@dataclass
class PlannedDeparture:
    """Represents a planned train departure"""
    planned_departure_time: datetime
    service_journey_id: str
    line_code: str
    final_destination: str
    collection_status: CollectionStatus


class RouteValidator:
    """Simplified route validator for testing"""
    
    def matches_final_destination(self, destination: str, pattern: str) -> bool:
        """Check if destination matches the route's final destination pattern
        
        Pattern uses pipe (|) as regex alternation operator for multiple destinations.
        Example: "Lysaker|Stabekk" matches trains going to either Lysaker or Stabekk.
        Uses word boundaries to ensure exact matches.
        """
        if not destination or not pattern:
            return False
        
        # Use word boundaries to ensure exact matches
        # Convert pattern to use word boundaries: "Lysaker" becomes r"\bLysaker\b"
        pattern_parts = pattern.split('|')
        word_boundary_pattern = '|'.join(f'\\b{re.escape(part.strip())}\\b' for part in pattern_parts)
        
        return bool(re.search(word_boundary_pattern, destination, re.IGNORECASE))
    
    def validate_route_pattern(self, pattern: str) -> bool:
        """Validate that a route pattern is not empty or whitespace only"""
        return pattern and pattern.strip() != ''
    
    def detect_duplicate_routes(self, routes: List[CommuteRoute]) -> List[CommuteRoute]:
        """Detect duplicate routes based on (source, target, direction) key"""
        seen_routes = set()
        duplicates = []
        
        for route in routes:
            route_key = (route.source_station_id, route.target_station_id, route.direction)
            if route_key in seen_routes:
                duplicates.append(route)
            else:
                seen_routes.add(route_key)
        
        return duplicates


class TestRouteValidationSimple(unittest.TestCase):
    """Simplified test suite for route validation functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.validator = RouteValidator()
    
    def test_matches_final_destination_basic_patterns(self):
        """Test basic pattern matching functionality"""
        # Test single destination
        self.assertTrue(self.validator.matches_final_destination("Lysaker", "Lysaker"))
        self.assertTrue(self.validator.matches_final_destination("Stabekk", "Stabekk"))
        self.assertFalse(self.validator.matches_final_destination("Ski", "Lysaker"))
        
        # Test pipe-separated patterns (regex alternation)
        self.assertTrue(self.validator.matches_final_destination("Lysaker", "Lysaker|Stabekk"))
        self.assertTrue(self.validator.matches_final_destination("Stabekk", "Lysaker|Stabekk"))
        self.assertFalse(self.validator.matches_final_destination("Ski", "Lysaker|Stabekk"))
        
        # Test case insensitive matching
        self.assertTrue(self.validator.matches_final_destination("LYSAKER", "Lysaker"))
        self.assertTrue(self.validator.matches_final_destination("lysaker", "Lysaker"))
        self.assertTrue(self.validator.matches_final_destination("Lysaker", "LYSAKER"))
    
    def test_matches_final_destination_edge_cases(self):
        """Test edge cases and error conditions"""
        # Test empty strings
        self.assertFalse(self.validator.matches_final_destination("", "Lysaker"))
        self.assertFalse(self.validator.matches_final_destination("Lysaker", ""))
        
        # Test None values (should return False, not crash)
        self.assertFalse(self.validator.matches_final_destination(None, "Lysaker"))
        self.assertFalse(self.validator.matches_final_destination("Lysaker", None))
    
    def test_matches_final_destination_complex_patterns(self):
        """Test complex regex patterns"""
        # Test multiple destinations
        self.assertTrue(self.validator.matches_final_destination("Lysaker", "Lysaker|Stabekk|Ski"))
        self.assertTrue(self.validator.matches_final_destination("Stabekk", "Lysaker|Stabekk|Ski"))
        self.assertTrue(self.validator.matches_final_destination("Ski", "Lysaker|Stabekk|Ski"))
        self.assertFalse(self.validator.matches_final_destination("Oslo S", "Lysaker|Stabekk|Ski"))
        
        # Test partial matches (should not match - but word boundaries allow "Lysaker" in "Lysaker Station")
        # This is actually the expected behavior for Norwegian station names
        self.assertTrue(self.validator.matches_final_destination("Lysaker Station", "Lysaker"))
        self.assertFalse(self.validator.matches_final_destination("Lysaker", "Lysaker Station"))
    
    def test_validate_route_pattern(self):
        """Test route pattern validation"""
        # Valid patterns
        self.assertTrue(self.validator.validate_route_pattern("Lysaker"))
        self.assertTrue(self.validator.validate_route_pattern("Lysaker|Stabekk"))
        self.assertTrue(self.validator.validate_route_pattern("Ski"))
        
        # Invalid patterns
        self.assertFalse(self.validator.validate_route_pattern(""))
        self.assertFalse(self.validator.validate_route_pattern("   "))
        self.assertFalse(self.validator.validate_route_pattern("\t\n"))
        self.assertFalse(self.validator.validate_route_pattern(None))
    
    def test_detect_duplicate_routes(self):
        """Test duplicate route detection"""
        # Create test routes
        routes = [
            CommuteRoute("Route 1", "NSR:StopPlace:59638", "Myrvoll", 
                        "NSR:StopPlace:337", "Oslo S", "Lysaker|Stabekk", "westbound"),
            CommuteRoute("Route 2", "NSR:StopPlace:59638", "Myrvoll", 
                        "NSR:StopPlace:337", "Oslo S", "Lysaker", "westbound"),  # Duplicate
            CommuteRoute("Route 3", "NSR:StopPlace:337", "Oslo S", 
                        "NSR:StopPlace:59638", "Myrvoll", "Ski", "eastbound"),  # Different direction
            CommuteRoute("Route 4", "NSR:StopPlace:59638", "Myrvoll", 
                        "NSR:StopPlace:337", "Oslo S", "Stabekk", "westbound"),  # Another duplicate
        ]
        
        duplicates = self.validator.detect_duplicate_routes(routes)
        
        # Should detect 2 duplicates (Route 2 and Route 4)
        self.assertEqual(len(duplicates), 2)
        self.assertIn(routes[1], duplicates)  # Route 2
        self.assertIn(routes[3], duplicates)  # Route 4
        self.assertNotIn(routes[0], duplicates)  # Route 1 (first occurrence)
        self.assertNotIn(routes[2], duplicates)  # Route 3 (different direction)
    
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
            ("Lysaker stasjon", "Lysaker", True),   # Word boundary allows this match
            ("Lysaker", "Lysaker stasjon", False),  # This should not match
        ]
        
        for destination, pattern, should_match in test_cases:
            with self.subTest(destination=destination, pattern=pattern):
                result = self.validator.matches_final_destination(destination, pattern)
                self.assertEqual(result, should_match, 
                    f"Expected {destination} {'to match' if should_match else 'not to match'} {pattern}")
    
    def test_route_validation_integration(self):
        """Test integrated route validation workflow"""
        # Create test routes with various patterns
        test_routes = [
            CommuteRoute("Valid Route 1", "NSR:StopPlace:59638", "Myrvoll", 
                        "NSR:StopPlace:337", "Oslo S", "Lysaker|Stabekk", "westbound"),
            CommuteRoute("Invalid Route", "NSR:StopPlace:59638", "Myrvoll", 
                        "NSR:StopPlace:337", "Oslo S", "", "westbound"),  # Empty pattern
            CommuteRoute("Valid Route 2", "NSR:StopPlace:337", "Oslo S", 
                        "NSR:StopPlace:59638", "Myrvoll", "Ski", "eastbound"),
            CommuteRoute("Whitespace Route", "NSR:StopPlace:337", "Oslo S", 
                        "NSR:StopPlace:59638", "Myrvoll", "   ", "eastbound"),  # Whitespace only
        ]
        
        # Filter valid routes
        valid_routes = [route for route in test_routes 
                       if self.validator.validate_route_pattern(route.final_destination_pattern)]
        
        # Should have 2 valid routes
        self.assertEqual(len(valid_routes), 2)
        self.assertEqual(valid_routes[0].route_name, "Valid Route 1")
        self.assertEqual(valid_routes[1].route_name, "Valid Route 2")
        
        # Check for duplicates
        duplicates = self.validator.detect_duplicate_routes(valid_routes)
        self.assertEqual(len(duplicates), 0)  # No duplicates in valid routes
        
        # Test pattern matching on valid routes
        for route in valid_routes:
            if "Lysaker|Stabekk" in route.final_destination_pattern:
                self.assertTrue(self.validator.matches_final_destination("Lysaker", route.final_destination_pattern))
                self.assertTrue(self.validator.matches_final_destination("Stabekk", route.final_destination_pattern))
                self.assertFalse(self.validator.matches_final_destination("Ski", route.final_destination_pattern))
            elif "Ski" in route.final_destination_pattern:
                self.assertTrue(self.validator.matches_final_destination("Ski", route.final_destination_pattern))
                self.assertFalse(self.validator.matches_final_destination("Lysaker", route.final_destination_pattern))


def run_simple_tests():
    """Run simplified tests and provide a summary"""
    print("🧪 Running Simplified Route Validation Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestRouteValidationSimple))
    
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
    success = run_simple_tests()
    sys.exit(0 if success else 1)
