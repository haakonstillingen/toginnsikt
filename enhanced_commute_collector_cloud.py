#!/usr/bin/env python3
"""
Enhanced Commute Data Collector - Cloud Version
Uses PostgreSQL instead of SQLite for cloud deployment
"""

import requests
import json
import psycopg2
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import time
import re
from dataclasses import dataclass
from enum import Enum
from config_cloud import *

class CollectionStatus(Enum):
    """Status of departure collection"""
    PENDING = "pending"
    COLLECTED = "collected"
    FAILED = "failed"
    EXPIRED = "expired"
class DepartureStatus(Enum):
    """Business intelligence classification of departure outcomes"""
    ON_TIME = "on_time"
    DELAYED = "delayed" 
    CANCELLED = "cancelled"
    SEVERELY_DELAYED = "severely_delayed"
    UNKNOWN = "unknown"
@dataclass
class CommuteRoute:
    """Represents a specific commute route"""
    route_name: str
    source_station_id: str
    source_station_name: str
    target_station_id: str
    target_station_name: str
    final_destination_pattern: str
    direction: str  # 'morning' or 'afternoon'

@dataclass
class PlannedDeparture:
    """Represents a planned train departure"""
    id: Optional[int] = None
    planned_departure_time: datetime = None
    service_journey_id: str = ""
    line_code: str = ""
    final_destination: str = ""
    collection_status: CollectionStatus = CollectionStatus.PENDING
    retry_count: int = 0
    last_retry_time: Optional[datetime] = None

@dataclass
class ActualDeparture:
    """Represents an actual train departure"""
    actual_departure_time: Optional[datetime] = None
    expected_departure_time: Optional[datetime] = None
    delay_minutes: Optional[int] = None
    is_cancelled: bool = False
    is_realtime: bool = False
    # NEW BUSINESS INTELLIGENCE FIELDS:
    departure_status: Optional[str] = None
    expected_delay_minutes: Optional[int] = None
    classification_reason: Optional[str] = None

