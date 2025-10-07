#!/usr/bin/env python3
"""
Delete incorrectly collected planned and actual departures that don't match route patterns

Morning Commute (route 1): Should only have Lysaker|Stabekk
Afternoon Commute (route 2): Should only have Ski
"""

import psycopg2
import re
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

def matches_pattern(destination: str, pattern: str) -> bool:
    """Check if destination matches the route pattern"""
    if not pattern:
        return False
    return bool(re.search(pattern, destination, re.IGNORECASE))

def delete_incorrect_departures():
    """Delete planned and actual departures that don't match route patterns"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 120)
    print("DELETE INCORRECTLY COLLECTED DEPARTURES")
    print("=" * 120)
    print()
    
    # Get all routes and their patterns
    cur.execute("""
        SELECT id, route_name, final_destination_pattern
        FROM commute_routes
        ORDER BY id;
    """)
    
    routes = cur.fetchall()
    
    print("ROUTE PATTERNS:")
    print("-" * 120)
    for route_id, route_name, pattern in routes:
        print(f"  Route {route_id} ({route_name}): Pattern = '{pattern}'")
    print()
    
    # Analyze each route for incorrect departures
    print("ANALYSIS OF INCORRECTLY COLLECTED DEPARTURES:")
    print("-" * 120)
    
    total_incorrect_planned = 0
    total_incorrect_actual = 0
    routes_to_clean = {}
    
    for route_id, route_name, pattern in routes:
        if not pattern:
            print(f"\n  Route {route_id} ({route_name}): Skipping (no pattern)")
            continue
        
        # Find all planned departures for this route
        cur.execute("""
            SELECT id, final_destination, COUNT(*) OVER() as total
            FROM planned_departures
            WHERE route_id = %s
            GROUP BY id, final_destination;
        """, (route_id,))
        
        all_departures = cur.fetchall()
        
        if not all_departures:
            print(f"\n  Route {route_id} ({route_name}): No departures found")
            continue
        
        # Count by destination and identify incorrect ones
        cur.execute("""
            SELECT final_destination, COUNT(*) as count
            FROM planned_departures
            WHERE route_id = %s
            GROUP BY final_destination
            ORDER BY count DESC;
        """, (route_id,))
        
        dest_counts = cur.fetchall()
        
        print(f"\n  Route {route_id} ({route_name}):")
        print(f"    Pattern: '{pattern}'")
        print(f"    Destinations found:")
        
        incorrect_dests = []
        correct_count = 0
        incorrect_count = 0
        
        for dest, count in dest_counts:
            matches = matches_pattern(dest, pattern)
            status = "✅ CORRECT" if matches else "❌ INCORRECT"
            print(f"      {dest}: {count} departures - {status}")
            
            if matches:
                correct_count += count
            else:
                incorrect_count += count
                incorrect_dests.append(dest)
        
        if incorrect_dests:
            routes_to_clean[route_id] = {
                'route_name': route_name,
                'pattern': pattern,
                'incorrect_destinations': incorrect_dests,
                'incorrect_count': incorrect_count
            }
            total_incorrect_planned += incorrect_count
            
            # Count actual departures for these incorrect planned departures
            cur.execute("""
                SELECT COUNT(DISTINCT ad.id)
                FROM actual_departures ad
                JOIN planned_departures pd ON ad.planned_departure_id = pd.id
                WHERE pd.route_id = %s 
                AND pd.final_destination = ANY(%s);
            """, (route_id, incorrect_dests))
            
            actual_count = cur.fetchone()[0]
            routes_to_clean[route_id]['actual_count'] = actual_count
            total_incorrect_actual += actual_count
        
        print(f"    Summary: {correct_count} correct, {incorrect_count} incorrect")
    
    print()
    print("=" * 120)
    print("DELETION SUMMARY:")
    print("=" * 120)
    
    if not routes_to_clean:
        print("  ✅ No incorrect departures found! All data matches route patterns.")
        cur.close()
        conn.close()
        return
    
    print(f"  Total incorrect PLANNED departures: {total_incorrect_planned}")
    print(f"  Total incorrect ACTUAL departures: {total_incorrect_actual}")
    print()
    
    for route_id, info in routes_to_clean.items():
        print(f"  Route {route_id} ({info['route_name']}):")
        print(f"    Will delete destinations: {', '.join(info['incorrect_destinations'])}")
        print(f"    Planned departures to delete: {info['incorrect_count']}")
        print(f"    Actual departures to delete: {info['actual_count']}")
        print()
    
    # Ask for confirmation
    import sys
    if '--yes' not in sys.argv:
        response = input("Do you want to proceed with deletion? (yes/no): ")
        
        if response.lower() != 'yes':
            print("\n❌ Deletion cancelled.")
            cur.close()
            conn.close()
            return
    else:
        print("Proceeding with deletion (--yes flag provided)...")
    
    print()
    print("Deleting incorrect departures...")
    print("-" * 120)
    
    try:
        total_planned_deleted = 0
        total_actual_deleted = 0
        
        for route_id, info in routes_to_clean.items():
            print(f"\n  Processing Route {route_id} ({info['route_name']})...")
            
            # First, delete actual departures linked to incorrect planned departures
            cur.execute("""
                DELETE FROM actual_departures
                WHERE planned_departure_id IN (
                    SELECT id FROM planned_departures
                    WHERE route_id = %s 
                    AND final_destination = ANY(%s)
                )
                RETURNING id;
            """, (route_id, info['incorrect_destinations']))
            
            actual_deleted = len(cur.fetchall())
            total_actual_deleted += actual_deleted
            print(f"    ✓ Deleted {actual_deleted} actual departures")
            
            # Then, delete the incorrect planned departures
            cur.execute("""
                DELETE FROM planned_departures
                WHERE route_id = %s 
                AND final_destination = ANY(%s)
                RETURNING id;
            """, (route_id, info['incorrect_destinations']))
            
            planned_deleted = len(cur.fetchall())
            total_planned_deleted += planned_deleted
            print(f"    ✓ Deleted {planned_deleted} planned departures")
        
        conn.commit()
        
        print()
        print("=" * 120)
        print("✅ DELETION COMPLETE!")
        print("=" * 120)
        print(f"  Total planned departures deleted: {total_planned_deleted}")
        print(f"  Total actual departures deleted: {total_actual_deleted}")
        print()
        
        # Show final state
        print("FINAL STATE - DEPARTURES BY DESTINATION:")
        print("-" * 120)
        
        for route_id, route_name, pattern in routes:
            cur.execute("""
                SELECT final_destination, COUNT(*) as count
                FROM planned_departures
                WHERE route_id = %s
                GROUP BY final_destination
                ORDER BY count DESC;
            """, (route_id,))
            
            dest_counts = cur.fetchall()
            
            if dest_counts:
                print(f"\n  Route {route_id} ({route_name}) - Pattern: '{pattern}':")
                for dest, count in dest_counts:
                    matches = matches_pattern(dest, pattern)
                    status = "✅" if matches else "⚠️"
                    print(f"    {status} {dest}: {count} departures")
            else:
                print(f"\n  Route {route_id} ({route_name}): No departures")
        
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during deletion: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    delete_incorrect_departures()
