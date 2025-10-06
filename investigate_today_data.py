#!/usr/bin/env python3
"""
Query planned and actual departures for today (2025-10-06)
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

def query_today_data():
    """Query all planned and actual departures for today"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    target_date = '2025-10-06'
    
    print("=" * 120)
    print(f"INVESTIGATING COLLECTION DATA FOR {target_date}")
    print("=" * 120)
    print()
    
    # Query 1: Count planned departures
    print("📋 PLANNED DEPARTURES:")
    print("-" * 120)
    cur.execute("""
        SELECT 
            cr.route_name,
            COUNT(*) as total,
            MIN(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') as earliest,
            MAX(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') as latest
        FROM planned_departures pd
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        GROUP BY cr.route_name
        ORDER BY cr.route_name;
    """, (target_date,))
    
    planned_results = cur.fetchall()
    total_planned = 0
    
    for row in planned_results:
        route_name, count, earliest, latest = row
        total_planned += count
        print(f"  {route_name}: {count} departures")
        print(f"    Earliest: {earliest}")
        print(f"    Latest: {latest}")
    
    if not planned_results:
        print("  No planned departures found")
    
    print(f"\n  TOTAL PLANNED: {total_planned}")
    print()
    
    # Query 2: Count actual departures
    print("🚂 ACTUAL DEPARTURES:")
    print("-" * 120)
    cur.execute("""
        SELECT 
            cr.route_name,
            COUNT(*) as total,
            MIN(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') as earliest,
            MAX(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') as latest
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        GROUP BY cr.route_name
        ORDER BY cr.route_name;
    """, (target_date,))
    
    actual_results = cur.fetchall()
    total_actual = 0
    
    for row in actual_results:
        route_name, count, earliest, latest = row
        total_actual += count
        print(f"  {route_name}: {count} departures")
        print(f"    Earliest: {earliest}")
        print(f"    Latest: {latest}")
    
    if not actual_results:
        print("  No actual departures found")
    
    print(f"\n  TOTAL ACTUAL: {total_actual}")
    print()
    
    # Query 3: Coverage analysis
    print("📊 COVERAGE ANALYSIS:")
    print("-" * 120)
    if total_planned > 0:
        coverage_pct = (total_actual / total_planned) * 100
        print(f"  Coverage: {total_actual}/{total_planned} ({coverage_pct:.1f}%)")
        print(f"  Missing: {total_planned - total_actual} departures")
    else:
        print("  No planned departures found for this date")
    print()
    
    # Query 4: Collection status breakdown
    print("📈 PLANNED DEPARTURES - COLLECTION STATUS:")
    print("-" * 120)
    cur.execute("""
        SELECT 
            collection_status,
            COUNT(*) as count
        FROM planned_departures pd
        WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        GROUP BY collection_status
        ORDER BY collection_status;
    """, (target_date,))
    
    status_results = cur.fetchall()
    if status_results:
        for row in status_results:
            status, count = row
            status_str = status if status else "NULL/Not Set"
            print(f"  {status_str}: {count}")
    else:
        print("  No status data available")
    print()
    
    # Query 5: Sample planned departures (first 10)
    print("📋 SAMPLE PLANNED DEPARTURES (First 10):")
    print("-" * 120)
    cur.execute("""
        SELECT 
            pd.id,
            cr.route_name,
            pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as local_time,
            pd.service_journey_id,
            pd.line_code,
            pd.final_destination,
            pd.collection_status
        FROM planned_departures pd
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        ORDER BY pd.planned_departure_time
        LIMIT 10;
    """, (target_date,))
    
    for row in cur.fetchall():
        id, route, time, journey_id, line, dest, status = row
        status_str = status if status else "NULL"
        print(f"  [{id}] {route} | {time} | {line} to {dest} | Status: {status_str}")
    print()
    
    # Query 6: Sample actual departures (first 10)
    print("🚂 SAMPLE ACTUAL DEPARTURES (First 10):")
    print("-" * 120)
    cur.execute("""
        SELECT 
            ad.id,
            cr.route_name,
            pd.planned_departure_time AT TIME ZONE 'Europe/Oslo' as planned_local,
            ad.actual_departure_time AT TIME ZONE 'Europe/Oslo' as actual_local,
            ad.delay_minutes,
            ad.is_cancelled,
            ad.is_realtime
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
        ORDER BY pd.planned_departure_time
        LIMIT 10;
    """, (target_date,))
    
    for row in cur.fetchall():
        id, route, planned, actual, delay, cancelled, realtime = row
        delay_str = f"{delay}min" if delay is not None else "N/A"
        print(f"  [{id}] {route} | Planned: {planned} | Actual: {actual} | Delay: {delay_str} | Cancelled: {cancelled} | Realtime: {realtime}")
    print()
    
    # Query 7: Delays and cancellations analysis
    print("⚠️  DELAYS & CANCELLATIONS:")
    print("-" * 120)
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN ad.is_cancelled = true THEN 1 END) as cancelled,
            COUNT(CASE WHEN ad.delay_minutes > 0 THEN 1 END) as delayed,
            COUNT(CASE WHEN ad.delay_minutes = 0 THEN 1 END) as on_time,
            AVG(ad.delay_minutes) as avg_delay,
            MAX(ad.delay_minutes) as max_delay
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s;
    """, (target_date,))
    
    row = cur.fetchone()
    if row and row[0] > 0:
        total, cancelled, delayed, on_time, avg_delay, max_delay = row
        print(f"  Total actual departures: {total}")
        print(f"  Cancelled: {cancelled} ({(cancelled/total*100):.1f}%)")
        print(f"  Delayed: {delayed} ({(delayed/total*100):.1f}%)")
        print(f"  On time: {on_time} ({(on_time/total*100):.1f}%)")
        if avg_delay is not None:
            print(f"  Average delay: {avg_delay:.1f} minutes")
        if max_delay is not None:
            print(f"  Maximum delay: {max_delay} minutes")
    else:
        print("  No actual departure data available")
    print()
    
    # Query 8: Check when planned departures were created
    print("🕒 PLANNED DEPARTURES CREATION TIME:")
    print("-" * 120)
    cur.execute("""
        SELECT 
            MIN(created_at AT TIME ZONE 'Europe/Oslo') as first_created,
            MAX(created_at AT TIME ZONE 'Europe/Oslo') as last_created,
            COUNT(DISTINCT DATE(created_at AT TIME ZONE 'Europe/Oslo')) as unique_creation_dates
        FROM planned_departures 
        WHERE DATE(planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s;
    """, (target_date,))
    
    row = cur.fetchone()
    if row and row[0]:
        first, last, unique = row
        print(f"  First created: {first}")
        print(f"  Last created: {last}")
        print(f"  Unique creation dates: {unique}")
    else:
        print("  No creation timestamps available")
    print()
    
    # Query 9: Hourly breakdown of planned vs actual
    print("⏰ HOURLY BREAKDOWN (Planned vs Actual):")
    print("-" * 120)
    cur.execute("""
        WITH hourly_planned AS (
            SELECT 
                EXTRACT(HOUR FROM planned_departure_time AT TIME ZONE 'Europe/Oslo') as hour,
                COUNT(*) as planned_count
            FROM planned_departures
            WHERE DATE(planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
            GROUP BY EXTRACT(HOUR FROM planned_departure_time AT TIME ZONE 'Europe/Oslo')
        ),
        hourly_actual AS (
            SELECT 
                EXTRACT(HOUR FROM pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') as hour,
                COUNT(*) as actual_count
            FROM actual_departures ad
            JOIN planned_departures pd ON ad.planned_departure_id = pd.id
            WHERE DATE(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo') = %s
            GROUP BY EXTRACT(HOUR FROM pd.planned_departure_time AT TIME ZONE 'Europe/Oslo')
        )
        SELECT 
            COALESCE(hp.hour, ha.hour) as hour,
            COALESCE(hp.planned_count, 0) as planned,
            COALESCE(ha.actual_count, 0) as actual
        FROM hourly_planned hp
        FULL OUTER JOIN hourly_actual ha ON hp.hour = ha.hour
        ORDER BY hour;
    """, (target_date, target_date))
    
    hourly_results = cur.fetchall()
    if hourly_results:
        print(f"  {'Hour':<10} {'Planned':<10} {'Actual':<10} {'Missing':<10} {'Coverage %':<12}")
        print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*12}")
        for hour, planned, actual in hourly_results:
            missing = planned - actual
            coverage = (actual / planned * 100) if planned > 0 else 0
            print(f"  {int(hour):02d}:00     {planned:<10} {actual:<10} {missing:<10} {coverage:.1f}%")
    else:
        print("  No hourly data available")
    print()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    query_today_data()
