/**
 * Time Selectors for Playback
 * 
 * Pure helper functions for filtering observability data by minute.
 * These functions have NO side effects and are fully deterministic.
 */

/**
 * Get the minimum and maximum minutes from zone pressure data.
 * @param {Array} zonePressure - Array of zone pressure entries with minute field
 * @returns {{ minMinute: number, maxMinute: number }}
 */
export const getMinuteRange = (zonePressure) => {
    if (!zonePressure || zonePressure.length === 0) {
        return { minMinute: 0, maxMinute: 0 };
    }

    const minutes = zonePressure.map(entry => entry.minute);
    return {
        minMinute: Math.min(...minutes),
        maxMinute: Math.max(...minutes)
    };
};

/**
 * Filter zone pressure entries to only those matching the given minute.
 * @param {Array} zonePressure - Array of zone pressure entries
 * @param {number} minute - The current minute to filter by
 * @returns {Array} Filtered zone pressure entries for the given minute
 */
export const zonePressureAtMinute = (zonePressure, minute) => {
    if (!zonePressure || minute === null || minute === undefined) {
        return [];
    }

    return zonePressure.filter(entry => entry.minute === minute);
};

/**
 * Get cumulative zone pressure up to the given minute.
 * Returns the latest pressure reading for each zone up to (and including) the given minute.
 * @param {Array} zonePressure - Array of zone pressure entries
 * @param {number} minute - The current minute
 * @returns {Object} Map of zone_id -> latest pressure entry
 */
export const cumulativeZonePressure = (zonePressure, minute) => {
    if (!zonePressure || minute === null || minute === undefined) {
        return {};
    }

    const latestByZone = {};

    // Sort by minute ascending and pick the latest for each zone up to current minute
    const filtered = zonePressure
        .filter(entry => entry.minute <= minute)
        .sort((a, b) => a.minute - b.minute);

    for (const entry of filtered) {
        latestByZone[entry.zone] = entry;
    }

    return latestByZone;
};

/**
 * Get station state snapshot at a given minute from timeline.
 * This is a DETERMINISTIC, PURE function with no side effects.
 * 
 * @param {Array} timeline - Array of state entries with minute field
 * @param {number} minute - The target minute
 * @returns {Object|null} The last state entry at or before the given minute
 */
const getStationStateAtMinute = (timeline, minute) => {
    if (!timeline || !Array.isArray(timeline) || timeline.length === 0) {
        return null;
    }

    let last = null;
    for (const entry of timeline) {
        if (entry.minute > minute) break;
        last = entry;
    }
    return last;
};

/**
 * Determine station state at the given minute.
 * Resolves queue, charging, inventory from timeline array.
 * @param {Object} stationTimelines - Map of station_id -> timeline data
 * @param {number} minute - The current minute
 * @returns {Object} Map of station_id -> resolved state with queue/charging/inventory
 */
export const stationStateAtMinute = (stationTimelines, minute) => {
    if (!stationTimelines || minute === null || minute === undefined) {
        return {};
    }

    const result = {};

    for (const [stationId, stationData] of Object.entries(stationTimelines)) {
        // Resolve state from timeline array
        const timelineState = getStationStateAtMinute(stationData.timeline, minute);

        // Determine pressure state from inventory/queue
        let activePressure = null;
        if (timelineState) {
            if (timelineState.inventory === 0) {
                activePressure = { reason: 'battery_stockout' };
            } else if (timelineState.queue > timelineState.charging) {
                activePressure = { reason: 'swap_congestion' };
            }
        }

        result[stationId] = {
            station_id: stationId,
            zone: stationData.zone,
            chargers: stationData.chargers || 0,
            // Resolved state from timeline
            queue: timelineState?.queue ?? 0,
            charging: timelineState?.charging ?? 0,
            inventory: timelineState?.inventory ?? 0,
            activePressure
        };
    }

    return result;
};

/**
 * Determine rider state at the given minute.
 * For each rider, computes:
 * - completedSwaps: number of swaps completed up to this minute
 * - currentStationIndex: index of the last visited station
 * - isActive: whether the rider is still active at this minute
 * 
 * @param {Object} riderTraces - Map of rider_id -> trace data
 * @param {number} minute - The current minute
 * @returns {Object} Map of rider_id -> trace data with playback state attached
 */
export const riderStateAtMinute = (riderTraces, minute) => {
    if (!riderTraces || minute === null || minute === undefined) {
        return {};
    }

    const result = {};

    for (const [riderId, trace] of Object.entries(riderTraces)) {
        // Determine completed swaps based on minute
        // Since swap_minutes might not be in data, estimate based on total_swaps
        // and the minute range progression
        const swapStations = trace.swap_stations || [];
        const totalSwaps = trace.total_swaps || swapStations.length;

        // If trace has swap_minutes array, use it; otherwise estimate
        let completedSwaps = 0;
        let completedStations = [];

        if (trace.swap_minutes && Array.isArray(trace.swap_minutes)) {
            // Use explicit minute data
            for (let i = 0; i < trace.swap_minutes.length; i++) {
                if (trace.swap_minutes[i] <= minute) {
                    completedSwaps++;
                    completedStations.push(swapStations[i]);
                }
            }
        } else {
            // Fallback: assume all swaps are complete (static behavior)
            completedSwaps = totalSwaps;
            completedStations = [...swapStations];
        }

        // Determine if rider is active
        let isActive = trace.end_state === 'active';
        if (trace.end_minute !== undefined && trace.end_minute <= minute) {
            isActive = false;
        }

        result[riderId] = {
            ...trace,
            completedSwaps,
            completedStations,
            currentStationIndex: completedStations.length - 1,
            isActiveAtMinute: isActive
        };
    }

    return result;
};

/**
 * Format minute as human-readable time (HH:MM).
 * Assumes minutes are counted from midnight (minute 0 = 00:00).
 * @param {number} minute - Minute of the day (0-1439)
 * @returns {string} Formatted time string
 */
export const formatMinuteAsTime = (minute) => {
    if (minute === null || minute === undefined) {
        return '--:--';
    }

    const hours = Math.floor(minute / 60);
    const mins = minute % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
};
