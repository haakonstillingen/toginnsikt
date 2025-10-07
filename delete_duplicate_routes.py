#!/usr/bin/env python3
"""
Delete duplicate routes from the database
Routes to delete: 9557 (Morning Commute with empty pattern) and 9558 (Afternoon Commute duplicate)
Keep: Routes 1 and 2 (the correct ones)
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

def delete_duplicate_routes():
    """Delete duplicate routes 9557 and 9558"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 100)
    print("DELETE DUPLICATE ROUTES")
    print("=" * 100)
    print()
    
    # First, show all routes
    print("CURRENT ROUTES IN DATABASE:")
    print("-" * 100)
    cur.execute("""
        SELECT id, route_name, source_station_name, target_station_name, 
               final_destination_pattern, direction
        FROM commute_routes
        ORDER BY id;
    """)
    
    for row in cur.fetchall():
        id, name, source, target, pattern, direction = row
        pattern_str = f"'{pattern}'" if pattern else "EMPTY"
        print(f"  [{id}] {name}: {source} → {target}")
        print(f"      Pattern: {pattern_str}, Direction: {direction}")
    
    print()
    
    # Show impact of deletion
    print("IMPACT ANALYSIS:")
    print("-" * 100)
    
    duplicate_ids = [9557, 9558]
    
    for route_id in duplicate_ids:
        # Check route details
        cur.execute("""
            SELECT route_name, final_destination_pattern
            FROM commute_routes
            WHERE id = %s;
        """, (route_id,))
        
        route_info = cur.fetchone()
        if not route_info:
            print(f"  Route {route_id}: NOT FOUND (already deleted?)")
            continue
            
        route_name, pattern = route_info
        pattern_str = f"'{pattern}'" if pattern else "EMPTY"
        
        # Count planned departures
        cur.execute("""
            SELECT COUNT(*) 
            FROM planned_departures 
            WHERE route_id = %s;
        """, (route_id,))
        planned_count = cur.fetchone()[0]
        
        # Count actual departures (via planned departures)
        cur.execute("""
            SELECT COUNT(DISTINCT ad.id)
            FROM actual_departures ad
            JOIN planned_departures pd ON ad.planned_departure_id = pd.id
            WHERE pd.route_id = %s;
        """, (route_id,))
        actual_count = cur.fetchone()[0]
        
        print(f"\n  Route {route_id}: {route_name} (Pattern: {pattern_str})")
        print(f"    - Planned departures: {planned_count}")
        print(f"    - Actual departures: {actual_count}")
    
    print()
    print("=" * 100)
    print("DELETION PLAN:")
    print("=" * 100)
    print(f"  Will DELETE routes: {duplicate_ids}")
    print(f"  Will KEEP routes: [1, 2]")
    print()
    print("  This will CASCADE DELETE:")
    print("    - All planned_departures linked to routes 9557 and 9558")
    print("    - All actual_departures linked to those planned_departures")
    print()
    
    # Ask for confirmation (can be skipped with --yes flag)
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
    print("Deleting duplicate routes...")
    
    try:
        # Delete routes (CASCADE should handle related records)
        for route_id in duplicate_ids:
            cur.execute("DELETE FROM commute_routes WHERE id = %s;", (route_id,))
            print(f"  ✓ Deleted route {route_id}")
        
        # Also delete planned/actual departures if CASCADE didn't work
        for route_id in duplicate_ids:
            # Delete actual departures first
            cur.execute("""
                DELETE FROM actual_departures
                WHERE planned_departure_id IN (
                    SELECT id FROM planned_departures WHERE route_id = %s
                );
            """, (route_id,))
            
            # Then delete planned departures
            cur.execute("DELETE FROM planned_departures WHERE route_id = %s;", (route_id,))
        
        conn.commit()
        
        print()
        print("=" * 100)
        print("✅ DELETION COMPLETE!")
        print("=" * 100)
        print()
        
        # Show final state
        print("REMAINING ROUTES:")
        print("-" * 100)
        cur.execute("""
            SELECT id, route_name, source_station_name, target_station_name, 
                   final_destination_pattern, direction
            FROM commute_routes
            ORDER BY id;
        """)
        
        for row in cur.fetchall():
            id, name, source, target, pattern, direction = row
            print(f"  [{id}] {name}: {source} → {target}")
            print(f"      Pattern: '{pattern}', Direction: {direction}")
        
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR during deletion: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    delete_duplicate_routes()
