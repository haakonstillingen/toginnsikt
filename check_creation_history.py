#!/usr/bin/env python3
"""
Check when planned departures were created
"""

import psycopg2
from config_cloud import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()

print("CREATION TIMESTAMPS FOR MORNING COMMUTE DEPARTURES:")
print("=" * 100)

cur.execute("""
    SELECT 
        pd.final_destination,
        MIN(pd.created_at AT TIME ZONE 'Europe/Oslo') as first_created,
        MAX(pd.created_at AT TIME ZONE 'Europe/Oslo') as last_created,
        COUNT(DISTINCT DATE(pd.created_at)) as creation_days,
        COUNT(*) as total
    FROM planned_departures pd
    JOIN commute_routes cr ON pd.route_id = cr.id
    WHERE cr.route_name = 'Morning Commute'
    AND cr.id = 1
    AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = '2025-10-06'
    GROUP BY pd.final_destination
    ORDER BY total DESC;
""")

print(f"\n{'Destination':<15} {'First Created':<25} {'Last Created':<25} {'Days':<6} {'Count'}")
print("-" * 100)
for row in cur.fetchall():
    dest, first, last, days, count = row
    print(f"{dest:<15} {str(first):<25} {str(last):<25} {days:<6} {count}")

# Check if there are any direct INSERT statements bypassing the pattern match
print("\n" + "=" * 100)
print("SAMPLE OF SKI DEPARTURES (should NOT exist):")
print("=" * 100)

cur.execute("""
    SELECT 
        pd.id,
        pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as time,
        pd.final_destination,
        pd.created_at AT TIME ZONE 'Europe/Oslo' as created
    FROM planned_departures pd
    JOIN commute_routes cr ON pd.route_id = cr.id
    WHERE cr.route_name = 'Morning Commute'
    AND cr.id = 1
    AND pd.final_destination = 'Ski'
    AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = '2025-10-06'
    ORDER BY pd.planned_departure_time
    LIMIT 5;
""")

for row in cur.fetchall():
    id, time, dest, created = row
    print(f"[{id}] {time} → {dest} (created: {created})")

cur.close()
conn.close()
