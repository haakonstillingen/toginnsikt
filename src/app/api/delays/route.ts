import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  ssl: { rejectUnauthorized: false }
});

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || '1d';
    const route = searchParams.get('route') || '';
    const selectedDate = searchParams.get('date');
    
    const now = new Date();
    let startDate: Date;
    let endDate: Date;
    
    switch (period) {
      case '1d':
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
        break;
      case '7d':
        // Last 7 days
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        endDate = now;
        break;
      case '30d':
        // Last 30 days
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        endDate = now;
        break;
      case '90d':
        // Last 90 days
        startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        endDate = now;
        break;
      default:
        return NextResponse.json({ error: 'Invalid period' }, { status: 400 });
    }
    
    // Build route filter
    let routeFilter = '';
    if (route) {
      if (route === 'myrvoll-oslo') {
        routeFilter = "AND cr.direction = 'westbound'";
      } else if (route === 'oslo-myrvoll') {
        routeFilter = "AND cr.direction = 'eastbound'";
      }
    }
    
    let query;
    if (period === '1d') {
      // Hourly data for 24-hour view with classification metrics - converted to Norwegian local time
      query = `
        SELECT 
          TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:00:00') as hour,
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
        WHERE ad.actual_departure_time >= $1 
          AND ad.actual_departure_time <= $2
          ${routeFilter}
        GROUP BY TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:00:00')
        ORDER BY hour
      `;
    } else {
      // Daily data for 7d, 30d, 90d views with classification metrics - converted to Norwegian local time
      query = `
        SELECT 
          TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD') as hour,
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
        WHERE ad.actual_departure_time >= $1 
          AND ad.actual_departure_time <= $2
          ${routeFilter}
        GROUP BY TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD')
        ORDER BY hour
      `;
    }
    
    const client = await pool.connect();
    const data = await client.query(query, [
      startDate.toISOString(),
      endDate.toISOString()
    ]);
    
    // Get actual time range for the selected day (first and last departure)
    let actualTimeRange = null;
    if (period === '1d' && data.rows.length > 0) {
      const timeRangeQuery = `
        SELECT 
          MIN(TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS')) as first_departure,
          MAX(TO_CHAR(ad.actual_departure_time AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:MI:SS')) as last_departure
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE ad.actual_departure_time >= $1 
          AND ad.actual_departure_time <= $2
          ${routeFilter}
      `;
      const timeRangeResult = await client.query(timeRangeQuery, [
        startDate.toISOString(),
        endDate.toISOString()
      ]);
      actualTimeRange = timeRangeResult.rows[0];
    }
    
    // Get summary stats with business intelligence metrics for all collected departures
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
      WHERE ad.actual_departure_time >= $1 
        AND ad.actual_departure_time <= $2
        ${routeFilter}
    `;
    
    const stats = await client.query(statsQuery, [
      startDate.toISOString(),
      endDate.toISOString()
    ]);
    
    client.release();
    
    // Process data to add calculated fields
    const processedData = data.rows.map(row => {
      const totalDepartures = parseInt(row.total_departures);
      const delayedDepartures = parseInt(row.delayed_departures);
      const onTimeDepartures = parseInt(row.on_time_departures);
      const delayedClassified = parseInt(row.delayed_classified);
      const cancelledDepartures = parseInt(row.cancelled_departures);
      const severelyDelayed = parseInt(row.severely_delayed);
      const unknownDepartures = parseInt(row.unknown_departures);
      
      return {
        hour: row.hour,
        totalDepartures,
        delayedDepartures,
        avgDelay: row.avg_delay ? parseFloat(row.avg_delay) : null,
        maxDelay: parseInt(row.max_delay),
        delayPercentage: totalDepartures > 0 ? Math.round((delayedDepartures / totalDepartures) * 100) : 0,
        onTimeDepartures,
        delayedClassified,
        cancelledDepartures,
        severelyDelayed,
        unknownDepartures,
        onTimePercentage: totalDepartures > 0 ? Math.round((onTimeDepartures / totalDepartures) * 100) : 0,
        cancelledPercentage: totalDepartures > 0 ? Math.round((cancelledDepartures / totalDepartures) * 100) : 0,
        severelyDelayedPercentage: totalDepartures > 0 ? Math.round((severelyDelayed / totalDepartures) * 100) : 0
      };
    });
    
    // Process stats
    const statsRow = stats.rows[0];
    const totalDepartures = parseInt(statsRow.total_departures);
    const delayedDepartures = parseInt(statsRow.delayed_departures);
    const onTimeDepartures = parseInt(statsRow.on_time_departures);
    const delayedClassified = parseInt(statsRow.delayed_classified);
    const cancelledDepartures = parseInt(statsRow.cancelled_departures);
    const severelyDelayed = parseInt(statsRow.severely_delayed);
    const unknownDepartures = parseInt(statsRow.unknown_departures);
    
    const summary = {
      totalDepartures,
      delayedDepartures,
      avgDelay: statsRow.avg_delay ? parseFloat(statsRow.avg_delay) : null,
      delayPercentage: totalDepartures > 0 ? Math.round((delayedDepartures / totalDepartures) * 100) : 0,
      onTimeDepartures,
      delayedClassified,
      cancelledDepartures,
      severelyDelayed,
      unknownDepartures,
      onTimePercentage: totalDepartures > 0 ? Math.round((onTimeDepartures / totalDepartures) * 100) : 0,
      cancelledPercentage: totalDepartures > 0 ? Math.round((cancelledDepartures / totalDepartures) * 100) : 0,
      severelyDelayedPercentage: totalDepartures > 0 ? Math.round((severelyDelayed / totalDepartures) * 100) : 0
    };
    
    return NextResponse.json({
      data: processedData,
      summary,
      actualTimeRange,
      period,
      route,
      dateRange: {
        start: startDate.toISOString(),
        end: endDate.toISOString()
      }
    });
    
  } catch (error) {
    console.error('Database error:', error);
    console.error('Error details:', error.message);
    console.error('Stack trace:', error.stack);
    return NextResponse.json(
      { error: 'Failed to fetch delay data', details: error.message },
      { status: 500 }
    );
  }
}