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
                - "base_demand_rate": float (arrivals per hour)
                - "time_of_day_curve": dict (TimeOfDayCurve config)
                - "weather_config": dict (WeatherModifier config)
                - "events_config": list[dict] (EventModifier config)
                - "station_weights": dict (StationSkewModel config)
            stations: List of Station instances
            event_logger: EventLogger instance for logging events

        TODO: Add validation for config structure
        TODO: Initialize all modifier components
        TODO: Set up RNG with seed
        """
        self.event_logger = event_logger
        self.stations = stations

        # Initialize RNG with seed for determinism
        rng_seed = config.get("rng_seed", 42)
        self.rng = random.Random(rng_seed)

        # Base demand rate (arrivals per hour)
        self.base_demand_rate = config.get("base_demand_rate", 10.0)

        # Initialize modifiers
        self.time_of_day_curve = TimeOfDayCurve(config.get("time_of_day_curve", {}))
        self.weather_modifier = WeatherModifier(config.get("weather_config", {}))
        self.event_modifier = EventModifier(config.get("events_config", []))
        self.station_skew = StationSkewModel(config.get("station_weights", {}))

        # Current weather state (TODO: integrate with weather service)
        self.current_weather = config.get("current_weather", "sunny")

        # TODO: Validate base_demand_rate > 0
        # TODO: Validate stations list is not empty
        # TODO: Initialize arrival counter for rider_id generation

    def generate_arrivals(self, start_time: datetime, end_time: datetime) -> list[dict]:
        """
        Generate rider arrivals between start_time and end_time.

        Args:
            start_time: Start datetime
            end_time: End datetime

        Returns:
            List of arrival dictionaries, each containing:
                - "timestamp": datetime
                - "rider_id": str
                - "station_id": str
                - "metadata": dict

        TODO: Implement Poisson process for arrival generation
        TODO: Apply all modifiers (time, weather, events)
        TODO: Select stations based on skew weights
        TODO: Log rider_arrival events
        TODO: Return arrival list for SimPy integration
        """
        arrivals = []
        current_time = start_time

        # TODO: Generate arrivals using Poisson process
        # TODO: While current_time < end_time:
        # TODO:   Calculate next arrival time using exponential distribution
        # TODO:   Apply time-of-day multiplier
        # TODO:   Apply weather multiplier
        # TODO:   Apply event multiplier
        # TODO:   Adjust arrival rate based on combined multiplier
        # TODO:   Generate rider_id
        # TODO:   Select station using weighted selection
        # TODO:   Log rider_arrival event
        # TODO:   Add to arrivals list
        # TODO:   Advance current_time

        # Placeholder: generate a single arrival for now
        if current_time < end_time:
            rider_id = f"rider_{self.rng.randint(1000, 9999)}"
            station = self.select_station()

            # Get multipliers for metadata
            tod_multiplier = self.time_of_day_curve.get_multiplier(current_time)
            weather_multiplier = self.weather_modifier.get_multiplier(self.current_weather)
            event_multiplier = self.event_modifier.get_multiplier(current_time)
            station_weight = self.station_skew.get_weight(station.station_id)

            # Get station location for routing
            rider_location = (station.latitude, station.longitude)

            # Log rider_arrival event
            self.event_logger.log_event(
                event_type="rider_arrival",
                station_id=station.station_id,
                rider_id=rider_id,
                metadata={
                    "timestamp": current_time.isoformat(),
                    "weather_state": self.current_weather,
                    "tod_multiplier": tod_multiplier,
                    "weather_multiplier": weather_multiplier,
                    "event_multiplier": event_multiplier,
                    "station_weight": station_weight
                }
            )

            arrival = {
                "timestamp": current_time,
                "rider_id": rider_id,
                "station_id": station.station_id,
                "metadata": {
                    "weather_state": self.current_weather,
                    "tod_multiplier": tod_multiplier,
                    "weather_multiplier": weather_multiplier,
                    "event_multiplier": event_multiplier,
                    "station_weight": station_weight,
                    "rider_location": rider_location
                }
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
        Select a station based on skew weights.

        Returns:
            Selected Station instance

        TODO: Implement weighted random selection
        TODO: Normalize weights
        TODO: Use RNG for selection
        """
        # TODO: Get weights for all stations
        # TODO: Normalize weights to probabilities
        # TODO: Use RNG to select station based on weights
        # TODO: Return selected station

        # Placeholder: return first station
        if not self.stations:
            raise ValueError("No stations available")
        return self.stations[0]

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
