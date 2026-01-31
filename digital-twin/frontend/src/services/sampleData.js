/**
 * Sample Data Generator for Testing Visualization
 * 
 * Provides mock data that matches the structure of observability outputs.
 * Includes minute-based timeline data for station state playback.
 * 
 * STRUCTURE:
 * - stationTimelines[stationId].timeline = array of state snapshots per minute
 * - Each snapshot: { minute, queue, charging, chargers, inventory }
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
            "zone": "zone_01",
            "minute": 618,
            "pressure_score": 18,
            "drivers": ["swap_congestion", "battery_stockout"]
        },
        {
            "zone": "zone_01",
            "minute": 620,
            "pressure_score": 10,
            "drivers": ["swap_congestion"]
        },
        {
            "zone": "zone_02",
            "minute": 625,
            "pressure_score": 5,
            "drivers": ["swap_congestion"]
        },
        {
            "zone": "zone_02",
            "minute": 630,
            "pressure_score": 3,
            "drivers": []
        },
        {
            "zone": "zone_03",
            "minute": 620,
            "pressure_score": 8,
            "drivers": ["battery_starvation"]
        },
        {
            "zone": "zone_04",
            "minute": 622,
            "pressure_score": 2,
            "drivers": []
        }
    ];
};

/**
 * Station timelines with per-minute state snapshots
 * Each timeline entry contains operational state at that minute.
 * 
 * Fields per entry:
 * - minute: simulation minute
 * - queue: riders waiting for swap
 * - charging: batteries currently charging
 * - chargers: total charger capacity
 * - inventory: available charged batteries
 */
