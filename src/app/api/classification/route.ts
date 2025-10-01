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
      routeFilter = "AND cr.direction = 'westbound'";
    } else if (route === 'oslo-ski') {
      routeFilter = "AND cr.direction = 'eastbound'";
    }
    
    // Get classification data - hourly for 1d, daily for 7d+
    let query;
    if (period === '1d') {
      // Hourly data for 24-hour view - converted to Norwegian local time
      query = `
        SELECT 
          TO_CHAR(ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:00:00') as time_period,
          COUNT(*) as total_departures,
          SUM(CASE WHEN ad.departure_status = 'on_time' THEN 1 ELSE 0 END) as on_time,
          SUM(CASE WHEN ad.departure_status = 'delayed' THEN 1 ELSE 0 END) as delayed,
          SUM(CASE WHEN ad.departure_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
          SUM(CASE WHEN ad.departure_status = 'severely_delayed' THEN 1 ELSE 0 END) as severely_delayed,
          SUM(CASE WHEN ad.departure_status = 'unknown' THEN 1 ELSE 0 END) as unknown
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE ad.actual_departure_time IS NOT NULL
          AND ad.actual_departure_time >= $1 
          AND ad.actual_departure_time <= $2
          AND EXTRACT(HOUR FROM ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo') >= 6
          AND EXTRACT(HOUR FROM ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo') <= 21
          ${routeFilter}
        GROUP BY TO_CHAR(ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD HH24:00:00')
        ORDER BY time_period
      `;
    } else {
      // Daily data for 7d, 30d, 90d views - converted to Norwegian local time
      query = `
        SELECT 
          TO_CHAR(ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD') as time_period,
          COUNT(*) as total_departures,
          SUM(CASE WHEN ad.departure_status = 'on_time' THEN 1 ELSE 0 END) as on_time,
          SUM(CASE WHEN ad.departure_status = 'delayed' THEN 1 ELSE 0 END) as delayed,
          SUM(CASE WHEN ad.departure_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
          SUM(CASE WHEN ad.departure_status = 'severely_delayed' THEN 1 ELSE 0 END) as severely_delayed,
          SUM(CASE WHEN ad.departure_status = 'unknown' THEN 1 ELSE 0 END) as unknown
        FROM actual_departures ad
        JOIN planned_departures pd ON ad.planned_departure_id = pd.id
        JOIN commute_routes cr ON pd.route_id = cr.id
        WHERE ad.actual_departure_time IS NOT NULL
          AND ad.actual_departure_time >= $1 
          AND ad.actual_departure_time <= $2
          AND EXTRACT(HOUR FROM ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo') >= 6
          AND EXTRACT(HOUR FROM ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo') <= 21
          ${routeFilter}
        GROUP BY TO_CHAR(ad.actual_departure_time::timestamp AT TIME ZONE 'Europe/Oslo', 'YYYY-MM-DD')
        ORDER BY time_period
      `;
    }
    
    const client = await pool.connect();
    const data = await client.query(query, [
      startDate.toISOString(),
      endDate.toISOString()
    ]);
    
    // Get summary classification stats
    const statsQuery = `
      SELECT 
        COUNT(*) as total_departures,
        SUM(CASE WHEN ad.departure_status = 'on_time' THEN 1 ELSE 0 END) as on_time,
        SUM(CASE WHEN ad.departure_status = 'delayed' THEN 1 ELSE 0 END) as delayed,
        SUM(CASE WHEN ad.departure_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
        SUM(CASE WHEN ad.departure_status = 'severely_delayed' THEN 1 ELSE 0 END) as severely_delayed,
        SUM(CASE WHEN ad.departure_status = 'unknown' THEN 1 ELSE 0 END) as unknown
      FROM actual_departures ad
      JOIN planned_departures pd ON ad.planned_departure_id = pd.id
      JOIN commute_routes cr ON pd.route_id = cr.id
      WHERE ad.actual_departure_time IS NOT NULL
        AND ad.actual_departure_time >= $1 
        AND ad.actual_departure_time <= $2
        AND EXTRACT(HOUR FROM ad.actual_departure_time::timestamp) >= 6
        AND EXTRACT(HOUR FROM ad.actual_departure_time::timestamp) <= 21
        ${routeFilter}
    `;
    
    const stats = await client.query(statsQuery, [
      startDate.toISOString(),
      endDate.toISOString()
    ]);
    
    client.release();
    
    // Calculate percentages for each time period
    const processedData = data.rows.map(row => {
      const total = parseInt(row.total_departures);
      const onTime = parseInt(row.on_time);
      const delayed = parseInt(row.delayed);
      const cancelled = parseInt(row.cancelled);
      const severelyDelayed = parseInt(row.severely_delayed);
      const unknown = parseInt(row.unknown);
      
      return {
        timePeriod: row.time_period,
        totalDepartures: total,
        onTime: onTime,
        delayed: delayed,
        cancelled: cancelled,
        severelyDelayed: severelyDelayed,
        unknown: unknown,
        // Percentages
        onTimePercentage: total > 0 ? Math.round((onTime / total) * 100 * 10) / 10 : 0,
        delayedPercentage: total > 0 ? Math.round((delayed / total) * 100 * 10) / 10 : 0,
        cancelledPercentage: total > 0 ? Math.round((cancelled / total) * 100 * 10) / 10 : 0,
        severelyDelayedPercentage: total > 0 ? Math.round((severelyDelayed / total) * 100 * 10) / 10 : 0,
        unknownPercentage: total > 0 ? Math.round((unknown / total) * 100 * 10) / 10 : 0
      };
    });
    
    // Calculate summary percentages
    const summaryTotal = parseInt(stats.rows[0].total_departures);
    const summaryOnTime = parseInt(stats.rows[0].on_time);
    const summaryDelayed = parseInt(stats.rows[0].delayed);
    const summaryCancelled = parseInt(stats.rows[0].cancelled);
    const summarySeverelyDelayed = parseInt(stats.rows[0].severely_delayed);
    const summaryUnknown = parseInt(stats.rows[0].unknown);
    
    return NextResponse.json({
      data: processedData,
      summary: {
        totalDepartures: summaryTotal,
        onTime: summaryOnTime,
        delayed: summaryDelayed,
        cancelled: summaryCancelled,
        severelyDelayed: summarySeverelyDelayed,
        unknown: summaryUnknown,
        // Summary percentages
        onTimePercentage: summaryTotal > 0 ? Math.round((summaryOnTime / summaryTotal) * 100 * 10) / 10 : 0,
        delayedPercentage: summaryTotal > 0 ? Math.round((summaryDelayed / summaryTotal) * 100 * 10) / 10 : 0,
        cancelledPercentage: summaryTotal > 0 ? Math.round((summaryCancelled / summaryTotal) * 100 * 10) / 10 : 0,
        severelyDelayedPercentage: summaryTotal > 0 ? Math.round((summarySeverelyDelayed / summaryTotal) * 100 * 10) / 10 : 0,
        unknownPercentage: summaryTotal > 0 ? Math.round((summaryUnknown / summaryTotal) * 100 * 10) / 10 : 0
      },
      period: period,
      route: route,
      dateRange: {
        start: startDate.toISOString(),
        end: endDate.toISOString()
      }
    });
    
  } catch (error) {
    console.error('Database error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch classification data' },
      { status: 500 }
    );
  }
}
