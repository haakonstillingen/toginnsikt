import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// Validate required environment variables
const requiredEnvVars = {
  DB_HOST: process.env.DB_HOST,
  DB_PORT: process.env.DB_PORT,
  DB_NAME: process.env.DB_NAME,
  DB_USER: process.env.DB_USER,
  DB_PASSWORD: process.env.DB_PASSWORD,
};

// Check for missing environment variables
const missingVars = Object.entries(requiredEnvVars)
  .filter(([_, value]) => !value)
  .map(([key]) => key);

if (missingVars.length > 0) {
  console.error('Missing environment variables:', missingVars);
  throw new Error(
    `Missing required environment variables: ${missingVars.join(', ')}`
  );
}

const pool = new Pool({
  host: process.env.DB_HOST!,
  port: parseInt(process.env.DB_PORT || '5432', 10),
  database: process.env.DB_NAME!,
  user: process.env.DB_USER!,
  password: process.env.DB_PASSWORD!,
  ssl: { rejectUnauthorized: false }
});

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || '1d';
    const route = searchParams.get('route') || '';
    const selectedDate = searchParams.get('date');
    
    // Only support 1d period for individual departures
    if (period !== '1d') {
      return NextResponse.json({ error: 'Only 1d period is supported for individual departures' }, { status: 400 });
    }
    
    const now = new Date();
    let startDate: Date;
    let endDate: Date;
    
    // Last 24 hours: use selected date or current date
    if (selectedDate) {
      const targetDate = new Date(selectedDate);
      // Set to 00:00 of the selected date to capture all departures
      targetDate.setHours(0, 0, 0, 0);
      startDate = targetDate;
      endDate = new Date(targetDate.getTime() + 24 * 60 * 60 * 1000);
    } else {
      // Default: 00:00 of current day to 00:00 of next day to capture all departures
      const today = new Date(now);
      today.setHours(0, 0, 0, 0);
      startDate = today;
      endDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
    }
    
    // Build route filter
    let routeFilter = '';
    if (route) {
      if (route === 'myrvoll-oslo') {
        routeFilter = "AND cr.direction = 'westbound'";
      } else if (route === 'oslo-ski') {
        routeFilter = "AND cr.direction = 'eastbound'";
      }
    }
    
    // Query individual departures with all required fields
    const query = `
      SELECT 
        pd.line_code,
        TO_CHAR(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS') as planned_time,
        TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS') as actual_time,
        ad.delay_minutes,
        ad.is_cancelled
      FROM actual_departures ad
      JOIN planned_departures pd ON ad.planned_departure_id = pd.id
      JOIN commute_routes cr ON pd.route_id = cr.id
      WHERE ad.actual_departure_time >= $1 
        AND ad.actual_departure_time < $2
        ${routeFilter}
      ORDER BY pd.planned_departure_time
    `;
    
    const client = await pool.connect();
    const result = await client.query(query, [
      startDate.toISOString(),
      endDate.toISOString()
    ]);
    
    client.release();
    
    // Process data to format for frontend
    const departures = result.rows.map(row => ({
      lineCode: row.line_code,
      plannedTime: row.planned_time,
      actualTime: row.actual_time || null,
      delayMinutes: row.delay_minutes || 0,
      isCancelled: row.is_cancelled || false,
    }));
    
    return NextResponse.json({
      departures,
      count: departures.length,
      period,
      route,
      dateRange: {
        start: startDate.toISOString(),
        end: endDate.toISOString()
      }
    });
    
  } catch (error) {
    console.error('Database error:', error);
    console.error('Error details:', error instanceof Error ? error.message : String(error));
    return NextResponse.json(
      { error: 'Failed to fetch departure data', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
