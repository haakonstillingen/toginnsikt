# Business Intelligence Metrics for Train Delay Dashboard

## Overview
This document outlines the comprehensive business intelligence metrics that can be displayed on the train delay dashboard to provide valuable insights into service quality, reliability, and operational performance.

## Core Performance Metrics

### 1. **On-Time Performance (OTP)**
- **Definition**: Percentage of trains departing within 2 minutes of scheduled time
- **Calculation**: `(On-time departures / Total departures) × 100`
- **Target**: >90% (industry standard)
- **Display**: Primary KPI with trend indicators

### 2. **Delay Rate**
- **Definition**: Percentage of trains with any delay (>2 minutes)
- **Calculation**: `(Delayed departures / Total departures) × 100`
- **Categories**: 
  - Slight delays (3-15 minutes)
  - Severe delays (>15 minutes)
- **Display**: Primary KPI with trend indicators
- Comment: currenlty implemented through the 

### 3. **Cancellation Rate**
- **Definition**: Percentage of planned departures that were cancelled
- **Calculation**: `(Cancelled departures / Total departures) × 100`
- **Target**: <5% (industry standard)
- **Display**: Primary KPI with trend indicators. Red alert indicator when above threshold

### 4. **Average Delay**
- **Definition**: Mean delay time for all delayed trains
- **Calculation**: `Sum of delay minutes / Number of delayed trains`
- **Display**: Trend line with target benchmarks

### 5. **Maximum Delay**
- **Definition**: Longest single delay recorded
- **Display**: Peak delay indicator with timestamp

## Service Quality Classifications

### 6. **Service Reliability Score**
- **Definition**: Composite score based on on-time performance and cancellation rate
- **Calculation**: `(OTP × 0.7) + ((100 - Cancellation Rate) × 0.3)`
- **Scale**: 0-100 (100 = perfect service)
- **Display**: Gauge chart with color coding

### 7. **Severe Delay Rate**
- **Definition**: Percentage of trains with delays >15 minutes
- **Calculation**: `(Severely delayed departures / Total departures) × 100`
- **Target**: <2%
- **Display**: Warning indicator when above threshold

### 8. **Unknown Status Rate**
- **Definition**: Percentage of departures with unclear status
- **Calculation**: `(Unknown departures / Total departures) × 100`
- **Display**: Data quality indicator

## Time-Based Analysis

### 9. **Rush Hour Performance**
- **Definition**: Service quality during peak commute times (07:00-09:00, 16:00-18:00)
- **Metrics**: On-time rate, delay rate, cancellation rate
- **Display**: Comparison chart vs. off-peak performance

### 10. **Hourly Performance Patterns**
- **Definition**: Service quality breakdown by hour of day
- **Display**: Heatmap showing performance by time slot
- **Insights**: Identify problematic time periods

### 11. **Day-of-Week Analysis**
- **Definition**: Service quality comparison across weekdays
- **Display**: Bar chart showing performance by day
- **Insights**: Identify recurring issues on specific days

## Route-Specific Metrics

### 12. **Direction Performance Comparison**
- **Definition**: Service quality comparison between Myrvoll→Oslo S vs Oslo S→Myrvoll
- **Display**: Side-by-side comparison charts
- **Insights**: Identify direction-specific issues

### 13. **Destination Performance**
- **Definition**: Service quality by final destination (Stabekk, Lysaker, Ski)
- **Display**: Multi-series chart
- **Insights**: Route-specific reliability patterns

## Historical Trend Analysis

### 14. **7-Day Rolling Average**
- **Definition**: Moving average of key metrics over 7 days
- **Display**: Trend line with confidence intervals
- **Purpose**: Smooth out daily variations

### 15. **30-Day Performance Trend**
- **Definition**: Monthly performance comparison
- **Display**: Line chart with month-over-month change
- **Purpose**: Identify long-term trends

### 16. **Seasonal Analysis**
- **Definition**: Performance comparison across seasons
- **Display**: Seasonal calendar view
- **Purpose**: Weather and seasonal impact analysis

### 17. **Year-over-Year Comparison**
- **Definition**: Performance comparison with same period previous year
- **Display**: Comparative bar chart
- **Purpose**: Long-term improvement tracking

## Operational Insights

### 18. **Peak Delay Times**
- **Definition**: Most common delay durations
- **Display**: Histogram of delay distribution
- **Purpose**: Identify delay patterns

### 19. **Service Recovery Time**
- **Definition**: Time to return to normal service after disruptions
- **Display**: Timeline visualization
- **Purpose**: Operational resilience analysis

### 20. **Data Quality Score**
- **Definition**: Percentage of successful data collection
- **Calculation**: `(Successful collections / Total collection attempts) × 100`
- **Target**: >95%
- **Display**: System health indicator

## Advanced Analytics

### 21. **Predictive Delay Risk**
- **Definition**: Risk score for future delays based on historical patterns
- **Factors**: Time of day, day of week, weather, previous delays
- **Display**: Risk meter with color coding

### 22. **Service Disruption Clusters**
- **Definition**: Identification of recurring disruption patterns
- **Display**: Cluster analysis visualization
- **Purpose**: Root cause analysis

### 23. **Customer Impact Score**
- **Definition**: Weighted impact based on delay severity and passenger volume
- **Calculation**: `Sum of (Delay minutes × Passenger weight)`
- **Display**: Impact heatmap

## Dashboard Layout Recommendations

### **Primary Dashboard (Overview)**
1. **Top Row**: Key KPIs (On-time rate, Delay rate, Cancellation rate)
2. **Second Row**: Service reliability score gauge
3. **Third Row**: 24-hour performance chart
4. **Bottom Row**: Recent alerts and system status

### **Detailed Analysis View**
1. **Time-based Analysis**: Hourly and daily patterns
2. **Route Comparison**: Direction and destination analysis
3. **Historical Trends**: 7-day, 30-day, and seasonal views
4. **Operational Insights**: Data quality and system health

### **Mobile Dashboard**
1. **Essential Metrics**: On-time rate, delay rate, cancellation rate
2. **Quick Trends**: 7-day performance summary
3. **Alerts**: Current service disruptions

## Implementation Priority

### **Phase 1 (Immediate)**
- On-time performance rate
- Delay rate and average delay
- Cancellation rate
- Basic time-based analysis

### **Phase 2 (Short-term)**
- Service reliability score
- Route comparison metrics
- Historical trend analysis
- Data quality indicators

### **Phase 3 (Long-term)**
- Predictive analytics
- Advanced clustering
- Customer impact scoring
- Seasonal analysis

## Technical Implementation Notes

### **Data Sources**
- `actual_departures` table with business intelligence fields
- `departure_status` classifications (on_time, delayed, cancelled, severely_delayed, unknown)
- `expected_delay_minutes` for cancellation detection
- `classification_reason` for detailed analysis

### **API Endpoints**
- `/api/delays` - Core performance metrics
- `/api/classification` - Business intelligence metrics
- `/api/trends` - Historical analysis (to be implemented)
- `/api/health` - System status and data quality

### **Update Frequency**
- **Real-time**: Current day metrics
- **Hourly**: Trend analysis
- **Daily**: Historical comparisons
- **Weekly**: Seasonal analysis

---

*This document serves as the foundation for implementing comprehensive business intelligence metrics in the train delay dashboard, providing valuable insights for both operational management and passenger information.*
