#!/usr/bin/env python3
"""
Check database schema
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

def check_schema():
    """Check the database schema"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 100)
    print("DATABASE SCHEMA INVESTIGATION")
    print("=" * 100)
    print()
    
    # Get all tables
    print("📋 TABLES IN DATABASE:")
    print("-" * 100)
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    tables = [row[0] for row in cur.fetchall()]
    for table in tables:
        print(f"  - {table}")
    print()
    
    # Get columns for each table
    for table in tables:
        print(f"📊 COLUMNS IN '{table}':")
        print("-" * 100)
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table,))
        
        for row in cur.fetchall():
            col_name, data_type, nullable = row
            null_str = "NULL" if nullable == "YES" else "NOT NULL"
            print(f"  {col_name:<30} {data_type:<20} {null_str}")
        print()
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"  Total rows: {count}")
        print()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_schema()
