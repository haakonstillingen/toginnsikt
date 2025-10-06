#!/usr/bin/env python3
"""
List all departures from Myrvoll to Oslo S for 2025-10-06
"""

import psycopg2
from config_cloud import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
cur = conn.cursor()

cur.execute("""
    SELECT 
        pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as planned_time,
        pd.final_destination,
        pd.collection_status,
        ad.actual_departure_time AT TIME ZONE 'Europe/Oslo' as actual_time,
        ad.delay_minutes
    FROM planned_departures pd
    JOIN commute_routes cr ON pd.route_id = cr.id
    LEFT JOIN actual_departures ad ON ad.planned_departure_id = pd.id
    WHERE cr.route_name = 'Morning Commute'
    AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = '2025-10-06'
    ORDER BY pd.planned_departure_time;
""")

print("Myrvoll → Oslo S - 2025-10-06")
print()

for row in cur.fetchall():
    planned, dest, status, actual, delay = row
    if actual:
        delay_text = f" (delay: {delay} min)" if delay and delay > 0 else ""
        print(f"{planned} → {dest:<15} | Actual: {actual}{delay_text}")
    else:
        print(f"{planned} → {dest:<15} | Status: {status}")

cur.close()
conn.close()
