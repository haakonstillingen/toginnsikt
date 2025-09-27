-- Create commute routes table for tracking specific commuting patterns
CREATE TABLE IF NOT EXISTS commute_routes (
    id SERIAL PRIMARY KEY,
    route_name VARCHAR(50) NOT NULL,
    source_station_id VARCHAR(50) NOT NULL,
    source_station_name VARCHAR(100) NOT NULL,
    target_station_id VARCHAR(50) NOT NULL,
    target_station_name VARCHAR(100) NOT NULL,
    final_destination_pattern VARCHAR(200) NOT NULL,
    direction VARCHAR(20) NOT NULL, -- 'morning' or 'afternoon'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create planned departures table
CREATE TABLE IF NOT EXISTS planned_departures (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES commute_routes(id),
    planned_departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
    service_journey_id VARCHAR(100),
    line_code VARCHAR(10) NOT NULL,
    final_destination VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create actual departures table
CREATE TABLE IF NOT EXISTS actual_departures (
    id SERIAL PRIMARY KEY,
    planned_departure_id INTEGER REFERENCES planned_departures(id),
    actual_departure_time TIMESTAMP WITH TIME ZONE,
    delay_minutes INTEGER DEFAULT 0,
    is_cancelled BOOLEAN DEFAULT FALSE,
    is_realtime BOOLEAN DEFAULT TRUE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commute_routes_direction ON commute_routes(direction);
CREATE INDEX IF NOT EXISTS idx_planned_departures_route_time ON planned_departures(route_id, planned_departure_time);
CREATE INDEX IF NOT EXISTS idx_actual_departures_planned ON actual_departures(planned_departure_id);
CREATE INDEX IF NOT EXISTS idx_actual_departures_collected ON actual_departures(collected_at);

-- Insert the two specific commute routes
INSERT INTO commute_routes (route_name, source_station_id, source_station_name, target_station_id, target_station_name, final_destination_pattern, direction) VALUES
('Morning Commute', 'NSR:StopPlace:59638', 'Myrvoll', 'NSR:StopPlace:337', 'Oslo S', '', 'morning'),
('Afternoon Commute', 'NSR:StopPlace:337', 'Oslo S', 'NSR:StopPlace:59638', 'Myrvoll', 'Ski', 'afternoon');
