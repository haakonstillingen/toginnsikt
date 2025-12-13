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
    // Use PostgreSQL's timezone() function to construct date range in Europe/Oslo timezone
    // This properly handles DST (UTC+1 in winter, UTC+2 in summer)
    // When no date is provided, use PostgreSQL to get current date in Europe/Oslo timezone
    let query: string;
    let queryParams: string[];
    
    if (selectedDate) {
      // Use the selected date string directly - PostgreSQL will handle timezone conversion
      query = `
        SELECT 
          pd.line_code,
          TO_CHAR(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS') as planned_time,
          TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS') as actual_time,
          ad.delay_minutes,
          ad.is_cancelled
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE ad.actual_departure_time >= timezone('Europe/Oslo', $1::date)::timestamptz
          AND ad.actual_departure_time < timezone('Europe/Oslo', $1::date + interval '1 day')::timestamptz
          ${routeFilter}
        ORDER BY pd.planned_departure_time
      `;
      queryParams = [selectedDate];
    } else {
      // Use PostgreSQL to get current date in Europe/Oslo timezone
      // This ensures we query the correct day regardless of server timezone
      query = `
        SELECT 
          pd.line_code,
          TO_CHAR(pd.planned_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS') as planned_time,
          TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS') as actual_time,
          ad.delay_minutes,
          ad.is_cancelled
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE ad.actual_departure_time >= timezone('Europe/Oslo', (NOW() AT TIME ZONE 'Europe/Oslo')::date)::timestamptz
          AND ad.actual_departure_time < timezone('Europe/Oslo', (NOW() AT TIME ZONE 'Europe/Oslo')::date + interval '1 day')::timestamptz
          ${routeFilter}
        ORDER BY pd.planned_departure_time
      `;
      queryParams = [];
    }
    
    const client = await pool.connect();
    let result;
    let currentDateStr: string | undefined;
    
    try {
      // If no date provided, get current date in Europe/Oslo timezone first
      if (!selectedDate) {
        const dateQuery = `SELECT (NOW() AT TIME ZONE 'Europe/Oslo')::date as current_date`;
        const dateResult = await client.query(dateQuery);
        currentDateStr = dateResult.rows[0].current_date.toISOString().split('T')[0];
      }
      
      result = await client.query(query, queryParams);
    } finally {
      // Always release the connection, even if query fails
      client.release();
    }
    
    // Process data to format for frontend
    const departures = result.rows.map(row => ({
      lineCode: row.line_code,
      plannedTime: row.planned_time,
      actualTime: row.actual_time || null,
      delayMinutes: row.delay_minutes || 0,
      isCancelled: row.is_cancelled || false,
    }));
    
    // Calculate date range for response
    let dateRangeStart: string;
    let dateRangeEnd: string;
    
    if (selectedDate) {
      dateRangeStart = `${selectedDate}T00:00:00+01:00`; // Approximate for response
      dateRangeEnd = new Date(new Date(dateRangeStart).getTime() + 24 * 60 * 60 * 1000).toISOString();
    } else {
      // Use the date we got from PostgreSQL
      dateRangeStart = `${currentDateStr}T00:00:00+01:00`; // Approximate for response
      dateRangeEnd = new Date(new Date(dateRangeStart).getTime() + 24 * 60 * 60 * 1000).toISOString();
    }
    
    return NextResponse.json({
      departures,
      count: departures.length,
      period,
      route,
      dateRange: {
        start: dateRangeStart,
        end: dateRangeEnd
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
