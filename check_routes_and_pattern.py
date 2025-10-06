#!/usr/bin/env python3
"""
Check route configuration and pattern matching
"""

import psycopg2
from config_cloud import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()

print("=" * 100)
print("COMMUTE ROUTES IN DATABASE:")
print("=" * 100)
cur.execute("SELECT id, route_name, source_station_name, target_station_name, final_destination_pattern, direction FROM commute_routes;")
for row in cur.fetchall():
    id, name, source, target, pattern, direction = row
    print(f"\n[{id}] {name}")
    print(f"    {source} → {target}")
    print(f"    Pattern: {pattern}")
    print(f"    Direction: {direction}")

print("\n" + "=" * 100)
print("ACTUAL DESTINATIONS IN PLANNED DEPARTURES (Morning Commute):")
print("=" * 100)
cur.execute("""
    SELECT DISTINCT pd.final_destination, COUNT(*) as count
    FROM planned_departures pd
    JOIN commute_routes cr ON pd.route_id = cr.id
    WHERE cr.route_name = 'Morning Commute'
    AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = '2025-10-06'
    GROUP BY pd.final_destination
    ORDER BY count DESC;
""")

print("\nDestinations found:")
for row in cur.fetchall():
    dest, count = row
    print(f"  {dest}: {count} departures")

print("\n" + "=" * 100)
print("CHECKING PATTERN MATCH:")
print("=" * 100)
print("Expected pattern: 'Lysaker|Stabekk'")
print("Should match: Lysaker, Stabekk")
print("Should NOT match: Ski, Oslo S, Skøyen, etc.")

cur.close()
conn.close()
