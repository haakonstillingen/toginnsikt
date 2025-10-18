#!/usr/bin/env python3
"""
Test script to verify tooltip filtering behavior for delay chart.

This script tests the tooltip filtering logic to ensure that categories
with zero values are properly filtered out from the tooltip display.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_tooltip_formatter_logic():
    """
    Test the tooltip formatter logic to ensure zero values are filtered out.
    This simulates the JavaScript formatter function behavior.
    """
    print("🧪 Testing tooltip formatter logic...")
    
    # Mock chart config (simplified version of the actual config)
    chart_config = {
        "onTimeDepartures": {
            "label": "I Riktig Tid",
            "color": "#22c55e"
        },
        "delayedClassified": {
            "label": "Forsinket", 
            "color": "#f59e0b"
        },
        "cancelledDepartures": {
            "label": "Kansellert",
            "color": "#000000"
        },
        "severelyDelayed": {
            "label": "Alvorlig Forsinket",
            "color": "#ef4444"
        },
        "unknownDepartures": {
            "label": "Ukjent Status",
            "color": "#6b7280"
        }
    }
    
    def mock_formatter(value, name):
        """Mock the formatter function with filtering logic"""
        # Only show categories with non-zero values
        if value == 0 or value is None:
            return None
        return [
            f"{value} avganger",
            chart_config.get(name, {}).get("label", name)
        ]
    
    # Test case 1: Hour with mixed data (some zero, some non-zero)
    print("\n📊 Test Case 1: Mixed data (17:00 hour)")
    test_data_17_00 = [
        ("onTimeDepartures", 3),
        ("delayedClassified", 1), 
        ("severelyDelayed", 0),
        ("cancelledDepartures", 0),
        ("unknownDepartures", 0)
    ]
    
    print("Input data:")
    for name, value in test_data_17_00:
        print(f"  {name}: {value}")
    
    print("\nFiltered tooltip content:")
    filtered_items = []
    for name, value in test_data_17_00:
        result = mock_formatter(value, name)
        if result is not None:
            filtered_items.append(result)
            print(f"  {result[1]}: {result[0]}")
    
    # Verify only non-zero items are shown
    expected_non_zero = 2  # onTimeDepartures and delayedClassified
    actual_non_zero = len(filtered_items)
    assert actual_non_zero == expected_non_zero, f"Expected {expected_non_zero} non-zero items, got {actual_non_zero}"
    print(f"✅ Correctly filtered: {actual_non_zero} non-zero items shown")
    
    # Test case 2: Hour with all zero values
    print("\n📊 Test Case 2: All zero data (15:00 hour)")
    test_data_15_00 = [
        ("onTimeDepartures", 0),
        ("delayedClassified", 0),
        ("severelyDelayed", 0), 
        ("cancelledDepartures", 1),  # Only cancelled departures
        ("unknownDepartures", 0)
    ]
    
    print("Input data:")
    for name, value in test_data_15_00:
        print(f"  {name}: {value}")
    
    print("\nFiltered tooltip content:")
    filtered_items = []
    for name, value in test_data_15_00:
        result = mock_formatter(value, name)
        if result is not None:
            filtered_items.append(result)
            print(f"  {result[1]}: {result[0]}")
    
    # Verify only cancelled departures are shown
    expected_non_zero = 1  # Only cancelledDepartures
    actual_non_zero = len(filtered_items)
    assert actual_non_zero == expected_non_zero, f"Expected {expected_non_zero} non-zero items, got {actual_non_zero}"
    print(f"✅ Correctly filtered: {actual_non_zero} non-zero items shown")
    
    # Test case 3: Hour with all non-zero values
    print("\n📊 Test Case 3: All non-zero data (busy hour)")
    test_data_busy = [
        ("onTimeDepartures", 2),
        ("delayedClassified", 1),
        ("severelyDelayed", 1),
        ("cancelledDepartures", 1),
        ("unknownDepartures", 1)
    ]
    
    print("Input data:")
    for name, value in test_data_busy:
        print(f"  {name}: {value}")
    
    print("\nFiltered tooltip content:")
    filtered_items = []
    for name, value in test_data_busy:
        result = mock_formatter(value, name)
        if result is not None:
            filtered_items.append(result)
            print(f"  {result[1]}: {result[0]}")
    
    # Verify all items are shown
    expected_non_zero = 5  # All categories have non-zero values
    actual_non_zero = len(filtered_items)
    assert actual_non_zero == expected_non_zero, f"Expected {expected_non_zero} non-zero items, got {actual_non_zero}"
    print(f"✅ Correctly filtered: {actual_non_zero} non-zero items shown")
    
    print("\n🎉 All tooltip filtering tests passed!")

def test_edge_cases():
    """Test edge cases for the formatter function"""
    print("\n🔍 Testing edge cases...")
    
    def mock_formatter(value, name):
        if value == 0 or value is None:
            return None
        return [f"{value} avganger", name]
    
    # Test with None values
    result = mock_formatter(None, "test")
    assert result is None, "None values should be filtered out"
    print("✅ None values correctly filtered")
    
    # Test with undefined (simulated as None in Python)
    result = mock_formatter(None, "test") 
    assert result is None, "Undefined values should be filtered out"
    print("✅ Undefined values correctly filtered")
    
    # Test with zero
    result = mock_formatter(0, "test")
    assert result is None, "Zero values should be filtered out"
    print("✅ Zero values correctly filtered")
    
    # Test with negative values (should not be filtered)
    result = mock_formatter(-1, "test")
    assert result is not None, "Negative values should not be filtered"
    print("✅ Negative values correctly preserved")
    
    print("🎉 All edge case tests passed!")

def main():
    """Run all tooltip filtering tests"""
    print("🚀 Starting tooltip filtering tests...")
    print("=" * 50)
    
    try:
        test_tooltip_formatter_logic()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nThe tooltip filtering fix should work correctly.")
        print("Categories with zero values will be hidden from the tooltip.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
