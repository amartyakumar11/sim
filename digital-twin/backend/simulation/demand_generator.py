"""
Demand Generator for Digital Twin Simulation Platform.

Generates deterministic rider arrival patterns with time, weather, event, and station skew modifiers.
"""

import random
from datetime import datetime, timedelta
from typing import Optional
from .station import Station
from .event_logger import EventLogger


class TimeOfDayCurve:
    """
    Models time-of-day demand patterns.

    Supports weekday vs weekend curves and configurable multipliers.
    """

    def __init__(self, curve_config: dict):
        """
        Initialize time-of-day curve with configuration.

        Args:
            curve_config: Dictionary containing curve configuration
                Expected keys: "weekday_curve", "weekend_curve" (optional)
                Each curve is a list of (hour, multiplier) tuples

        TODO: Add validation for curve_config structure
        TODO: Support smooth interpolation between hours
        TODO: Add ML-based curve fitting capability
        """
        self.weekday_curve = curve_config.get("weekday_curve", [])
        self.weekend_curve = curve_config.get("weekend_curve", curve_config.get("weekday_curve", []))
        # TODO: Validate curve format (list of tuples)
        # TODO: Sort curves by hour for efficient lookup
        # TODO: Add default curve if none provided

    def get_multiplier(self, timestamp: datetime) -> float:
        """
        Get demand multiplier for a given timestamp.

        Args:
            timestamp: Datetime to evaluate

        Returns:
            Multiplier value (>= 0.0)

        TODO: Implement piecewise linear interpolation
        TODO: Handle edge cases (midnight wrap-around)
        TODO: Cache results for performance
        """
        # TODO: Determine if weekday or weekend
        # TODO: Select appropriate curve
        # TODO: Find surrounding hour points
        # TODO: Interpolate multiplier value
        # TODO: Return multiplier (default to 1.0 if no curve)
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5
        curve = self.weekend_curve if is_weekend else self.weekday_curve

        # Placeholder: simple lookup (no interpolation yet)
        for curve_hour, multiplier in curve:
            if curve_hour == hour:
                return multiplier
        return 1.0


class WeatherModifier:
    """
    Modifies demand based on weather conditions.

    Supports multiple weather states with configurable multipliers.
    """

    def __init__(self, weather_config: dict):
        """
        Initialize weather modifier with configuration.

        Args:
            weather_config: Dictionary mapping weather states to multipliers
                Example: {"sunny": 1.2, "rainy": 0.8, "snowy": 0.5}

        TODO: Add validation for weather_config
        TODO: Support time-varying weather (weather forecast integration)
        TODO: Add real weather API integration
        """
        self.weather_multipliers = weather_config or {}
        # TODO: Validate all multipliers are >= 0.0
        # TODO: Add default weather states if none provided

    def get_multiplier(self, weather_state: str) -> float:
        """
        Get demand multiplier for a weather state.

        Args:
            weather_state: Weather condition string (e.g., "sunny", "rainy")

        Returns:
            Multiplier value (>= 0.0), defaults to 1.0 if weather unknown

        TODO: Support fuzzy matching for weather states
        TODO: Handle weather state normalization
        """
        # TODO: Normalize weather_state (lowercase, strip whitespace)
        # TODO: Lookup multiplier in weather_multipliers
        # TODO: Return multiplier or default to 1.0
        return self.weather_multipliers.get(weather_state, 1.0)


class EventModifier:
    """
    Applies time-window-based demand spikes from events.

    Supports overlapping events with multiplicative effects.
    """

    def __init__(self, events_config: list[dict]):
        """
        Initialize event modifier with event list.

        Args:
            events_config: List of event dictionaries
                Each event: {"start": datetime, "end": datetime, "multiplier": float}

        TODO: Add validation for events_config structure
        TODO: Support recurring events
        TODO: Add city event feed integration
        """
        self.events = events_config or []
        # TODO: Validate each event has start, end, multiplier
        # TODO: Sort events by start time for efficient lookup
        # TODO: Check for overlapping events

    def get_multiplier(self, timestamp: datetime) -> float:
        """
        Get combined multiplier from all active events at timestamp.

        Args:
            timestamp: Datetime to evaluate

        Returns:
            Combined multiplier (>= 0.0), product of all active events

        TODO: Optimize lookup with sorted events
        TODO: Handle edge cases (events spanning midnight)
        """
        # TODO: Iterate through events
        # TODO: Check if timestamp is within event window
        # TODO: Multiply all active event multipliers
        # TODO: Return product (default to 1.0 if no active events)
        multiplier = 1.0
        for event in self.events:
            start = event.get("start")
            end = event.get("end")
            if start and end and start <= timestamp <= end:
                multiplier *= event.get("multiplier", 1.0)
        return multiplier


class StationSkewModel:
    """
    Models station selection bias.

    Assigns weights to stations to skew demand distribution.
    """

    def __init__(self, station_weights: dict):
        """
        Initialize station skew model with weights.

        Args:
            station_weights: Dictionary mapping station_id to weight (float >= 0.0)

        TODO: Add validation for station_weights
        TODO: Support normalized vs raw weights
        TODO: Add ML-based calibration capability
        """
        self.weights = station_weights or {}
        # TODO: Validate all weights are >= 0.0
        # TODO: Normalize weights if needed

    def get_weight(self, station_id: str) -> float:
        """
        Get weight for a station.

        Args:
            station_id: Station identifier

        Returns:
            Weight value (>= 0.0), defaults to 1.0 if station unknown

        TODO: Support station category-based weights
        TODO: Add dynamic weight updates
        """
        # TODO: Lookup weight in weights dictionary
        # TODO: Return weight or default to 1.0
        return self.weights.get(station_id, 1.0)


