import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// Cloud SQL PostgreSQL connection
const pool = new Pool({
  host: '35.228.203.238',
  port: 5432,
  database: 'togforsinkelse_enhanced',
  user: 'togforsinkelse-user',
  password: 'fPl21YN#cF0RngM9',
  ssl: { rejectUnauthorized: false }
});

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || '7d';
    const route = searchParams.get('route') || 'all';
    const selectedDate = searchParams.get('date');
    
    // Calculate date range based on period
    const now = new Date();
    let startDate: Date;
    let endDate: Date = now;
    
    switch (period) {
      case '1d':
        // Last 24 hours: use selected date or current date
        if (selectedDate) {
          const targetDate = new Date(selectedDate);
          // Set to 06:00 of the selected date
          targetDate.setHours(6, 0, 0, 0);
          startDate = targetDate;
          endDate = new Date(targetDate.getTime() + 24 * 60 * 60 * 1000);
        } else {
          // Default: 06:00 of current day to 06:00 of next day
          const today = new Date(now);
          today.setHours(6, 0, 0, 0);
          startDate = today;
          endDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
        }
        break;
      case '7d':
        // Last 7 days: current day and 6 days before
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        // Last 30 days: current day and 29 days before
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '90d':
        // Last 90 days: current day and 89 days before
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    }
    
    // Build route filter
    let routeFilter = '';
    if (route === 'myrvoll-oslo') {
      routeFilter = "AND cr.direction = 'morning'";
    } else if (route === 'oslo-ski') {
      routeFilter = "AND cr.direction = 'afternoon'";
    }
    
    // Get aggregated data with business intelligence metrics - hourly for 1d, daily for 7d+
    let query;
    if (period === '1d') {
      // Hourly data for 24-hour view with classification metrics
      query = `
        SELECT 
          TO_CHAR(pd.planned_departure_time::timestamp, 'YYYY-MM-DD HH24:00:00') as hour,
          COUNT(*) as total_departures,
          SUM(CASE WHEN ad.delay_minutes > 0 THEN 1 ELSE 0 END) as delayed_departures,
          AVG(CASE WHEN ad.delay_minutes > 0 THEN ad.delay_minutes END) as avg_delay,
          MAX(ad.delay_minutes) as max_delay,
          -- Business Intelligence Metrics
          SUM(CASE WHEN ad.departure_status = 'on_time' THEN 1 ELSE 0 END) as on_time_departures,
          SUM(CASE WHEN ad.departure_status = 'delayed' THEN 1 ELSE 0 END) as delayed_classified,
          SUM(CASE WHEN ad.departure_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_departures,
          SUM(CASE WHEN ad.departure_status = 'severely_delayed' THEN 1 ELSE 0 END) as severely_delayed,
          SUM(CASE WHEN ad.departure_status = 'unknown' THEN 1 ELSE 0 END) as unknown_departures
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE pd.planned_departure_time >= $1 
          AND pd.planned_departure_time <= $2
          AND EXTRACT(HOUR FROM pd.planned_departure_time::timestamp) >= 6
          AND EXTRACT(HOUR FROM pd.planned_departure_time::timestamp) <= 21
          ${routeFilter}
        GROUP BY TO_CHAR(pd.planned_departure_time::timestamp, 'YYYY-MM-DD HH24:00:00')
        ORDER BY hour
      `;
    } else {
      // Daily data for 7d, 30d, 90d views with classification metrics
      query = `
        SELECT 
          TO_CHAR(pd.planned_departure_time::timestamp, 'YYYY-MM-DD') as hour,
          COUNT(*) as total_departures,
          SUM(CASE WHEN ad.delay_minutes > 0 THEN 1 ELSE 0 END) as delayed_departures,
          AVG(CASE WHEN ad.delay_minutes > 0 THEN ad.delay_minutes END) as avg_delay,
          MAX(ad.delay_minutes) as max_delay,
          -- Business Intelligence Metrics
          SUM(CASE WHEN ad.departure_status = 'on_time' THEN 1 ELSE 0 END) as on_time_departures,
          SUM(CASE WHEN ad.departure_status = 'delayed' THEN 1 ELSE 0 END) as delayed_classified,
          SUM(CASE WHEN ad.departure_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_departures,
          SUM(CASE WHEN ad.departure_status = 'severely_delayed' THEN 1 ELSE 0 END) as severely_delayed,
          SUM(CASE WHEN ad.departure_status = 'unknown' THEN 1 ELSE 0 END) as unknown_departures
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE pd.planned_departure_time >= $1 
          AND pd.planned_departure_time <= $2
          AND EXTRACT(HOUR FROM pd.planned_departure_time::timestamp) >= 6
          AND EXTRACT(HOUR FROM pd.planned_departure_time::timestamp) <= 21
          ${routeFilter}
        GROUP BY TO_CHAR(pd.planned_departure_time::timestamp, 'YYYY-MM-DD')
        ORDER BY hour
      `;
    }
    
    const client = await pool.connect();
    const data = await client.query(query, [
      startDate.toISOString(),
      endDate.toISOString()
    ]);
    
    // Get summary stats with business intelligence metrics, focusing on morning and after-work hours (06:00-21:00)
    const statsQuery = `
      SELECT 
        COUNT(*) as total_departures,
        SUM(CASE WHEN ad.delay_minutes > 0 THEN 1 ELSE 0 END) as delayed_departures,
        AVG(CASE WHEN ad.delay_minutes > 0 THEN ad.delay_minutes ELSE 0 END) as avg_delay,
        -- Business Intelligence Summary Metrics
        SUM(CASE WHEN ad.departure_status = 'on_time' THEN 1 ELSE 0 END) as on_time_departures,
        SUM(CASE WHEN ad.departure_status = 'delayed' THEN 1 ELSE 0 END) as delayed_classified,
        SUM(CASE WHEN ad.departure_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_departures,
        SUM(CASE WHEN ad.departure_status = 'severely_delayed' THEN 1 ELSE 0 END) as severely_delayed,
        SUM(CASE WHEN ad.departure_status = 'unknown' THEN 1 ELSE 0 END) as unknown_departures
      FROM actual_departures ad
      JOIN planned_departures pd ON ad.planned_departure_id = pd.id
      JOIN commute_routes cr ON pd.route_id = cr.id
      WHERE pd.planned_departure_time >= $1 
        AND pd.planned_departure_time <= $2
        AND EXTRACT(HOUR FROM pd.planned_departure_time::timestamp) >= 6
        AND EXTRACT(HOUR FROM pd.planned_departure_time::timestamp) <= 21
        ${routeFilter}
    `;
    
    const stats = await client.query(statsQuery, [
      startDate.toISOString(),
      endDate.toISOString()
    ]);
    
    client.release();
    
    return NextResponse.json({
      data: data.rows.map(row => ({
        hour: row.hour,
        totalDepartures: parseInt(row.total_departures),
        delayedDepartures: parseInt(row.delayed_departures),
        avgDelay: Math.round(parseFloat(row.avg_delay) * 10) / 10,
        maxDelay: parseInt(row.max_delay),
        delayPercentage: Math.round((parseInt(row.delayed_departures) / parseInt(row.total_departures)) * 100 * 10) / 10,
        // Business Intelligence Metrics
        onTimeDepartures: parseInt(row.on_time_departures),
        delayedClassified: parseInt(row.delayed_classified),
        cancelledDepartures: parseInt(row.cancelled_departures),
        severelyDelayed: parseInt(row.severely_delayed),
        unknownDepartures: parseInt(row.unknown_departures),
        // Calculated percentages
        onTimePercentage: Math.round((parseInt(row.on_time_departures) / parseInt(row.total_departures)) * 100 * 10) / 10,
        cancelledPercentage: Math.round((parseInt(row.cancelled_departures) / parseInt(row.total_departures)) * 100 * 10) / 10,
        severelyDelayedPercentage: Math.round((parseInt(row.severely_delayed) / parseInt(row.total_departures)) * 100 * 10) / 10
      })),
      stats: {
        totalDepartures: parseInt(stats.rows[0].total_departures),
        delayedDepartures: parseInt(stats.rows[0].delayed_departures),
        avgDelay: Math.round(parseFloat(stats.rows[0].avg_delay) * 10) / 10,
        delayPercentage: Math.round((parseInt(stats.rows[0].delayed_departures) / parseInt(stats.rows[0].total_departures)) * 100 * 10) / 10,
        // Business Intelligence Summary
        onTimeDepartures: parseInt(stats.rows[0].on_time_departures),
        delayedClassified: parseInt(stats.rows[0].delayed_classified),
        cancelledDepartures: parseInt(stats.rows[0].cancelled_departures),
        severelyDelayed: parseInt(stats.rows[0].severely_delayed),
        unknownDepartures: parseInt(stats.rows[0].unknown_departures),
        // Calculated summary percentages
        onTimePercentage: Math.round((parseInt(stats.rows[0].on_time_departures) / parseInt(stats.rows[0].total_departures)) * 100 * 10) / 10,
        cancelledPercentage: Math.round((parseInt(stats.rows[0].cancelled_departures) / parseInt(stats.rows[0].total_departures)) * 100 * 10) / 10,
        severelyDelayedPercentage: Math.round((parseInt(stats.rows[0].severely_delayed) / parseInt(stats.rows[0].total_departures)) * 100 * 10) / 10
      }
    });
    
  } catch (error) {
    console.error('Database error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch delay data' },
      { status: 500 }
    );
  }
}