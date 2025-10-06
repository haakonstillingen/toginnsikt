#!/usr/bin/env python3
"""
Test the pattern matching logic
"""

import re

def matches_final_destination(destination: str, pattern: str) -> bool:
    """Check if destination matches the route's final destination pattern"""
    # Convert pattern to regex (e.g., "Lysaker|Stabekk" becomes "Lysaker|Stabekk")
    pattern_regex = pattern.replace('|', '|')
    return bool(re.search(pattern_regex, destination, re.IGNORECASE))

# Test with the actual pattern
pattern = "Lysaker|Stabekk"

destinations = [
    ("Ski", False),
    ("Stabekk", True),
    ("Oslo S", False),
    ("Skøyen", False),
    ("Lysaker", True),
]

print(f"Pattern: '{pattern}'")
print("=" * 60)

for dest, expected in destinations:
    result = matches_final_destination(dest, pattern)
    status = "✅" if result == expected else "❌ WRONG"
    print(f"{dest:<15} Expected: {expected:<5} Got: {result:<5} {status}")