class DemandGenerator:
    """
    Main demand generation engine.

    Generates deterministic rider arrivals with configurable modifiers.
    """

    def __init__(self, config: dict, stations: list[Station], event_logger: EventLogger):
        """
        Initialize demand generator.

        Args:
            config: Configuration dictionary containing:
                - "rng_seed": int (for deterministic RNG)
                - "base_demand_rate_per_min": float (arrivals per minute)
                - "time_of_day_curve": dict (TimeOfDayCurve config)
                - "weather_config": dict (WeatherModifier config)
                - "events_config": list[dict] (EventModifier config)
                - "station_weights": dict (StationSkewModel config)
            stations: List of Station instances
            event_logger: EventLogger instance for logging events
        """
        self.event_logger = event_logger
        self.stations = stations

        if not stations or len(stations) == 0:
            raise ValueError("At least one station is required")

        # Initialize RNG with seed for determinism
        rng_seed = config.get("rng_seed", 42)
        self.rng = random.Random(rng_seed)

        # Base demand rate (arrivals per minute)
        self.base_demand_rate_per_min = config.get("base_demand_rate_per_min", 0.167)  # ~10/hour default
        
        if self.base_demand_rate_per_min <= 0:
            raise ValueError("base_demand_rate_per_min must be > 0")

        # Initialize modifiers (Level 1: not used, but keep infrastructure)
        self.time_of_day_curve = TimeOfDayCurve(config.get("time_of_day_curve", {}))
        self.weather_modifier = WeatherModifier(config.get("weather_config", {}))
        self.event_modifier = EventModifier(config.get("events_config", []))
        self.station_skew = StationSkewModel(config.get("station_weights", {}))

        # Current weather state (Level 1: not used)
        self.current_weather = config.get("current_weather", "sunny")
        
        # Arrival counter for unique rider IDs
        self.arrival_counter = 0

    def generate_arrivals(self, start_time: datetime, end_time: datetime) -> list[dict]:
        """
        Generate rider arrivals between start_time and end_time using Poisson process.

        Args:
            start_time: Start datetime
            end_time: End datetime

        Returns:
            List of arrival dictionaries, each containing:
                - "timestamp": datetime
                - "rider_id": str
                - "station_id": str
                - "metadata": dict
        """
        arrivals = []
        current_time = start_time
        
        # Generate arrivals using Poisson process (exponential inter-arrival times)
        while current_time < end_time:
            # Sample inter-arrival time from exponential distribution
            # Rate parameter is lambda (arrivals per minute)
            # Inter-arrival time ~ Exp(lambda), mean = 1/lambda minutes
            inter_arrival_minutes = self.rng.expovariate(self.base_demand_rate_per_min)
            
            # Advance time
            current_time = current_time + timedelta(minutes=inter_arrival_minutes)
            
            # Check if still within simulation window
            if current_time >= end_time:
                break
            
            # Generate unique rider ID
            self.arrival_counter += 1
            rider_id = f"rider_{self.arrival_counter:06d}"
            
            # Select station (deterministic round-robin for Level 1)
            station = self.select_station()
            
            # Create arrival record
            arrival = {
                "timestamp": current_time,
                "rider_id": rider_id,
                "station_id": station.station_id,
                "metadata": {}
            }
            arrivals.append(arrival)
        
        return arrivals

    def next_arrival_time(self, current_time: datetime) -> datetime:
        """
        Calculate next arrival time based on current demand rate.

        Args:
            current_time: Current simulation time

        Returns:
            Next arrival datetime

        TODO: Apply all modifiers to get effective demand rate
        TODO: Sample from exponential distribution
        TODO: Return current_time + sampled interval
        """
        # TODO: Get time-of-day multiplier
        # TODO: Get weather multiplier
        # TODO: Get event multiplier
        # TODO: Calculate effective demand rate: base_rate * tod * weather * event
        # TODO: Sample inter-arrival time from exponential distribution
        # TODO: Return current_time + inter_arrival_time

        # Placeholder: return fixed interval
        return current_time + timedelta(minutes=10)

    def select_station(self) -> Station:
        """
        Select a station deterministically (round-robin for Level 1).

        Returns:
            Selected Station instance
        """
        if not self.stations:
            raise ValueError("No stations available")
        
        # Level 1: Simple round-robin selection
        # Use arrival counter to distribute evenly
        station_index = self.arrival_counter % len(self.stations)
        return self.stations[station_index]

    def snapshot(self) -> dict:
        """
        Create a snapshot of current demand generator state.

        Returns:
            Dictionary containing configuration and state

        TODO: Serialize all configuration
        TODO: Include current modifiers state
        TODO: Include RNG state (if needed for debugging)
        """
        # TODO: Build dictionary with:
        # TODO:   - base_demand_rate
        # TODO:   - current_weather
        # TODO:   - station_weights
        # TODO:   - time_of_day_curve config
        # TODO:   - weather_config
        # TODO:   - events_config
        # TODO: Return serializable structure
        return {
            "base_demand_rate": self.base_demand_rate,
            "current_weather": self.current_weather,
            "num_stations": len(self.stations),
            "station_weights": self.station_skew.weights
        }