export const getSampleStationTimelines = () => {
    return {
        "ST_01_01": {
            "station_id": "ST_01_01",
            "zone": "zone_01",
            "chargers": 4,
            "timeline": [
                { "minute": 615, "queue": 0, "charging": 2, "inventory": 10 },
                { "minute": 616, "queue": 2, "charging": 4, "inventory": 8 },
                { "minute": 617, "queue": 3, "charging": 4, "inventory": 5 },
                { "minute": 618, "queue": 5, "charging": 4, "inventory": 2 },
                { "minute": 619, "queue": 4, "charging": 4, "inventory": 0 },  // Stockout!
                { "minute": 620, "queue": 3, "charging": 4, "inventory": 1 },
                { "minute": 621, "queue": 2, "charging": 4, "inventory": 3 },
                { "minute": 622, "queue": 1, "charging": 3, "inventory": 5 },
                { "minute": 623, "queue": 0, "charging": 2, "inventory": 7 },
                { "minute": 624, "queue": 0, "charging": 2, "inventory": 9 },
                { "minute": 625, "queue": 1, "charging": 2, "inventory": 8 },
                { "minute": 626, "queue": 0, "charging": 2, "inventory": 10 },
                { "minute": 627, "queue": 0, "charging": 1, "inventory": 11 },
                { "minute": 628, "queue": 1, "charging": 2, "inventory": 10 },
                { "minute": 629, "queue": 0, "charging": 2, "inventory": 10 },
                { "minute": 630, "queue": 0, "charging": 1, "inventory": 11 }
            ]
        },
        "ST_01_02": {
            "station_id": "ST_01_02",
            "zone": "zone_01",
            "chargers": 3,
            "timeline": [
                { "minute": 615, "queue": 0, "charging": 1, "inventory": 8 },
                { "minute": 616, "queue": 1, "charging": 2, "inventory": 6 },
                { "minute": 617, "queue": 2, "charging": 3, "inventory": 4 },
                { "minute": 618, "queue": 3, "charging": 3, "inventory": 2 },
                { "minute": 619, "queue": 2, "charging": 3, "inventory": 1 },
                { "minute": 620, "queue": 1, "charging": 3, "inventory": 2 },
                { "minute": 621, "queue": 0, "charging": 2, "inventory": 4 },
                { "minute": 622, "queue": 0, "charging": 2, "inventory": 5 },
                { "minute": 623, "queue": 0, "charging": 1, "inventory": 6 },
                { "minute": 624, "queue": 1, "charging": 2, "inventory": 5 },
                { "minute": 625, "queue": 0, "charging": 2, "inventory": 6 },
                { "minute": 626, "queue": 0, "charging": 1, "inventory": 7 },
                { "minute": 627, "queue": 0, "charging": 1, "inventory": 7 },
                { "minute": 628, "queue": 0, "charging": 1, "inventory": 8 },
                { "minute": 629, "queue": 0, "charging": 0, "inventory": 8 },
                { "minute": 630, "queue": 0, "charging": 1, "inventory": 8 }
            ]
        },
        "ST_02_01": {
            "station_id": "ST_02_01",
            "zone": "zone_02",
            "chargers": 3,
            "timeline": [
                { "minute": 615, "queue": 0, "charging": 1, "inventory": 12 },
                { "minute": 618, "queue": 0, "charging": 1, "inventory": 11 },
                { "minute": 620, "queue": 1, "charging": 2, "inventory": 10 },
                { "minute": 622, "queue": 0, "charging": 2, "inventory": 11 },
                { "minute": 625, "queue": 2, "charging": 3, "inventory": 8 },
                { "minute": 627, "queue": 1, "charging": 2, "inventory": 9 },
                { "minute": 630, "queue": 0, "charging": 1, "inventory": 10 }
            ]
        },
        "ST_02_02": {
            "station_id": "ST_02_02",
            "zone": "zone_02",
            "chargers": 2,
            "timeline": [
                { "minute": 615, "queue": 0, "charging": 0, "inventory": 6 },
                { "minute": 620, "queue": 0, "charging": 1, "inventory": 6 },
                { "minute": 625, "queue": 1, "charging": 2, "inventory": 5 },
                { "minute": 628, "queue": 0, "charging": 1, "inventory": 5 },
                { "minute": 630, "queue": 0, "charging": 1, "inventory": 6 }
            ]
        },
        "ST_03_01": {
            "station_id": "ST_03_01",
            "zone": "zone_03",
            "chargers": 4,
            "timeline": [
                { "minute": 615, "queue": 0, "charging": 2, "inventory": 15 },
                { "minute": 618, "queue": 1, "charging": 3, "inventory": 12 },
                { "minute": 620, "queue": 3, "charging": 4, "inventory": 8 },
                { "minute": 621, "queue": 4, "charging": 4, "inventory": 5 },
                { "minute": 622, "queue": 5, "charging": 4, "inventory": 2 },  // Congested
                { "minute": 623, "queue": 4, "charging": 4, "inventory": 3 },
                { "minute": 625, "queue": 2, "charging": 3, "inventory": 6 },
                { "minute": 628, "queue": 1, "charging": 2, "inventory": 9 },
                { "minute": 630, "queue": 0, "charging": 2, "inventory": 11 }
            ]
        },
        "ST_04_01": {
            "station_id": "ST_04_01",
            "zone": "zone_04",
            "chargers": 2,
            "timeline": [
                { "minute": 615, "queue": 0, "charging": 0, "inventory": 8 },
                { "minute": 620, "queue": 0, "charging": 1, "inventory": 8 },
                { "minute": 625, "queue": 1, "charging": 2, "inventory": 6 },
                { "minute": 628, "queue": 0, "charging": 1, "inventory": 7 },
                { "minute": 630, "queue": 0, "charging": 1, "inventory": 7 }
            ]
        },
        "ST_04_02": {
            "station_id": "ST_04_02",
            "zone": "zone_04",
            "chargers": 2,
            "timeline": [
                { "minute": 615, "queue": 0, "charging": 1, "inventory": 5 },
                { "minute": 618, "queue": 1, "charging": 2, "inventory": 4 },
                { "minute": 620, "queue": 2, "charging": 2, "inventory": 2 },
                { "minute": 621, "queue": 3, "charging": 2, "inventory": 0 },  // Stockout!
                { "minute": 622, "queue": 2, "charging": 2, "inventory": 1 },
                { "minute": 623, "queue": 1, "charging": 2, "inventory": 2 },
                { "minute": 625, "queue": 0, "charging": 1, "inventory": 4 },
                { "minute": 628, "queue": 0, "charging": 1, "inventory": 5 },
                { "minute": 630, "queue": 0, "charging": 0, "inventory": 5 }
            ]
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
