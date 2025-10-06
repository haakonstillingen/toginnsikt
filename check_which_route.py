#!/usr/bin/env python3
"""
Check which route_id is being used for Ski departures
"""

import psycopg2
from config_cloud import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()

print("CHECKING ROUTE_ID FOR EACH DESTINATION:")
print("=" * 100)

cur.execute("""
    SELECT 
        pd.route_id,
        cr.route_name,
        cr.final_destination_pattern,
        pd.final_destination,
        COUNT(*) as count
    FROM planned_departures pd
    JOIN commute_routes cr ON pd.route_id = cr.id
    WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = '2025-10-06'
    GROUP BY pd.route_id, cr.route_name, cr.final_destination_pattern, pd.final_destination
    ORDER BY cr.route_name, count DESC;
""")

current_route = None
for row in cur.fetchall():
    route_id, route_name, pattern, destination, count = row
    
    if current_route != route_name:
        print(f"\n{route_name} (route_id={route_id}, pattern='{pattern}'):")
        current_route = route_name
    
    # Check if destination matches pattern
    matches = "✅ MATCH" if pattern and destination in pattern else ("❌ NO MATCH" if pattern else "⚠️ NO PATTERN")
    
    print(f"  {destination:<15} {count:>3} departures  {matches}")

cur.close()
conn.close()
