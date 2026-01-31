"""
Scenario Intervention Engine: Apply deterministic interventions to city graphs.

Enables counterfactual analysis by:
1. Cloning baseline graph (immutable)
2. Applying interventions (add/remove/modify stations)
3. Returning modified graph for simulation re-run
4. Comparing baseline vs intervention outcomes

NO randomness, NO new events, NO simulation logic changes.
"""

from typing import Dict, List, Optional, Union
from copy import deepcopy
from enum import Enum

from .network_graph import NetworkGraph


class InterventionType(Enum):
    """Types of deterministic interventions."""
    ADD_STATION = "add_station"
    REMOVE_STATION = "remove_station"
    MODIFY_CAPACITY = "modify_capacity"
    MODIFY_SWAP_TIME = "modify_swap_time"
    MODIFY_CHARGERS = "modify_chargers"


class Intervention:
    """
    Represents a single intervention to apply to a city graph.
    
    Deterministic - same intervention always produces same result.
    """
    
    def __init__(
        self,
        intervention_type: InterventionType,
        station_id: str,
        zone_id: Optional[str] = None,
        parameters: Optional[Dict] = None
    ):
        """
        Initialize an intervention.
        
        Args:
            intervention_type: Type of intervention
            station_id: Station to modify (or new station ID for add)
            zone_id: Zone for new station (add_station only)
            parameters: Intervention-specific parameters
        """
        self.intervention_type = intervention_type
        self.station_id = station_id
        self.zone_id = zone_id
        self.parameters = parameters or {}
    
    def __repr__(self):
        return f"Intervention({self.intervention_type.value}, {self.station_id}, {self.parameters})"


