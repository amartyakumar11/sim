/**
 * Sample Data Generator for Testing Visualization
 * 
 * Provides mock data that matches the structure of observability outputs.
 * Use this for testing before connecting to real backend endpoints.
 */

export const getSampleCityGraph = () => {
    return {
        "zones": {
            "zone_01": {
                "type": "commercial",
                "station_ids": ["ST_01_01", "ST_01_02"]
            },
            "zone_02": {
                "type": "residential",
                "station_ids": ["ST_02_01", "ST_02_02"]
            },
            "zone_03": {
                "type": "business",
                "station_ids": ["ST_03_01"]
            },
            "zone_04": {
                "type": "industrial",
                "station_ids": ["ST_04_01", "ST_04_02"]
            }
        }
    };
};

export const getSampleZonePressure = () => {
    return [
        {
            "zone": "zone_01",
            "minute": 615,
            "pressure_score": 12,
            "drivers": ["swap_congestion", "battery_stockout"]
        },
        {
            "zone": "zone_01",
            "minute": 616,
            "pressure_score": 15,
            "drivers": ["swap_congestion"]
        },
        {
            "zone": "zone_02",
            "minute": 630,
            "pressure_score": 3,
            "drivers": ["swap_congestion"]
        },
        {
            "zone": "zone_03",
            "minute": 620,
            "pressure_score": 8,
            "drivers": ["battery_starvation"]
        }
    ];
};

export const getSampleStationTimelines = () => {
    return {
        "ST_01_01": {
            "station_id": "ST_01_01",
            "zone": "zone_01",
            "swaps_total": 45,
            "lost_swaps": 3,
            "pressure_windows": [
                {
                    "start_minute": 615,
                    "end_minute": 625,
                    "reason": "swap_congestion"
                }
            ]
        },
        "ST_01_02": {
            "station_id": "ST_01_02",
            "zone": "zone_01",
            "swaps_total": 32,
            "lost_swaps": 1,
            "pressure_windows": []
        },
        "ST_02_01": {
            "station_id": "ST_02_01",
            "zone": "zone_02",
            "swaps_total": 28,
            "lost_swaps": 0,
            "pressure_windows": []
        },
        "ST_02_02": {
            "station_id": "ST_02_02",
            "zone": "zone_02",
            "swaps_total": 19,
            "lost_swaps": 0,
            "pressure_windows": []
        },
        "ST_03_01": {
            "station_id": "ST_03_01",
            "zone": "zone_03",
            "swaps_total": 38,
            "lost_swaps": 2,
            "pressure_windows": []
        },
        "ST_04_01": {
            "station_id": "ST_04_01",
            "zone": "zone_04",
            "swaps_total": 15,
            "lost_swaps": 0,
            "pressure_windows": []
        },
        "ST_04_02": {
            "station_id": "ST_04_02",
            "zone": "zone_04",
            "swaps_total": 12,
            "lost_swaps": 0,
            "pressure_windows": []
        }
    };
};

export const getSampleRiderTraces = () => {
    return {
        "R_001": {
            "rider_id": "R_001",
            "spawn_zone": "zone_01",
            "spawn_minute": 610,
            "total_swaps": 4,
            "swap_stations": ["ST_01_01", "ST_02_01", "ST_03_01", "ST_01_02"],
            "swap_minutes": [615, 620, 625, 632],
            "end_state": "active",
            "total_distance_km": 45.5
        },
        "R_002": {
            "rider_id": "R_002",
            "spawn_zone": "zone_02",
            "spawn_minute": 625,
            "total_swaps": 1,
            "swap_stations": ["ST_02_02"],
            "swap_minutes": [630],
            "end_state": "active",
            "total_distance_km": 12.0
        },
        "R_003": {
            "rider_id": "R_003",
            "spawn_zone": "zone_03",
            "spawn_minute": 618,
            "total_swaps": 2,
            "swap_stations": ["ST_03_01", "ST_04_01"],
            "swap_minutes": [620, 628],
            "end_state": "lost",
            "end_minute": 630
        }
    };
};
