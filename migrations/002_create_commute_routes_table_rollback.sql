-- Rollback script for migration 002_create_commute_routes_table.sql
-- WARNING: This will permanently delete all data in the commute-related tables

-- Drop indexes first
DROP INDEX IF EXISTS idx_commute_routes_direction;
DROP INDEX IF EXISTS idx_planned_departures_route_time;
DROP INDEX IF EXISTS idx_actual_departures_planned;
DROP INDEX IF EXISTS idx_actual_departures_collected;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS actual_departures;
DROP TABLE IF EXISTS planned_departures;
DROP TABLE IF EXISTS commute_routes;