class ScenarioInterventionEngine:
    """
    Applies deterministic interventions to city graphs.
    
    Core principle: Baseline graph NEVER modified.
    All interventions create a NEW graph via clone().
    """
    
    def __init__(self):
        """Initialize intervention engine."""
        pass
    
    def apply(
        self,
        baseline_graph: NetworkGraph,
        interventions: Union[Intervention, List[Intervention]]
    ) -> NetworkGraph:
        """
        Apply interventions to baseline graph (returns new graph).
        
        CRITICAL: Baseline graph is NEVER modified.
        Uses NetworkGraph.clone() to create independent copy.
        
        Args:
            baseline_graph: Original city graph (immutable)
            interventions: Single intervention or list of interventions
            
        Returns:
            New NetworkGraph with interventions applied
            
        Raises:
            ValueError: If intervention is invalid
        """
        # Ensure interventions is a list
        if isinstance(interventions, Intervention):
            interventions = [interventions]
        
        # Clone baseline (immutable guarantee)
        intervention_graph = baseline_graph.clone()
        
        # Apply each intervention deterministically
        for intervention in interventions:
            self._apply_single_intervention(intervention_graph, intervention)
        
        return intervention_graph
    
    def _apply_single_intervention(
        self,
        graph: NetworkGraph,
        intervention: Intervention
    ):
        """
        Apply a single intervention to graph (mutates graph in-place).
        
        Args:
            graph: NetworkGraph to modify
            intervention: Intervention to apply
            
        Raises:
            ValueError: If intervention is invalid
        """
        intervention_type = intervention.intervention_type
        station_id = intervention.station_id
        parameters = intervention.parameters
        
        if intervention_type == InterventionType.ADD_STATION:
            self._add_station(graph, station_id, intervention.zone_id, parameters)
        
        elif intervention_type == InterventionType.REMOVE_STATION:
            self._remove_station(graph, station_id)
        
        elif intervention_type == InterventionType.MODIFY_CAPACITY:
            self._modify_capacity(graph, station_id, parameters)
        
        elif intervention_type == InterventionType.MODIFY_SWAP_TIME:
            self._modify_swap_time(graph, station_id, parameters)
        
        elif intervention_type == InterventionType.MODIFY_CHARGERS:
            self._modify_chargers(graph, station_id, parameters)
        
        else:
            raise ValueError(f"Unknown intervention type: {intervention_type}")
    
    def _add_station(
        self,
        graph: NetworkGraph,
        station_id: str,
        zone_id: str,
        parameters: Dict
    ):
        """
        Add new station to graph.
        
        Args:
            graph: NetworkGraph to modify
            station_id: New station ID
            zone_id: Zone to add station to
            parameters: Station config (swap_bays, chargers_total, etc.)
            
        Raises:
            ValueError: If station already exists or zone doesn't exist
        """
        # Validate zone exists
        zones = graph.graph.graph.get("zones", {})
        if zone_id not in zones:
            raise ValueError(f"Zone {zone_id} does not exist")
        
        # Validate station doesn't already exist
        if station_id in graph.graph.nodes():
            raise ValueError(f"Station {station_id} already exists")
        
        # Add station node to graph
        graph.graph.add_node(
            station_id,
            zone_id=zone_id,
            swap_bays=parameters.get("swap_bays", 5),
            chargers_total=parameters.get("chargers_total", 5),
            inventory_current=parameters.get("inventory_current", 40),
            swap_time_sec=parameters.get("swap_time_sec", 300),
            queue_limit=parameters.get("queue_limit", 10)
        )
        
        # Add station to zone's station_ids
        zones[zone_id]["station_ids"].append(station_id)
        
        # Add edges to/from neighboring zones' stations
        # (Simple connectivity: connect to all stations in same zone and adjacent zones)
        for other_zone_id, other_zone_data in zones.items():
            for other_station_id in other_zone_data["station_ids"]:
                if other_station_id != station_id:
                    # Add bidirectional edges
                    graph.graph.add_edge(station_id, other_station_id, weight=1.0)
                    graph.graph.add_edge(other_station_id, station_id, weight=1.0)
    
    def _remove_station(self, graph: NetworkGraph, station_id: str):
        """
        Remove station from graph.
        
        Args:
            graph: NetworkGraph to modify
            station_id: Station to remove
            
        Raises:
            ValueError: If station doesn't exist
        """
        if station_id not in graph.graph.nodes():
            raise ValueError(f"Station {station_id} does not exist")
        
        # Get zone before removing
        zone_id = graph.graph.nodes[station_id].get("zone_id")
        
        # Remove from graph
        graph.graph.remove_node(station_id)
        
        # Remove from zone's station_ids
        if zone_id:
            zones = graph.graph.graph.get("zones", {})
            if zone_id in zones:
                zones[zone_id]["station_ids"] = [
                    sid for sid in zones[zone_id]["station_ids"]
                    if sid != station_id
                ]
    
    def _modify_capacity(
        self,
        graph: NetworkGraph,
        station_id: str,
        parameters: Dict
    ):
        """
        Modify station capacity (swap_bays, inventory).
        
        Args:
            graph: NetworkGraph to modify
            station_id: Station to modify
            parameters: New capacity values
            
        Raises:
            ValueError: If station doesn't exist
        """
        if station_id not in graph.graph.nodes():
            raise ValueError(f"Station {station_id} does not exist")
        
        node_data = graph.graph.nodes[station_id]
        
        if "swap_bays" in parameters:
            node_data["swap_bays"] = parameters["swap_bays"]
        
        if "inventory_current" in parameters:
            node_data["inventory_current"] = parameters["inventory_current"]
        
        if "queue_limit" in parameters:
            node_data["queue_limit"] = parameters["queue_limit"]
    
    def _modify_swap_time(
        self,
        graph: NetworkGraph,
        station_id: str,
        parameters: Dict
    ):
        """
        Modify station swap time.
        
        Args:
            graph: NetworkGraph to modify
            station_id: Station to modify
            parameters: New swap_time_sec value
            
        Raises:
            ValueError: If station doesn't exist or swap_time_sec not provided
        """
        if station_id not in graph.graph.nodes():
            raise ValueError(f"Station {station_id} does not exist")
        
        if "swap_time_sec" not in parameters:
            raise ValueError("swap_time_sec parameter required")
        
        graph.graph.nodes[station_id]["swap_time_sec"] = parameters["swap_time_sec"]
    
    def _modify_chargers(
        self,
        graph: NetworkGraph,
        station_id: str,
        parameters: Dict
    ):
        """
        Modify station charger count.
        
        Args:
            graph: NetworkGraph to modify
            station_id: Station to modify
            parameters: New chargers_total value
            
        Raises:
            ValueError: If station doesn't exist or chargers_total not provided
        """
        if station_id not in graph.graph.nodes():
            raise ValueError(f"Station {station_id} does not exist")
        
        if "chargers_total" not in parameters:
            raise ValueError("chargers_total parameter required")
        
        graph.graph.nodes[station_id]["chargers_total"] = parameters["chargers_total"]


def create_intervention(
    intervention_type: str,
    station_id: str,
    zone_id: Optional[str] = None,
    **parameters
) -> Intervention:
    """
    Helper function to create interventions with cleaner syntax.
    
    Args:
        intervention_type: Type string ("add_station", "modify_capacity", etc.)
        station_id: Station ID
        zone_id: Zone ID (for add_station)
        **parameters: Intervention parameters
        
    Returns:
        Intervention object
        
    Example:
        >>> add_station = create_intervention(
        ...     "add_station",
        ...     "ST_NEW_01",
        ...     zone_id="zone_01",
        ...     swap_bays=10,
        ...     chargers_total=15
        ... )
    """
    intervention_type_enum = InterventionType(intervention_type)
    return Intervention(intervention_type_enum, station_id, zone_id, parameters)
