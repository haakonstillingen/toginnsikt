#!/usr/bin/env python3
"""
Simple list of all Myrvoll to Oslo S departures for today (2025-10-06)
"""

import psycopg2
from config_cloud import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def list_departures():
    """List all Myrvoll to Oslo S departures"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    target_date = '2025-10-06'
    
    print("=" * 150)
    print(f"MYRVOLL → OSLO S DEPARTURES - {target_date}")
    print("=" * 150)
    print()
    
    # Get all departures
    cur.execute("""
        SELECT 
            pd.id,
            pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as planned_local,
            pd.final_destination,
            pd.collection_status,
            ad.actual_departure_time AT TIME ZONE 'Europe/Oslo' as actual_local,
            ad.delay_minutes,
            ad.is_cancelled,
            ad.is_realtime
        FROM planned_departures pd
        JOIN commute_routes cr ON pd.route_id = cr.id
        LEFT JOIN actual_departures ad ON ad.planned_departure_id = pd.id
        WHERE cr.route_name = 'Morning Commute'
        AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        ORDER BY pd.planned_departure_time;
    """, (target_date,))
    
    departures = cur.fetchall()
    
    print(f"{'ID':<6} {'Planned Time':<20} {'→ Destination':<15} {'Status':<12} {'Actual Time':<20} {'Delay':<10} {'Cancelled':<10} {'Realtime'}")
    print("-" * 150)
    
    for row in departures:
        id, planned, dest, status, actual, delay, cancelled, realtime = row
        
        actual_str = str(actual) if actual else "-"
        delay_str = f"{delay} min" if delay is not None else "-"
        cancelled_str = "YES" if cancelled else "-"
        realtime_str = "YES" if realtime else "-"
        
        print(f"{id:<6} {str(planned):<20} {dest:<15} {status:<12} {actual_str:<20} {delay_str:<10} {cancelled_str:<10} {realtime_str}")
    
    print("-" * 150)
    print(f"Total: {len(departures)} departures")
    print()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_departures()
