"""
Routing Engine for Digital Twin Simulation Platform.

Provides station selection and routing logic.
"""

from typing import Optional, Tuple
from .network_graph import NetworkGraph


class RoutingEngine:
    """
    Routing engine for selecting optimal stations and computing travel costs.

    Implements minimal scoring logic based on queue length, inventory, and travel time.
    """

    def __init__(self, graph: NetworkGraph):
        """
        Initialize routing engine with a network graph.

        Args:
            graph: NetworkGraph instance containing station topology

        TODO: Add routing parameter configuration
        TODO: Add distance matrix caching
        """
        self.graph = graph

    def score_station(self, station_id: str, rider_location: Tuple[float, float]) -> float:
        """
        Score a station for routing selection.

        Args:
            station_id: Station identifier to score
            rider_location: Tuple of (latitude, longitude) for rider location

        Returns:
            Score value (lower is better)

        TODO: Add more sophisticated scoring factors
        TODO: Add weight configuration
        """
        try:
            station = self.graph.get_station(station_id)
        except KeyError:
            return float('inf')

        # Score based on queue length (higher queue = worse score)
        queue_score = station.queue_length * 2.0

        # Score based on inventory (lower inventory = worse score)
        inventory_score = max(0, 10 - station.inventory_current) * 1.5

        # Score based on distance (simplified - use station location)
        # TODO: Calculate actual distance from rider_location
        distance_score = 0.0  # Placeholder

        # Score based on status (down = very bad)
        status_score = 100.0 if station.status == "down" else 0.0

        total_score = queue_score + inventory_score + distance_score + status_score
        return total_score

    def select_best_station(self, rider_location: Tuple[float, float]) -> str:
        """
        Select the best station for a rider at the given location.

        Args:
            rider_location: Tuple of (latitude, longitude) for rider location

        Returns:
            Station ID of the best station

        Raises:
            ValueError: If no stations available

        TODO: Add station filtering (exclude down stations)
        TODO: Add tie-breaking logic
        """
        stations = list(self.graph.graph.nodes())
        if not stations:
            raise ValueError("No stations available in graph")

        # Score all stations
        scored_stations = [
            (station_id, self.score_station(station_id, rider_location))
            for station_id in stations
        ]

        # Select station with lowest score
        best_station_id, _ = min(scored_stations, key=lambda x: x[1])
        return best_station_id

    def compute_travel_cost(
        self,
        from_station_id: str,
        to_station_id: str
    ) -> float:
        """
        Compute travel cost between two stations.

        Args:
            from_station_id: Source station identifier
            to_station_id: Target station identifier

        Returns:
            Travel cost value in minutes

        TODO: Implement shortest path calculation
        TODO: Use networkx shortest path algorithms
        """
        if from_station_id not in self.graph.graph:
            raise ValueError(f"Station {from_station_id} not found")
        if to_station_id not in self.graph.graph:
            raise ValueError(f"Station {to_station_id} not found")

        # Check if direct edge exists
        if self.graph.graph.has_edge(from_station_id, to_station_id):
            edge_data = self.graph.graph[from_station_id][to_station_id]
            return edge_data.get("effective_travel_time_min", 0.0)

        # TODO: Compute shortest path if no direct edge
        # Placeholder: return high cost for indirect path
        return 999.0

    def reroute(
        self,
        current_station_id: str,
        rider_location: Tuple[float, float]
    ) -> str:
        """
        Compute a reroute to a different station.

        Args:
            current_station_id: Current target station identifier
            rider_location: Tuple of (latitude, longitude) for rider location

        Returns:
            New station ID to reroute to

        TODO: Add reroute reason tracking
        TODO: Add reroute attempt limits
        """
        stations = list(self.graph.graph.nodes())
        if not stations:
            raise ValueError("No stations available in graph")

        # Filter out current station
        alternative_stations = [s for s in stations if s != current_station_id]
        if not alternative_stations:
            # No alternatives - return current station
            return current_station_id

        # Score alternative stations
        scored_stations = [
            (station_id, self.score_station(station_id, rider_location))
            for station_id in alternative_stations
        ]

        # Select best alternative
        best_station_id, _ = min(scored_stations, key=lambda x: x[1])
        return best_station_id
