/**
 * Demand Forecasting Utility
 * Predicts future inventory based on recent historical trends.
 * logic ported from Python backend for client-side agility.
 */

export const predictStationDemand = (stationId, timeline, currentMinute) => {
    // 1. Basic Validation
    if (!timeline || !timeline.states) {
        return { forecast: [], risk_level: 'unknown', error: 'No history' };
    }

    // Need at least 30 mins of history
    if (currentMinute < 30) {
        return { forecast: [], risk_level: 'low', message: 'Gathering data...' };
    }

    // 2. Filter relevant history (last 30-60 mins)
    // we use a sliding window to calculate the rate of change
    const windowSize = 30; // minutes
    const relevantStates = timeline.states.filter(
        s => s.minute <= currentMinute && s.minute > currentMinute - windowSize
    );

    if (relevantStates.length < 5) {
        return { forecast: [], risk_level: 'unknown', message: 'Insufficient recent data' };
    }

    // 3. Calculate Consumption Rate (Batteries/min)
    // defined as: (EndInventory - StartInventory) / TimeDelta
    // Negative rate means inventory is dropping.
    const startState = relevantStates[0];
    const endState = relevantStates[relevantStates.length - 1];

    // Inventory might be undefined in some raw logs, default to 10
    const startInv = startState.inventory !== undefined ? startState.inventory : 10;
    const endInv = endState.inventory !== undefined ? endState.inventory : 10;

    const timeDelta = endState.minute - startState.minute;
    if (timeDelta === 0) return { forecast: [], risk_level: 'low' };

    const netChangeRate = (endInv - startInv) / timeDelta;

    // 4. Project Future (Next 60 mins)
    const forecast = [];
    let currentInv = endInv;
    let riskLevel = 'low';

    // We'll generate a point every 10 minutes
    for (let i = 10; i <= 60; i += 10) {
        // Linear projection
        let predictedInv = currentInv + (netChangeRate * i);

        // Clamp values
        predictedInv = Math.max(0, Math.min(20, predictedInv));

        forecast.push({
            minute: currentMinute + i,
            predicted_inventory: parseFloat(predictedInv.toFixed(1))
        });

        // Risk Assessment
        if (predictedInv < 1) {
            riskLevel = 'critical';
        } else if (predictedInv < 3 && riskLevel !== 'critical') {
            riskLevel = 'high';
        }
    }

    return {
        station_id: stationId,
        current_inventory: endInv,
        net_flow_rate: parseFloat(netChangeRate.toFixed(2)),
        risk_level: riskLevel,
        forecast: forecast
    };
};
