#!/usr/bin/env python3
"""
Query ALL departures from Oslo S to Myrvoll for the entire Monday (24 hours)
"""

import requests
import json
from datetime import datetime, timezone, timedelta

def st to tion():
    """Query all departures from Oslo S to Myrvoll for the entire Monday"""
    
    base_url = "https://api.entur.io/journey-planner/v3/graphql"
    headers = {
        'Content-Type': 'application/json',
        'ET-Client-Name': 'togforsinkelse-monday-oslo-myrvoll-full'
    }
    
    oslo_id = "NSR:StopPlace:337"  # Oslo S
    
    def make_request(query, variables):
        """Make GraphQL request"""
        payload = {"query": query, "variables": variables}
        response = requests.post(base_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_departures(station_id, start_time):
        """Get all departures from a specific station"""
        query = """
            query($id: String!, $startTime: DateTime!, $numberOfDepartures: Int!) {
                stopPlace(id: $id) {
                    id
                    name
                    estimatedCalls(
                        numberOfDepartures: $numberOfDepartures,
                        startTime: $startTime,
                        timeRange: 86400
                    ) {
                        aimedDepartureTime
                        expectedDepartureTime
                        actualDepartureTime
                        realtime
                        cancellation
                        serviceJourney {
                            id
                            line {
                                publicCode
                                name
                                id
                            }
                            transportMode
                        }
                        destinationDisplay {
                            frontText
                        }
                        quay {
                            id
                            name
                        }
                    }
                }
            }
        """
        
        variables = {
            "id": station_id,
            "startTime": start_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
            "numberOfDepartures": 1000  # Increased to get more departures
        }
        
        response = make_request(query, variables)
        if 'errors' in response:
            print(f"Error: {response['errors']}")
            return []
            
        stop_place = response['data']['stopPlace']
        if not stop_place:
            return []
            
        return stop_place.get('estimatedCalls', [])
    
    # Calculate Monday next week
    now = datetime.now(timezone.utc)
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:  # If today is Monday, get next Monday
        days_until_monday = 7
    
    monday = now + timedelta(days=days_until_monday)
    monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"🚂 OSLO S → MYRVOLL DEPARTURES (ENTIRE MONDAY)")
    print("=" * 80)
    print(f"Monday date: {monday_start.strftime('%Y-%m-%d (%A)')}")
    print(f"Query time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Monday start: {monday_start.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"Monday start: {(monday_start + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')} Local (UTC+2)")
    print()
    
    # Get all departures from Oslo S for Monday (starting from 00:00 UTC)
    all_departures = get_departures(oslo_id, monday_start)
    print(f"Total departures from Oslo S on Monday: {len(all_departures)}")
    
    # If we didn't get enough departures, try with a higher limit
    if len(all_departures) < 100:
        print("Increasing departure limit to capture more data...")
        # Update the function to get more departures
        def get_more_departures(station_id, start_time):
            query = """
                query($id: String!, $startTime: DateTime!, $numberOfDepartures: Int!) {
                    stopPlace(id: $id) {
                        id
                        name
                        estimatedCalls(
                            numberOfDepartures: $numberOfDepartures,
                            startTime: $startTime,
                            timeRange: 86400
                        ) {
                            aimedDepartureTime
                            expectedDepartureTime
                            actualDepartureTime
                            realtime
                            cancellation
                            serviceJourney {
                                id
                                line {
                                    publicCode
                                    name
                                    id
                                }
                                transportMode
                            }
                            destinationDisplay {
                                frontText
                            }
                            quay {
                                id
                                name
                            }
                        }
                    }
                }
            """
            
            variables = {
                "id": station_id,
                "startTime": start_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                "numberOfDepartures": 1000  # Much higher limit
            }
            
            response = make_request(query, variables)
            if 'errors' in response:
                print(f"Error: {response['errors']}")
                return []
                
            stop_place = response['data']['stopPlace']
            if not stop_place:
                return []
                
            return stop_place.get('estimatedCalls', [])
        
        all_departures = get_more_departures(oslo_id, monday_start)
        print(f"Total departures from Oslo S on Monday (expanded): {len(all_departures)}")
    
    # Filter for L2 trains going towards Myrvoll (Ski)
    l2_to_myrvoll = []
    for call in all_departures:
        line_code = call['serviceJourney']['line'].get('publicCode', '')
        if line_code == 'L2':
            final_dest = call.get('destinationDisplay', {}).get('frontText', '')
            # Check if going towards Myrvoll (Ski)
            if 'ski' in final_dest.lower():
                l2_to_myrvoll.append(call)
    
    print(f"L2 departures going to Myrvoll area: {len(l2_to_myrvoll)}")
    print()
    
    # Display ALL L2 departures to Myrvoll
    print("📅 ALL L2 DEPARTURES FROM OSLO S TO MYRVOLL (ENTIRE MONDAY):")
    print("-" * 80)
    print(f"{'Time (UTC)':<12} {'Time (Local)':<12} {'Final Dest':<15} {'Realtime':<8} {'Cancelled':<10} {'Service ID':<25}")
    print("-" * 80)
    
    for call in l2_to_myrvoll:
        aimed_time = call.get('aimedDepartureTime', '')
        expected_time = call.get('expectedDepartureTime', '')
        actual_time = call.get('actualDepartureTime', '')
        realtime = call.get('realtime', False)
        cancelled = call.get('cancellation', False)
        final_dest = call.get('destinationDisplay', {}).get('frontText', '')
        service_id = call['serviceJourney']['id']
        
        # Use actual time if available, otherwise expected, otherwise aimed
        departure_time = actual_time or expected_time or aimed_time
        if departure_time:
            dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            utc_time = dt.strftime('%H:%M')
            local_time = (dt + timedelta(hours=2)).strftime('%H:%M')  # UTC+2
        else:
            utc_time = 'N/A'
            local_time = 'N/A'
            
        print(f"{utc_time:<12} {local_time:<12} {final_dest:<15} {str(realtime):<8} {str(cancelled):<10} {service_id[:25]:<25}")
    
    # Analyze schedule patterns
    print(f"\n📈 SCHEDULE ANALYSIS:")
    print("=" * 50)
    
    # Group by hour
    by_hour = {}
    for call in l2_to_myrvoll:
        aimed_time = call.get('aimedDepartureTime', '')
        if aimed_time:
            dt = datetime.fromisoformat(aimed_time.replace('Z', '+00:00'))
            hour = dt.hour
            if hour not in by_hour:
                by_hour[hour] = []
            by_hour[hour].append(dt)
    
    print("Departures by hour (UTC):")
    for hour in sorted(by_hour.keys()):
        local_hour = (hour + 2) % 24
        count = len(by_hour[hour])
        times = [dt.strftime('%H:%M') for dt in sorted(by_hour[hour])]
        print(f"  {hour:02d}:00 UTC ({local_hour:02d}:00 Local): {count} departures - {', '.join(times)}")
    
    # Find service periods
    print(f"\n🚀 SERVICE PERIODS:")
    print("-" * 25)
    
    # Early morning (4-6 UTC)
    early_morning = [dt for hour, times in by_hour.items() if 4 <= hour < 6 for dt in times]
    print(f"Early morning (4-6 UTC): {len(early_morning)} departures")
    
    # Morning rush (6-9 UTC)
    morning_rush = [dt for hour, times in by_hour.items() if 6 <= hour < 9 for dt in times]
    print(f"Morning rush (6-9 UTC): {len(morning_rush)} departures")
    
    # Midday (9-15 UTC)
    midday = [dt for hour, times in by_hour.items() if 9 <= hour < 15 for dt in times]
    print(f"Midday (9-15 UTC): {len(midday)} departures")
    
    # Afternoon rush (15-18 UTC)
    afternoon_rush = [dt for hour, times in by_hour.items() if 15 <= hour < 18 for dt in times]
    print(f"Afternoon rush (15-18 UTC): {len(afternoon_rush)} departures")
    
    # Evening (18-24 UTC)
    evening = [dt for hour, times in by_hour.items() if 18 <= hour < 24 for dt in times]
    print(f"Evening (18-24 UTC): {len(evening)} departures")
    
    # Night (0-4 UTC)
    night = [dt for hour, times in by_hour.items() if 0 <= hour < 4 for dt in times]
    print(f"Night (0-4 UTC): {len(night)} departures")
    
    # Check for different final destinations
    print(f"\n🎯 FINAL DESTINATIONS:")
    print("-" * 25)
    destinations = {}
    for call in l2_to_myrvoll:
        final_dest = call.get('destinationDisplay', {}).get('frontText', '')
        if final_dest not in destinations:
            destinations[final_dest] = 0
        destinations[final_dest] += 1
    
    for dest, count in sorted(destinations.items()):
        print(f"  {dest}: {count} departures")
    
    # Service coverage analysis
    print(f"\n📊 SERVICE COVERAGE:")
    print("-" * 25)
    total_hours = 24
    hours_with_service = len(by_hour)
    coverage_percentage = (hours_with_service / total_hours) * 100
    
    print(f"Hours with service: {hours_with_service}/24 ({coverage_percentage:.1f}%)")
    print(f"Total departures: {len(l2_to_myrvoll)}")
    print(f"Average departures per hour: {len(l2_to_myrvoll)/24:.1f}")
    
    if by_hour:
        peak_hour = max(by_hour.keys(), key=lambda h: len(by_hour[h]))
        peak_count = len(by_hour[peak_hour])
        print(f"Peak hour: {peak_hour:02d}:00 UTC ({peak_hour+2:02d}:00 Local) with {peak_count} departures")
    
    # Analyze intervals during peak periods
    print(f"\n⏰ PEAK PERIOD INTERVAL ANALYSIS:")
    print("-" * 40)
    
    if len(l2_to_myrvoll) > 1:
        # Calculate intervals between consecutive departures
        times = []
        for call in l2_to_myrvoll:
            aimed_time = call.get('aimedDepartureTime', '')
            if aimed_time:
                dt = datetime.fromisoformat(aimed_time.replace('Z', '+00:00'))
                times.append(dt)
        
        times.sort()
        
        # Focus on afternoon rush hours (15-18 UTC)
        afternoon_times = [dt for dt in times if 15 <= dt.hour < 18]
        if len(afternoon_times) > 1:
            afternoon_intervals = []
            for i in range(1, len(afternoon_times)):
                interval = (afternoon_times[i] - afternoon_times[i-1]).total_seconds() / 60
                afternoon_intervals.append(interval)
            
            if afternoon_intervals:
                avg_interval = sum(afternoon_intervals) / len(afternoon_intervals)
                print(f"Afternoon rush average interval: {avg_interval:.1f} minutes")
                print(f"Afternoon rush intervals: {[f'{int(i)}min' for i in afternoon_intervals]}")
        
        # Focus on evening hours (18-24 UTC)
        evening_times = [dt for dt in times if 18 <= dt.hour < 24]
        if len(evening_times) > 1:
            evening_intervals = []
            for i in range(1, len(evening_times)):
                interval = (evening_times[i] - evening_times[i-1]).total_seconds() / 60
                evening_intervals.append(interval)
            
            if evening_intervals:
                avg_interval = sum(evening_intervals) / len(evening_intervals)
                print(f"Evening average interval: {avg_interval:.1f} minutes")
                print(f"Evening intervals: {[f'{int(i)}min' for i in evening_intervals]}")
    
    print(f"\n📋 SUMMARY:")
    print(f"Date: {monday_start.strftime('%Y-%m-%d (%A)')}")
    print(f"Total L2 departures from Oslo S to Myrvoll: {len(l2_to_myrvoll)}")
    if by_hour:
        print(f"Service period: {min(by_hour.keys()):02d}:00 - {max(by_hour.keys()):02d}:00 UTC")
        print(f"Service period: {(min(by_hour.keys())+2)%24:02d}:00 - {(max(by_hour.keys())+2)%24:02d}:00 Local")

if __name__ == "__main__":
    query_monday_oslo_to_myrvoll_full_day()
