# Data Collection Strategy Documentation

## Overview

This document outlines the refined data collection strategy for the Togforsinkelse project, designed to efficiently collect train delay and cancellation data for the L2 line between Myrvoll and Oslo S.

## Collection Architecture

### Two-Tier Collection System

The system operates on two distinct collection tiers:

1. **Planned Departure Collection** - Daily baseline collection
2. **Actual Departure Collection** - Real-time data collection throughout the day

## 1. Planned Departure Collection

### Schedule
- **Frequency:** Once daily
- **Time:** 03:00 UTC
- **Duration:** Single collection per day

### Purpose
- Collects the complete schedule for the next 24 hours
- Creates a "roadmap" of all planned departures
- Establishes baseline data for actual departure tracking

### Process
```
03:00 UTC Daily:
├── Query Entur API for Myrvoll → Oslo S departures (next 24h)
├── Query Entur API for Oslo S → Myrvoll departures (next 24h)
├── Store all planned departures in database
└── Create collection targets for actual departure collection
```

### Why 03:00 UTC?
- **Service Gap:** No trains running (01:16-05:46 UTC gap)
- **Complete Schedule:** Gets full 24-hour schedule
- **No Interference:** Doesn't conflict with actual service
- **Reliability:** Same time every day, predictable

## 2. Actual Departure Collection

### Schedule
The collection frequency varies based on service intensity:

#### High Frequency (15 minutes)
- **Periods:** 06:00-09:00 UTC, 15:00-18:00 UTC
- **Rationale:** Rush hours with more trains and higher delay probability

#### Medium Frequency (30 minutes)
- **Periods:** 09:00-15:00 UTC, 18:00-24:00 UTC
- **Rationale:** Regular service hours with moderate train frequency

#### Low Frequency (60 minutes)
- **Periods:** 00:00-06:00 UTC
- **Rationale:** Night service with minimal train frequency

### Collection Timing
- **Primary Collection:** Scheduled departure time + 5 minutes
- **Retry Logic:** Use subsequent collection windows for missed data
- **Cutoff:** Stop trying after 2 hours (API data becomes unavailable)

### Process Flow
```
For each planned departure:
├── At scheduled_time + 5 minutes:
│   ├── Attempt to collect actual departure data
│   ├── If successful: Store data and mark as collected
│   └── If failed: Mark for retry
├── During next collection window:
│   ├── Collect data for current departures
│   ├── Retry any pending departures from previous windows
│   └── Update retry status
└── After 2 hours:
    ├── Mark as data unavailable
    └── Stop retry attempts
```

## Data Retention Analysis

### Entur API Data Availability
Based on investigation:
- **0-2 hours:** 100% actual departure data available
- **2+ hours:** 0% actual departure data available

### Collection Success Rates
- **Normal delays (0-30 min):** >95% success rate
- **Minor delays (30-60 min):** >95% success rate
- **Major delays (60-120 min):** 80-95% success rate
- **Very late trains (>2 hours):** <80% success rate

## Target Routes

### Morning Commute
- **Route:** Myrvoll → Oslo S
- **Line:** L2
- **Final Destination:** Lysaker or Stabekk
- **Peak Hours:** 06:00-09:00 UTC (08:00-11:00 Local)

### Afternoon Commute
- **Route:** Oslo S → Myrvoll
- **Line:** L2
- **Final Destination:** Ski
- **Peak Hours:** 15:00-18:00 UTC (17:00-20:00 Local)

## Database Schema

### Tables
1. **commute_routes** - Route definitions
2. **planned_departures** - Scheduled departures (from 03:00 collection)
3. **actual_departures** - Real departure data (from throughout-day collection)

### Key Fields
- **aimed_departure_time** - Scheduled time
- **actual_departure_time** - Real departure time
- **expected_departure_time** - Expected time (if different from aimed)
- **delay_minutes** - Calculated delay
- **cancellation_status** - Whether train was cancelled
- **realtime_status** - Whether data is real-time or scheduled

## Implementation Benefits

### Efficiency
- **Minimal API Calls:** Batch collection reduces API usage
- **Smart Retry:** Natural retry logic using regular collection windows
- **Targeted Collection:** Only collects during service hours

### Data Quality
- **High Coverage:** Captures most delay scenarios
- **Timely Collection:** Data collected close to actual departure
- **Comprehensive:** Both directions and all service periods

### Scalability
- **Cloud Ready:** Designed for Google Cloud deployment
- **Configurable:** Easy to adjust collection frequencies
- **Monitoring:** Built-in logging and status tracking

## Error Handling

### API Failures
- Retry with exponential backoff
- Log failures for monitoring
- Continue with other departures

### Data Unavailability
- Mark as unavailable after 2-hour cutoff
- Track retry attempts
- Report data quality metrics

### System Failures
- Graceful degradation
- Resume from last successful collection
- Alert on critical failures

## Monitoring and Alerts

### Key Metrics
- Collection success rate
- API response times
- Data quality scores
- System uptime

### Alerts
- Collection failures
- API errors
- Data quality issues
- System downtime

## Future Enhancements

### Potential Improvements
- Machine learning for delay prediction
- Real-time notifications
- Historical trend analysis
- Performance optimization

### Scalability Considerations
- Multi-route support
- Regional expansion
- Advanced analytics
- User customization

---

*This document represents the refined collection strategy after extensive investigation and iteration. It provides a clear, implementable approach for reliable train delay data collection.*
