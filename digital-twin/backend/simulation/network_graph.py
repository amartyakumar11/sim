"""
Network Graph for Digital Twin Simulation Platform.

Manages station topology and connectivity using networkx.
"""

import networkx as nx
from typing import Optional
from .station import Station


class NetworkGraph:
    """
    Network graph representing station topology and connectivity.

    Uses networkx to manage nodes (stations) and edges (routes).
    Supports distance, time, and traffic-based edge weighting.
    """

    def __init__(self):
        """
        Initialize an empty network graph.

        TODO: Add graph configuration options
        TODO: Add graph validation
        """
        self.graph = nx.DiGraph()

    def add_station(self, station: Station):
        """
        Add a station node to the graph.

        Args:
            station: Station instance to add as a node

        TODO: Validate station has required fields (station_id, latitude, longitude)
        TODO: Check for duplicate station_id
        TODO: Store station metadata as node attributes
        """
        # TODO: Validate station.station_id exists
        # TODO: Check if station_id already exists in graph
        # TODO: Add node with station_id as identifier
        # TODO: Store station object and location as node attributes
        self.graph.add_node(
            station.station_id,
            station=station,
            latitude=station.latitude,
            longitude=station.longitude,
            swap_bays=station.swap_bays,
            chargers_total=station.chargers_total
        )

    def add_edge(
        self,
        from_station_id: str,
        to_station_id: str,
        distance_km: float,
        base_travel_time_min: float,
        traffic_factor: float
    ):
        """
        Add a directed edge between two stations.

        Args:
            from_station_id: Source station identifier
            to_station_id: Target station identifier
            distance_km: Distance in kilometers
            base_travel_time_min: Base travel time in minutes
            traffic_factor: Traffic multiplier (1.0 = no traffic, >1.0 = traffic delay)

        TODO: Validate both stations exist
        TODO: Validate edge attributes are positive
        TODO: Check for duplicate edges
        TODO: Compute weighted cost based on distance, time, and traffic
        """
        # TODO: Validate from_station_id exists in graph
        # TODO: Validate to_station_id exists in graph
        # TODO: Validate distance_km > 0
        # TODO: Validate base_travel_time_min > 0
        # TODO: Validate traffic_factor >= 1.0
        # TODO: Compute effective travel time: base_travel_time_min * traffic_factor
        # TODO: Add edge with all attributes
        self.graph.add_edge(
            from_station_id,
            to_station_id,
            distance_km=distance_km,
            base_travel_time_min=base_travel_time_min,
            traffic_factor=traffic_factor,
            effective_travel_time_min=base_travel_time_min * traffic_factor
        )

    def remove_station(self, station_id: str):
        """
        Remove a station and all its edges from the graph.

        Args:
            station_id: Station identifier to remove

        TODO: Validate station exists
        TODO: Handle cascading effects (orphaned edges)
        TODO: Log removal event
        """
        # TODO: Validate station_id exists in graph
        # TODO: Check for dependent routes that will be removed
        # TODO: Remove all incoming and outgoing edges
        # TODO: Remove node
        if station_id in self.graph:
            self.graph.remove_node(station_id)

    def update_station_capacity(
        self,
        station_id: str,
        new_swap_bays: Optional[int] = None,
        new_chargers_total: Optional[int] = None
    ):
        """
        Update station capacity attributes in the graph.

        Args:
            station_id: Station identifier
            new_swap_bays: New number of swap bays (None to keep current)
            new_chargers_total: New number of total chargers (None to keep current)

        TODO: Validate station exists
        TODO: Validate new values are non-negative
        TODO: Update both graph node attributes and Station object
        """
        # TODO: Validate station_id exists in graph
        # TODO: Validate new_swap_bays >= 0 if provided
        # TODO: Validate new_chargers_total >= 0 if provided
        # TODO: Update graph node attributes
        # TODO: Update Station object attributes if station is stored
        if station_id in self.graph:
            if new_swap_bays is not None:
                self.graph.nodes[station_id]['swap_bays'] = new_swap_bays
                # TODO: Update Station object if stored
            if new_chargers_total is not None:
                self.graph.nodes[station_id]['chargers_total'] = new_chargers_total
                # TODO: Update Station object if stored

    def get_neighbors(self, station_id: str) -> list:
        """
        Get all neighbor station IDs reachable from this station.

        Args:
            station_id: Station identifier

        Returns:
            List of neighbor station IDs

        TODO: Validate station exists
        TODO: Return sorted list for determinism
        """
        # TODO: Validate station_id exists in graph
        # TODO: Get all successors (outgoing edges)
        # TODO: Return sorted list of neighbor IDs
        if station_id in self.graph:
            return list(self.graph.successors(station_id))
        return []

    def get_station(self, station_id: str) -> Station:
        """
        Get the Station object for a given station ID.

        Args:
            station_id: Station identifier

        Returns:
            Station instance

        Raises:
            KeyError: If station_id not found

        TODO: Validate station exists
        TODO: Return Station object from node attributes
        """
        # TODO: Validate station_id exists in graph
        # TODO: Retrieve Station object from node attributes
        if station_id not in self.graph:
            raise KeyError(f"Station {station_id} not found in graph")
        return self.graph.nodes[station_id]['station']

    def load_topology(self, topology_config: dict):
        """
        Load station topology from configuration dictionary.

        Args:
            topology_config: Dictionary containing zones, stations, and edges

        Expected format:
        {
            "zones": [{"zone_id": "Z_...", "zone_name": "...", ...}, ...],
            "stations": [{"station_id": "...", "zone_id": "...", ...}, ...],
            "edges": [{"from_station_id": "...", "to_station_id": "...", ...}, ...]
        }

        Raises:
            ValueError: If topology_config is invalid or connectivity validation fails
        """
        # Validate topology_config structure
        if not isinstance(topology_config, dict):
            raise ValueError("topology_config must be a dictionary")
        
        if "zones" not in topology_config:
            raise ValueError("topology_config must contain 'zones' key")
        
        if "stations" not in topology_config:
            raise ValueError("topology_config must contain 'stations' key")
        
        if "edges" not in topology_config:
            raise ValueError("topology_config must contain 'edges' key")
        
        # Parse zones and build zone metadata structure
        zones_metadata = {}
        for zone in topology_config["zones"]:
            zone_id = zone.get("zone_id")
            if not zone_id:
                raise ValueError("Each zone must have a 'zone_id'")
            
            zones_metadata[zone_id] = {
                "station_ids": [],  # Will be populated when adding stations
                "zone_name": zone.get("zone_name", zone_id),
                "type": zone.get("description", "").split()[0].lower() if zone.get("description") else "unknown"
            }
        
        # Store zone metadata in graph attributes (GUARDRAIL #1)
        self.graph.graph["zones"] = zones_metadata
        
        # Add all stations as nodes (without Station objects - will be added later by simulation)
        for station_config in topology_config["stations"]:
            station_id = station_config.get("station_id")
            if not station_id:
                raise ValueError("Each station must have a 'station_id'")
            
            zone_id = station_config.get("zone_id")
            if zone_id not in zones_metadata:
                raise ValueError(f"Station {station_id} references unknown zone {zone_id}")
            
            # Add station node with attributes (no Station object yet)
            self.graph.add_node(
                station_id,
                zone_id=zone_id,
                swap_bays=station_config.get("swap_bays", 4),
                inventory_capacity=station_config.get("inventory_capacity", 40),
                status=station_config.get("status", "up"),
                station=None  # Will be set when Station object is created
            )
            
            # Add station_id to zone metadata
            zones_metadata[zone_id]["station_ids"].append(station_id)
        
        # Add all edges
        for edge in topology_config["edges"]:
            from_station_id = edge.get("from_station_id")
            to_station_id = edge.get("to_station_id")
            
            if not from_station_id or not to_station_id:
                raise ValueError("Each edge must have 'from_station_id' and 'to_station_id'")
            
            if from_station_id not in self.graph:
                raise ValueError(f"Edge references unknown station: {from_station_id}")
            
            if to_station_id not in self.graph:
                raise ValueError(f"Edge references unknown station: {to_station_id}")
            
            self.add_edge(
                from_station_id,
                to_station_id,
                distance_km=edge.get("distance_km", 1.0),
                base_travel_time_min=edge.get("base_travel_time_min", 3.0),
                traffic_factor=edge.get("traffic_factor", 1.0)
            )
        
        # Validate zone-level connectivity (GUARDRAIL #2: zone-level, not node-level)
        self._validate_zone_connectivity()
    
    def _validate_zone_connectivity(self):
        """
        Validate that every zone connects to at least one other zone.
        
        This is ZONE-LEVEL validation, not node-level (GUARDRAIL #2).
        We don't require all stations to reach all other stations.
        
        Raises:
            ValueError: If any zone is isolated (no inter-zone edges)
        """
        zones = self.graph.graph.get("zones", {})
        
        if not zones:
            # No zones defined, skip validation
            return
        
        # Build zone-to-zone connectivity map
        zone_connections = {zone_id: set() for zone_id in zones.keys()}
        
        for from_station, to_station in self.graph.edges():
            from_zone = self.graph.nodes[from_station].get("zone_id")
            to_zone = self.graph.nodes[to_station].get("zone_id")
            
            if from_zone and to_zone and from_zone != to_zone:
                zone_connections[from_zone].add(to_zone)
        
        # Check that every zone connects to at least one other zone
        isolated_zones = [
            zone_id for zone_id, connections in zone_connections.items()
            if len(connections) == 0
        ]
        
        if isolated_zones:
            raise ValueError(
                f"Zone-level connectivity validation failed: "
                f"Zones {isolated_zones} have no inter-zone connections"
            )
    
    def clone(self):
        """
        Clone the network graph for intervention scenarios.
        
        GUARDRAIL #3: Deep copy graph structure and node attributes,
        but do NOT copy Station objects. Station objects will be
        re-instantiated during simulation initialization.
        
        Returns:
            New NetworkGraph instance with copied graph structure
        """
        cloned_graph = NetworkGraph()
        
        # Deep copy the networkx graph structure
        cloned_graph.graph = self.graph.copy(as_view=False)
        
        # Ensure zone metadata is also deep copied
        if "zones" in self.graph.graph:
            import copy
            cloned_graph.graph.graph["zones"] = copy.deepcopy(self.graph.graph["zones"])
        
        # Clear Station object references (will be rehydrated later)
        for node_id in cloned_graph.graph.nodes():
            cloned_graph.graph.nodes[node_id]["station"] = None
        
        return cloned_graph

    def snapshot(self) -> dict:
        """
        Create a snapshot of the current graph state.

        Returns:
            Dictionary containing graph topology, zone information, and attributes
        """
        # Count intra-zone vs inter-zone edges
        intra_zone_edges = 0
        inter_zone_edges = 0
        
        for from_station, to_station in self.graph.edges():
            from_zone = self.graph.nodes[from_station].get("zone_id")
            to_zone = self.graph.nodes[to_station].get("zone_id")
            
            if from_zone == to_zone:
                intra_zone_edges += 1
            else:
                inter_zone_edges += 1
        
        # Build zone connectivity matrix
        zones = self.graph.graph.get("zones", {})
        zone_connectivity = {}
        
        for zone_id in zones.keys():
            zone_connectivity[zone_id] = set()
        
        for from_station, to_station in self.graph.edges():
            from_zone = self.graph.nodes[from_station].get("zone_id")
            to_zone = self.graph.nodes[to_station].get("zone_id")
            
            if from_zone and to_zone and from_zone != to_zone:
                zone_connectivity[from_zone].add(to_zone)
        
        # Convert sets to lists for JSON serialization
        zone_connectivity_serializable = {
            zone_id: list(connections) 
            for zone_id, connections in zone_connectivity.items()
        }
        
        return {
            "nodes": list(self.graph.nodes(data=True)),
            "edges": list(self.graph.edges(data=True)),
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "zones": self.graph.graph.get("zones", {}),
            "intra_zone_edges": intra_zone_edges,
            "inter_zone_edges": inter_zone_edges,
            "zone_connectivity": zone_connectivity_serializable
        }

