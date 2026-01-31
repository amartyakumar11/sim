"""
Simulation Configuration Constants for Level-2 Digital Twin.

Defines global constants for deterministic rider lifecycle simulation.
"""

# Timestep configuration
SIMULATION_TIME_STEP_MIN = 1  # 1-minute timesteps

# Battery configuration
BATTERY_FULL_RANGE_KM = 80
BATTERY_SWAP_THRESHOLD_KM = 8
BATTERY_CRITICAL_THRESHOLD_KM = 3

# Movement configuration
AVG_SPEED_KMPH = 30
KM_PER_MIN = AVG_SPEED_KMPH / 60  # 0.5 km/min
MAX_ZONE_DWELL_MIN = 20

# Zone type priority for deterministic zone selection
ZONE_TYPE_PRIORITY = {
    "high-density": 3,
    "commercial": 3,
    "business": 3,
    "residential": 2,
    "fleet": 1,
    "industrial": 1,
    "transportation": 1,
    "unknown": 0
}

# Station selection scoring weights
STATION_BATTERY_AVAILABLE_SCORE = 100
STATION_QUEUE_PENALTY_PER_RIDER = 5
STATION_ZONE_HOP_PENALTY = 10
