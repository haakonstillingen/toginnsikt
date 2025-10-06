#!/usr/bin/env python3
"""
Query all departures from Myrvoll to Oslo S for today (2025-10-06)
"""

import psycopg2
from datetime import datetime
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

def query_myrvoll_to_oslo():
    """Query all Myrvoll to Oslo S departures for today"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    target_date = '2025-10-06'
    
    print("=" * 140)
    print(f"MYRVOLL → OSLO S DEPARTURES FOR {target_date}")
    print("=" * 140)
    print()
    
    # Get all planned departures for Morning Commute (Myrvoll → Oslo S)
    cur.execute("""
        SELECT 
            pd.id,
            pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as local_time,
            pd.planned_departure_time AT TIME ZONE 'UTC' as utc_time,
            pd.line_code,
            pd.final_destination,
            pd.service_journey_id,
            pd.collection_status,
            pd.retry_count,
            ad.actual_departure_time AT TIME ZONE 'Europe/Oslo' as actual_local,
            ad.expected_departure_time AT TIME ZONE 'Europe/Oslo' as expected_local,
            ad.delay_minutes,
            ad.is_cancelled,
            ad.is_realtime,
            ad.collected_at AT TIME ZONE 'Europe/Oslo' as collected_at_local
        FROM planned_departures pd
        JOIN commute_routes cr ON pd.route_id = cr.id
        LEFT JOIN actual_departures ad ON ad.planned_departure_id = pd.id
        WHERE cr.route_name = 'Morning Commute'
        AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        ORDER BY pd.planned_departure_time;
    """, (target_date,))
    
    departures = cur.fetchall()
    
    print(f"Total departures: {len(departures)}")
    print()
    print(f"{'ID':<6} {'Planned (Local)':<20} {'Planned (UTC)':<20} {'Status':<12} {'Retry':<7} {'Actual (Local)':<20} {'Delay':<8} {'Cancelled':<10} {'RT':<5} {'Destination':<15}")
    print("-" * 140)
    
    collected_count = 0
    pending_count = 0
    failed_count = 0
    
    for row in departures:
        (id, planned_local, planned_utc, line, dest, journey_id, 
         status, retry_count, actual_local, expected_local, 
         delay, cancelled, realtime, collected_at) = row
        
        # Count by status
        if status == 'collected':
            collected_count += 1
        elif status == 'pending':
            pending_count += 1
        elif status == 'failed':
            failed_count += 1
        
        # Format fields
        actual_str = str(actual_local) if actual_local else "N/A"
        delay_str = f"{delay}min" if delay is not None else "N/A"
        cancelled_str = "YES" if cancelled else "No"
        realtime_str = "YES" if realtime else "No"
        retry_str = str(retry_count) if retry_count is not None else "0"
        
        # Highlight issues
        status_display = status if status else "NULL"
        
        print(f"{id:<6} {str(planned_local):<20} {str(planned_utc):<20} {status_display:<12} {retry_str:<7} {actual_str:<20} {delay_str:<8} {cancelled_str:<10} {realtime_str:<5} {dest:<15}")
    
    print()
    print("=" * 140)
    print("SUMMARY:")
    print("-" * 140)
    print(f"  Total departures: {len(departures)}")
    print(f"  Collected: {collected_count} ({collected_count/len(departures)*100:.1f}%)")
    print(f"  Pending: {pending_count} ({pending_count/len(departures)*100:.1f}%)")
    print(f"  Failed: {failed_count} ({failed_count/len(departures)*100:.1f}%)")
    print()
    
    # Show problematic departures
    print("⚠️  PENDING DEPARTURES (Not yet collected):")
    print("-" * 140)
    cur.execute("""
        SELECT 
            pd.id,
            pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as local_time,
            pd.planned_departure_time AT TIME ZONE 'UTC' as utc_time,
            pd.final_destination,
            pd.retry_count,
            pd.last_retry_time AT TIME ZONE 'Europe/Oslo' as last_retry
        FROM planned_departures pd
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE cr.route_name = 'Morning Commute'
        AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        AND pd.collection_status = 'pending'
        ORDER BY pd.planned_departure_time;
    """, (target_date,))
    
    pending = cur.fetchall()
    if pending:
        for row in pending:
            id, local_time, utc_time, dest, retry_count, last_retry = row
            print(f"  [{id}] {local_time} (UTC: {utc_time}) → {dest}")
            print(f"       Retries: {retry_count if retry_count else 0}, Last retry: {last_retry if last_retry else 'Never'}")
    else:
        print("  None")
    print()
    
    # Show failed departures
    print("❌ FAILED DEPARTURES:")
    print("-" * 140)
    cur.execute("""
        SELECT 
            pd.id,
            pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as local_time,
            pd.planned_departure_time AT TIME ZONE 'UTC' as utc_time,
            pd.final_destination,
            pd.retry_count,
            pd.last_retry_time AT TIME ZONE 'Europe/Oslo' as last_retry
        FROM planned_departures pd
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE cr.route_name = 'Morning Commute'
        AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        AND pd.collection_status = 'failed'
        ORDER BY pd.planned_departure_time;
    """, (target_date,))
    
    failed = cur.fetchall()
    if failed:
        for row in failed:
            id, local_time, utc_time, dest, retry_count, last_retry = row
            print(f"  [{id}] {local_time} (UTC: {utc_time}) → {dest}")
            print(f"       Retries: {retry_count if retry_count else 0}, Last retry: {last_retry if last_retry else 'Never'}")
    else:
        print("  None")
    print()
    
    # Time range analysis
    print("⏰ TIME DISTRIBUTION:")
    print("-" * 140)
    cur.execute("""
        SELECT 
            EXTRACT(HOUR FROM pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') as hour,
            COUNT(*) as total,
            COUNT(CASE WHEN pd.collection_status = 'collected' THEN 1 END) as collected,
            COUNT(CASE WHEN pd.collection_status = 'pending' THEN 1 END) as pending,
            COUNT(CASE WHEN pd.collection_status = 'failed' THEN 1 END) as failed
        FROM planned_departures pd
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE cr.route_name = 'Morning Commute'
        AND DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        GROUP BY EXTRACT(HOUR FROM pd.planned_departure_time AT TIME ZONE 'Europe/Oslo')
        ORDER BY hour;
    """, (target_date,))
    
    time_dist = cur.fetchall()
    print(f"  {'Hour (Local)':<15} {'Total':<8} {'Collected':<12} {'Pending':<10} {'Failed':<10} {'Coverage':<10}")
    print(f"  {'-'*15} {'-'*8} {'-'*12} {'-'*10} {'-'*10} {'-'*10}")
    for hour, total, collected, pending, failed in time_dist:
        coverage = (collected / total * 100) if total > 0 else 0
        print(f"  {int(hour):02d}:00          {total:<8} {collected:<12} {pending:<10} {failed:<10} {coverage:.1f}%")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    query_myrvoll_to_oslo()
