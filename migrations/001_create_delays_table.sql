-- Create delays table for PostgreSQL
CREATE TABLE IF NOT EXISTS delays (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    line_code VARCHAR(10) NOT NULL,
    direction VARCHAR(100) NOT NULL,
    delay_minutes INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_delays_timestamp ON delays(timestamp);
CREATE INDEX IF NOT EXISTS idx_delays_line_code ON delays(line_code);
CREATE INDEX IF NOT EXISTS idx_delays_direction ON delays(direction);
CREATE INDEX IF NOT EXISTS idx_delays_timestamp_line ON delays(timestamp, line_code);

-- Create a composite index for common queries
CREATE INDEX IF NOT EXISTS idx_delays_line_timestamp ON delays(line_code, timestamp);