class EnhancedCommuteCollectorCloud:
    """Enhanced collector for cloud deployment using PostgreSQL"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
        # Entur API configuration
        self.base_url = ENTUR_API_URL
        self.headers = {
            'Content-Type': 'application/json',
            'ET-Client-Name': CLIENT_NAME
        }
        
        # Collection configuration
        self.data_retention_hours = DATA_RETENTION_HOURS
        self.retry_delay_minutes = RETRY_DELAY_MINUTES
        
        # Setup logging
        self.setup_logging()
        
        # Initialize database
        self.init_database()
        
        # Load commute routes
        self.routes = self.load_commute_routes()
        
    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.INFO if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_db_connection(self):
        """Get PostgreSQL database connection"""
        try:
            if CLOUD_SQL_CONNECTION_NAME:
                # Use Cloud SQL connector
                import socket
                import struct
                
                def connect_tcp_socket():
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(30)
                    sock.connect(('127.0.0.1', 5432))
                    return sock
                
                conn = psycopg2.connect(
                    host=f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}',
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME
                )
            else:
                # Direct connection
                conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
            return conn
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
        
    def init_database(self):
        """Initialize PostgreSQL database with enhanced schema"""
        conn = self.get_db_connection()
        if not conn:
            self.logger.error("Cannot initialize database - no connection")
            return
            
        cursor = conn.cursor()
        
        try:
            # Read and execute the base migration
            with open('migrations/002_create_commute_routes_table.sql', 'r') as f:
                migration_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    cursor.execute(statement)
            
            # Read and execute the business intelligence migration
            with open('migrations/003_add_business_intelligence_fields.sql', 'r') as f:
                bi_migration_sql = f.read()
            
            # Split by semicolon and execute each statement
            bi_statements = [stmt.strip() for stmt in bi_migration_sql.split(';') if stmt.strip()]
            for statement in bi_statements:
                if statement:
                    cursor.execute(statement)
            
            # Add enhanced columns to planned_departures table
            try:
                cursor.execute("""
                    ALTER TABLE planned_departures 
                    ADD COLUMN collection_status VARCHAR(20) DEFAULT 'pending'
                """)
            except psycopg2.ProgrammingError:
                pass  # Column already exists
                
            try:
                cursor.execute("""
                    ALTER TABLE planned_departures 
                    ADD COLUMN retry_count INTEGER DEFAULT 0
                """)
            except psycopg2.ProgrammingError:
                pass  # Column already exists
                
            try:
                cursor.execute("""
                    ALTER TABLE planned_departures 
                    ADD COLUMN last_retry_time TIMESTAMP WITH TIME ZONE
                """)
            except psycopg2.ProgrammingError:
                pass  # Column already exists
            
            conn.commit()
            self.logger.info("Enhanced database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
        finally:
            conn.close()
        
    def load_commute_routes(self) -> List[CommuteRoute]:
        """Load commute routes from database"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT route_name, source_station_id, source_station_name, 
                       target_station_id, target_station_name, final_destination_pattern, direction
                FROM commute_routes
            """)
            
            routes = []
            for row in cursor.fetchall():
                routes.append(CommuteRoute(
                    route_name=row[0],
                    source_station_id=row[1],
                    source_station_name=row[2],
                    target_station_id=row[3],
                    target_station_name=row[4],
                    final_destination_pattern=row[5],
                    direction=row[6]
                ))
            
            return routes
        except Exception as e:
            self.logger.error(f"Failed to load routes: {e}")
            return []
        finally:
            conn.close()
        
    def make_graphql_request(self, query: str, variables: Dict = None) -> Optional[Dict]:
        """Make a GraphQL request to Entur API"""
        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                self.logger.error(f"GraphQL errors: {data['errors']}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return None

    def collect_planned_departures_daily(self):
        """Collect planned departures for the next 24 hours (run at 03:00 UTC)"""
        self.logger.info("Starting daily planned departure collection")
        
        # Calculate start time (next 24 hours from now)
        now = datetime.now(timezone.utc)
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for route in self.routes:
            try:
                self.logger.info(f"Collecting planned departures for {route.route_name}")
                planned_departures = self.fetch_planned_departures(route, start_time, 24)
                self.store_planned_departures(route, planned_departures)
                self.logger.info(f"Stored {len(planned_departures)} planned departures for {route.route_name}")
            except Exception as e:
                self.logger.error(f"Error collecting planned departures for {route.route_name}: {e}")

    def fetch_planned_departures(self, route: CommuteRoute, start_time: datetime, hours_ahead: int = 24) -> List[PlannedDeparture]:
        """Fetch planned departures for a specific route"""
        # Use 1000 departures to ensure we capture all L2 departures in the time range
        num_departures = 1000
        
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
                        serviceJourney {
                            id
                            line {
                                publicCode
                            }
                        }
                        destinationDisplay {
                            frontText
                        }
                    }
                }
            }
        """
        
        variables = {
            "id": route.source_station_id,
            "startTime": start_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
            "numberOfDepartures": num_departures
        }
        
        response = self.make_graphql_request(query, variables)
        if not response or 'data' not in response:
            return []
            
        stop_place = response['data']['stopPlace']
        if not stop_place:
            return []
            
        planned_departures = []
        
        for call in stop_place.get('estimatedCalls', []):
            line_code = call['serviceJourney']['line'].get('publicCode', '')
            
            # Only process L2 line departures
            if line_code != 'L2':
                continue
                
            aimed_time = call.get('aimedDepartureTime')
            if not aimed_time:
                continue
                
            # Parse departure time
            departure_time = datetime.fromisoformat(aimed_time.replace('Z', '+00:00'))
            
            # Get final destination
            final_destination = call.get('destinationDisplay', {}).get('frontText', '')
            
            # Check if this matches our route's final destination pattern (skip if pattern is empty)
            if route.final_destination_pattern and not self.matches_final_destination(final_destination, route.final_destination_pattern):
                continue
                
            planned_departures.append(PlannedDeparture(
                planned_departure_time=departure_time,
                service_journey_id=call['serviceJourney']['id'],
                line_code=line_code,
                final_destination=final_destination,
                collection_status=CollectionStatus.PENDING
            ))
            
        return planned_departures

    def matches_final_destination(self, destination: str, pattern: str) -> bool:
        """Check if destination matches the route's final destination pattern"""
        # Convert pattern to regex (e.g., "Lysaker|Stabekk" becomes "Lysaker|Stabekk")
        pattern_regex = pattern.replace('|', '|')
        return bool(re.search(pattern_regex, destination, re.IGNORECASE))

    def get_collection_frequency(self) -> int:
        """Get collection frequency in minutes based on current time"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # High frequency during rush hours
        if (6 <= hour < 9) or (15 <= hour < 18):
            return 15
        # Medium frequency during regular hours
        elif (9 <= hour < 15) or (18 <= hour < 24):
            return 30
        # Low frequency during night
        else:
            return 60

    def get_pending_departures(self) -> List[PlannedDeparture]:
        """Get departures that need actual data collection"""
        conn = self.get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        try:
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(hours=self.data_retention_hours)
            
            cursor.execute("""
                SELECT pd.id, pd.planned_departure_time, pd.service_journey_id, 
                       pd.line_code, pd.final_destination, pd.collection_status,
                       pd.retry_count, pd.last_retry_time, cr.route_name
                FROM planned_departures pd
                JOIN commute_routes cr ON pd.route_id = cr.id
                WHERE pd.collection_status IN ('pending', 'failed')
                AND pd.planned_departure_time >= %s
                AND pd.planned_departure_time <= %s
                ORDER BY pd.planned_departure_time
            """, (cutoff_time, now))
            
            departures = []
            for row in cursor.fetchall():
                planned_time = row[1]
                last_retry = row[7]
                
                departures.append(PlannedDeparture(
                    id=row[0],
                    planned_departure_time=planned_time,
                    service_journey_id=row[2],
                    line_code=row[3],
                    final_destination=row[4],
                    collection_status=CollectionStatus(row[5]),
                    retry_count=row[6],
                    last_retry_time=last_retry
                ))
            
            return departures
        except Exception as e:
            self.logger.error(f"Failed to get pending departures: {e}")
            return []
        finally:
            conn.close()

    def collect_actual_departures(self):
        """Collect actual departure data for pending departures"""
        self.logger.info("Starting actual departure collection")
        
        # Get pending departures
        pending_departures = self.get_pending_departures()
        self.logger.info(f"Found {len(pending_departures)} pending departures")
        
        if not pending_departures:
            return
            
        # Fetch actual data
        actual_data = self.fetch_actual_departures(pending_departures)
        self.logger.info(f"Collected actual data for {len(actual_data)} departures")
        
        # Store successful collections
        if actual_data:
            self.store_actual_departures(actual_data)
            
        # Update failed collections
        successful_ids = set(actual_data.keys())
        failed_ids = [dep.id for dep in pending_departures if dep.id not in successful_ids]
        
        if failed_ids:
            # Enhanced monitoring: Log details about failed collections
            for dep in pending_departures:
                if dep.id in failed_ids:
                    self.logger.warning(f"Collection failed for departure: "
                                      f"planned={dep.planned_departure_time.strftime('%H:%M')} "
                                      f"destination={dep.final_destination} "
                                      f"service_journey_id={dep.service_journey_id} "
                                      f"retry_count={dep.retry_count}")
            
            self.update_failed_departures(failed_ids)
            self.logger.info(f"Marked {len(failed_ids)} departures as failed")

    def fetch_actual_departures(self, departures: List[PlannedDeparture]) -> Dict[int, ActualDeparture]:
        """Fetch actual departure data for a list of planned departures"""
        if not departures:
            return {}
            
        # Group departures by route for efficient API calls
        route_departures = {}
        for dep in departures:
            route_name = self.get_route_name_for_departure(dep.id)
            if route_name not in route_departures:
                route_departures[route_name] = []
            route_departures[route_name].append(dep)
        
        actual_data = {}
        
        for route_name, route_deps in route_departures.items():
            route = next((r for r in self.routes if r.route_name == route_name), None)
            if not route:
                continue
                
            # Fetch actual data for this route
            route_actual_data = self.fetch_route_actual_departures(route, route_deps)
            actual_data.update(route_actual_data)
            
        return actual_data

    def get_route_name_for_departure(self, departure_id: int) -> str:
        """Get route name for a departure ID"""
        conn = self.get_db_connection()
        if not conn:
            return ""
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT cr.route_name
                FROM planned_departures pd
                JOIN commute_routes cr ON pd.route_id = cr.id
                WHERE pd.id = %s
            """, (departure_id,))
            
            result = cursor.fetchone()
            return result[0] if result else ""
        except Exception as e:
            self.logger.error(f"Failed to get route name: {e}")
            return ""
        finally:
            conn.close()

    def fetch_route_actual_departures(self, route: CommuteRoute, departures: List[PlannedDeparture]) -> Dict[int, ActualDeparture]:
        """Fetch actual departure data for a specific route"""
        if not departures:
            return {}
            
        # Get the time range for this batch
        min_time = min(dep.planned_departure_time for dep in departures)
        max_time = max(dep.planned_departure_time for dep in departures)
        
        # Extend range to catch any delays
        start_time = min_time - timedelta(minutes=30)
        end_time = max_time + timedelta(hours=2)
        
        query = """
            query($id: String!, $startTime: DateTime!, $numberOfDepartures: Int!) {
                stopPlace(id: $id) {
                    id
                    name
                    estimatedCalls(
                        numberOfDepartures: $numberOfDepartures,
                        startTime: $startTime,
                        timeRange: 7200
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
                            }
                        }
                        destinationDisplay {
                            frontText
                        }
                    }
                }
            }
        """
        
        variables = {
            "id": route.source_station_id,
            "startTime": start_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
            "numberOfDepartures": 200
        }
        
        response = self.make_graphql_request(query, variables)
        if not response or 'data' not in response:
            return {}
            
        stop_place = response['data']['stopPlace']
        if not stop_place:
            return {}
            
        actual_data = {}
        
        # Create a lookup for our planned departures
        planned_lookup = {
            dep.service_journey_id: dep for dep in departures
        }
        
        # Enhanced monitoring: Log API response details
        total_api_calls = len(stop_place.get('estimatedCalls', []))
        l2_calls = [call for call in stop_place.get('estimatedCalls', []) 
                   if call['serviceJourney']['line'].get('publicCode', '') == 'L2']
        
        self.logger.info(f"API Response: {total_api_calls} total calls, {len(l2_calls)} L2 calls, "
                        f"looking for {len(departures)} planned departures")
        
        for call in stop_place.get('estimatedCalls', []):
            line_code = call['serviceJourney']['line'].get('publicCode', '')
            if line_code != 'L2':
                continue
                
            service_journey_id = call['serviceJourney']['id']
            if service_journey_id not in planned_lookup:
                # Enhanced monitoring: Log unmatched service journeys for debugging
                final_dest = call.get('destinationDisplay', {}).get('frontText', '')
                aimed_time = call.get('aimedDepartureTime', '')
                if aimed_time:
                    aimed_dt_log = datetime.fromisoformat(aimed_time.replace('Z', '+00:00'))
                    self.logger.debug(f"Unmatched L2 service journey: "
                                    f"time={aimed_dt_log.strftime('%H:%M')} "
                                    f"destination={final_dest} "
                                    f"service_journey_id={service_journey_id}")
                continue
                
            planned_dep = planned_lookup[service_journey_id]
            
            # Parse times
            aimed_time = call.get('aimedDepartureTime')
            expected_time = call.get('expectedDepartureTime')
            actual_time = call.get('actualDepartureTime')
            
            if not aimed_time:
                continue
                
            aimed_dt = datetime.fromisoformat(aimed_time.replace('Z', '+00:00'))
            expected_dt = datetime.fromisoformat(expected_time.replace('Z', '+00:00')) if expected_time else None
            actual_dt = datetime.fromisoformat(actual_time.replace('Z', '+00:00')) if actual_time else None
            
            # Calculate delay - ONLY from actual departure times
            # Bug fix: Remove calculation from expected_departure_time to prevent phantom delays
            delay_minutes = None
            if actual_dt and aimed_dt:
                delay_minutes = int((actual_dt - aimed_dt).total_seconds() / 60)
            # Removed: elif expected_dt and aimed_dt - this was creating phantom delays
                
            # Create ActualDeparture object
            actual_departure = ActualDeparture(
                actual_departure_time=actual_dt,
                expected_departure_time=expected_dt,
                delay_minutes=delay_minutes,
                is_cancelled=call.get('cancellation', False),
                is_realtime=call.get('realtime', False)
            )
            
            # CLASSIFICATION INTEGRATION: Classify departure outcome
            try:
                collection_time = datetime.now(timezone.utc)
                departure_status, classification_reason = self.classify_departure_outcome(
                    planned_dep, actual_departure, collection_time
                )
                
                # Set business intelligence fields
                actual_departure.departure_status = departure_status
                actual_departure.classification_reason = classification_reason
                
                # Calculate expected delay if we have expected time
                if expected_dt and aimed_dt:
                    expected_delay = int((expected_dt - aimed_dt).total_seconds() / 60)
                    actual_departure.expected_delay_minutes = expected_delay
                
                # Log classification for monitoring
                self.logger.debug(f"Classified departure: {departure_status.upper()} - {classification_reason} "
                                f"(planned={aimed_dt.strftime('%H:%M')}, "
                                f"actual={actual_dt.strftime('%H:%M') if actual_dt else 'None'}, "
                                f"expected={expected_dt.strftime('%H:%M') if expected_dt else 'None'})")
                
            except Exception as e:
                self.logger.error(f"Classification failed for departure {planned_dep.id}: {e}")
                # Set default values if classification fails
                actual_departure.departure_status = DepartureStatus.UNKNOWN.value
                actual_departure.classification_reason = "classification_error"
            
            actual_data[planned_dep.id] = actual_departure
            
            # Enhanced monitoring: Log cases with missing actual departure times
            if actual_dt is None and expected_dt is not None:
                self.logger.warning(f"Missing actual departure time detected: "
                                  f"planned={aimed_dt.strftime('%H:%M')} "
                                  f"expected={expected_dt.strftime('%H:%M')} "
                                  f"destination={planned_dep.final_destination} "
                                  f"service_journey_id={service_journey_id} "
                                  f"cancelled={call.get('cancellation', False)} "
                                  f"realtime={call.get('realtime', False)}")
            elif actual_dt is None and expected_dt is None:
                self.logger.info(f"No departure data available: "
                                f"planned={aimed_dt.strftime('%H:%M')} "
                                f"destination={planned_dep.final_destination} "
                                f"service_journey_id={service_journey_id} "
                                f"cancelled={call.get('cancellation', False)}")
        
        # Enhanced monitoring: Log summary of missing departures
        missing_actual = sum(1 for dep_id, dep_data in actual_data.items() 
                           if dep_data.actual_departure_time is None and dep_data.expected_departure_time is not None)
        missing_all = sum(1 for dep_id, dep_data in actual_data.items() 
                         if dep_data.actual_departure_time is None and dep_data.expected_departure_time is None)
        
        if missing_actual > 0 or missing_all > 0:
            self.logger.warning(f"Collection summary: {missing_actual} with expected but no actual time, "
                              f"{missing_all} with no departure data, "
                              f"{len(actual_data) - missing_actual - missing_all} successful")
        
        # CLASSIFICATION INTEGRATION: Log classification summary
        if actual_data:
            classification_summary = {}
            for dep_data in actual_data.values():
                status = dep_data.departure_status or 'unknown'
                classification_summary[status] = classification_summary.get(status, 0) + 1
            
            summary_parts = [f"{status.upper()}: {count}" for status, count in classification_summary.items()]
            self.logger.info(f"Classification summary: {', '.join(summary_parts)}")
            
        return actual_data

    def store_planned_departures(self, route: CommuteRoute, planned_departures: List[PlannedDeparture]):
        """Store planned departures in database"""
        conn = self.get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        try:
            # Get route ID
            cursor.execute("SELECT id FROM commute_routes WHERE route_name = %s", (route.route_name,))
            route_id = cursor.fetchone()[0]
            
            for planned in planned_departures:
                # Check if this departure already exists
                cursor.execute("""
                    SELECT id FROM planned_departures 
                    WHERE service_journey_id = %s AND planned_departure_time = %s
                """, (planned.service_journey_id, planned.planned_departure_time))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO planned_departures 
                        (route_id, planned_departure_time, service_journey_id, line_code, final_destination, collection_status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        route_id,
                        planned.planned_departure_time,
                        planned.service_journey_id,
                        planned.line_code,
                        planned.final_destination,
                        planned.collection_status.value
                    ))
                
            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to store planned departures: {e}")
        finally:
            conn.close()

    def store_actual_departures(self, actual_data: Dict[int, ActualDeparture]):
        """Store actual departure data in database"""
        conn = self.get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        try:
            for planned_id, actual in actual_data.items():
                # Data validation: ensure consistency (Bug fix for phantom delays)
                if actual.actual_departure_time is None and actual.delay_minutes is not None:
                    self.logger.warning(f"Data inconsistency detected for planned_id {planned_id}: "
                                      f"actual_departure_time is None but delay_minutes is {actual.delay_minutes}. "
                                      f"Setting delay_minutes to None to prevent phantom delay.")
                    actual.delay_minutes = None
                
                # Update planned departure status
                cursor.execute("""
                    UPDATE planned_departures 
                    SET collection_status = %s, retry_count = retry_count + 1, last_retry_time = %s
                    WHERE id = %s
                """, (CollectionStatus.COLLECTED.value, datetime.now(timezone.utc), planned_id))
                
                # Insert actual departure with business intelligence fields
                cursor.execute("""
                    INSERT INTO actual_departures 
                    (planned_departure_id, actual_departure_time, expected_departure_time, 
                     delay_minutes, is_cancelled, is_realtime, departure_status, 
                     expected_delay_minutes, classification_reason)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (planned_departure_id) DO UPDATE SET
                        actual_departure_time = EXCLUDED.actual_departure_time,
                        expected_departure_time = EXCLUDED.expected_departure_time,
                        delay_minutes = EXCLUDED.delay_minutes,
                        is_cancelled = EXCLUDED.is_cancelled,
                        is_realtime = EXCLUDED.is_realtime,
                        departure_status = EXCLUDED.departure_status,
                        expected_delay_minutes = EXCLUDED.expected_delay_minutes,
                        classification_reason = EXCLUDED.classification_reason
                """, (
                    planned_id,
                    actual.actual_departure_time,
                    actual.expected_departure_time,
                    actual.delay_minutes,
                    actual.is_cancelled,
                    actual.is_realtime,
                    actual.departure_status,
                    actual.expected_delay_minutes,
                    actual.classification_reason
                ))
                
            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to store actual departures: {e}")
        finally:
            conn.close()

    def update_failed_departures(self, failed_departure_ids: List[int]):
        """Update status for departures that failed to collect"""
        conn = self.get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        try:
            for dep_id in failed_departure_ids:
                cursor.execute("""
                    UPDATE planned_departures 
                    SET collection_status = %s, retry_count = retry_count + 1, last_retry_time = %s
                    WHERE id = %s
                """, (CollectionStatus.FAILED.value, datetime.now(timezone.utc), dep_id))
                
            conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to update failed departures: {e}")
        finally:
            conn.close()

    def run_collection_cycle(self):
        """Run one collection cycle"""
        try:
            # Collect actual departures
            self.collect_actual_departures()
            
            # Log collection statistics
            self.log_collection_stats()
            
        except Exception as e:
            self.logger.error(f"Collection cycle error: {e}")

    def log_collection_stats(self):
        """Log collection statistics"""
        conn = self.get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        try:
            # Get stats for today
            today = datetime.now(timezone.utc).date()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN collection_status = 'collected' THEN 1 ELSE 0 END) as collected,
                    SUM(CASE WHEN collection_status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN collection_status = 'failed' THEN 1 ELSE 0 END) as failed
                FROM planned_departures 
                WHERE DATE(planned_departure_time) = %s
            """, (today,))
            
            stats = cursor.fetchone()
            
            if stats[0] > 0:
                success_rate = (stats[1] / stats[0]) * 100
                self.logger.info(f"Collection stats: {stats[1]}/{stats[0]} collected ({success_rate:.1f}%), {stats[2]} pending, {stats[3]} failed")
        except Exception as e:
            self.logger.error(f"Failed to log collection stats: {e}")
        finally:
            conn.close()

    def run_continuous(self):
        """Run continuous data collection with adaptive scheduling"""
        self.logger.info("Starting enhanced continuous data collection")
        
        while True:
            try:
                # Run collection cycle
                self.run_collection_cycle()
                
                # Get next collection interval
                interval_minutes = self.get_collection_frequency()
                self.logger.info(f"Next collection in {interval_minutes} minutes")
                
                # Sleep until next collection
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                self.logger.info("Stopping data collection")
                break
            except Exception as e:
                self.logger.error(f"Collection error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def classify_departure_outcome(self, planned_dep: PlannedDeparture, actual_data: ActualDeparture, collection_time: datetime) -> Tuple[str, str]:
        """
        Classify departure outcome for business intelligence
        Returns: (departure_status, classification_reason)
        """
        
        # Case 1: Actual departure time available
        if actual_data.actual_departure_time:
            delay = actual_data.delay_minutes
            if delay <= 2:  # Within 2 minutes is considered on-time
                return DepartureStatus.ON_TIME.value, "actual_departure_on_time"
            elif delay <= 15:  # 3-15 minutes is delayed
                return DepartureStatus.DELAYED.value, "actual_departure_delayed"
            else:  # 15+ minutes is severely delayed
                return DepartureStatus.SEVERELY_DELAYED.value, "actual_departure_severely_delayed"
        
        # Case 2: Expected time available but no actual time
        elif actual_data.expected_departure_time:
            expected_delay = (actual_data.expected_departure_time - planned_dep.planned_departure_time).total_seconds() / 60
            
            # If expected delay is reasonable (0-15 min), likely a cancellation
            if 0 <= expected_delay <= 15:
                return DepartureStatus.CANCELLED.value, "expected_time_reasonable_cancellation"
            # If expected delay is severe (15+ min), likely severely delayed
            else:
                return DepartureStatus.SEVERELY_DELAYED.value, "expected_time_severe_delay"
        
        # Case 3: No departure data at all
        else:
            # Check if enough time has passed since planned departure
            time_since_planned = (collection_time - planned_dep.planned_departure_time).total_seconds() / 60
            
            if time_since_planned > 30:  # 30+ minutes past planned time
                return DepartureStatus.CANCELLED.value, "no_data_after_30min"
            else:
                return DepartureStatus.UNKNOWN.value, "no_data_within_collection_window"

    def calculate_business_metrics(self, departures: List[ActualDeparture]) -> Dict[str, float]:
        """
        Calculate business intelligence metrics
        """
        total = len(departures)
        if total == 0:
            return {
                'total_departures': 0,
                'on_time_rate': 0.0,
                'delay_rate': 0.0,
                'cancellation_rate': 0.0,
                'severe_delay_rate': 0.0
            }
        
        on_time = sum(1 for d in departures if d.departure_status == DepartureStatus.ON_TIME.value)
        delayed = sum(1 for d in departures if d.departure_status == DepartureStatus.DELAYED.value)
        cancelled = sum(1 for d in departures if d.departure_status == DepartureStatus.CANCELLED.value)
        severely_delayed = sum(1 for d in departures if d.departure_status == DepartureStatus.SEVERELY_DELAYED.value)
        
        return {
            'total_departures': total,
            'on_time_rate': (on_time / total * 100),
            'delay_rate': ((delayed + severely_delayed) / total * 100),
            'cancellation_rate': (cancelled / total * 100),
            'severe_delay_rate': (severely_delayed / total * 100)
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Commute Data Collector - Cloud Version')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--planned-only', action='store_true', help='Run only planned departure collection')
    parser.add_argument('--actual-only', action='store_true', help='Run only actual departure collection')
    
    args = parser.parse_args()
    
    collector = EnhancedCommuteCollectorCloud(verbose=args.verbose)
    
    try:
        if args.planned_only:
            collector.collect_planned_departures_daily()
        elif args.actual_only:
            collector.collect_actual_departures()
        elif args.continuous:
            collector.run_continuous()
        else:
            collector.run_collection_cycle()
    finally:
        pass
