/**
 * RiderPathLayer: Renders hero rider journey.
 * 
 * - Selects ONE rider deterministically (most swaps, longest journey)
 * - Draws polyline through swap stations
 * - Marks swap points with numbered labels
 * - Tooltip shows rider details
 * 
 * NO animation, NO time slider - static visualization only.
 */

import React, { useState } from 'react';

const RiderPathLayer = ({ cityGraph, riderTraces }) => {
    const [hoveredRider, setHoveredRider] = useState(null);

    if (!cityGraph || !cityGraph.zones || !riderTraces || Object.keys(riderTraces).length === 0) {
        return null;
    }

    // Select hero rider deterministically
    const selectHeroRider = () => {
        const riders = Object.entries(riderTraces);

        if (riders.length === 0) return null;

        // Sort by: total_swaps (desc), then swap_stations.length (desc), then rider_id (asc)
        riders.sort((a, b) => {
            const [idA, traceA] = a;
            const [idB, traceB] = b;

            // Primary: total swaps
            if (traceB.total_swaps !== traceA.total_swaps) {
                return traceB.total_swaps - traceA.total_swaps;
            }

            // Secondary: journey length (number of stations visited)
            const lenA = (traceA.swap_stations || []).length;
            const lenB = (traceB.swap_stations || []).length;
            if (lenB !== lenA) {
                return lenB - lenA;
            }

            // Tertiary: rider_id (deterministic tiebreak)
            return idA.localeCompare(idB);
        });

        return riders[0];
    };

    const heroRider = selectHeroRider();

    if (!heroRider) return null;

    const [riderId, riderTrace] = heroRider;
    const swapStations = riderTrace.swap_stations || [];

    if (swapStations.length === 0) return null;

    // Build station position map
    const zones = cityGraph.zones;
    const zoneIds = Object.keys(zones);
    const gridSize = Math.ceil(Math.sqrt(zoneIds.length));
    const zoneWidth = 140;
    const zoneHeight = 100;
    const padding = 20;

    const stationPositions = {};

    zoneIds.forEach((zoneId, index) => {
        const row = Math.floor(index / gridSize);
        const col = index % gridSize;
        const zoneX = col * (zoneWidth + padding) + padding;
        const zoneY = row * (zoneHeight + padding) + padding;

        const zoneData = zones[zoneId];
        const stationIds = zoneData.station_ids || [];

        const stationGridSize = Math.ceil(Math.sqrt(stationIds.length));
        const stationSpacing = Math.min(zoneWidth, zoneHeight) / (stationGridSize + 1);

        stationIds.forEach((stationId, sIndex) => {
            const sRow = Math.floor(sIndex / stationGridSize);
            const sCol = sIndex % stationGridSize;

            const stationX = zoneX + (sCol + 1) * stationSpacing;
            const stationY = zoneY + 50 + (sRow * stationSpacing / 2);

            stationPositions[stationId] = { x: stationX, y: stationY };
        });
    });

    // Build path points
    const pathPoints = swapStations
        .map(stationId => stationPositions[stationId])
        .filter(pos => pos !== undefined);

    if (pathPoints.length === 0) return null;

    // Create polyline path
    const pathData = pathPoints
        .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
        .join(' ');

    return (
        <g className="rider-path-layer">
            {/* Rider journey path */}
            <path
                d={pathData}
                fill="none"
                stroke="#9C27B0"
                strokeWidth="3"
                strokeDasharray="5,5"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredRider(riderId)}
                onMouseLeave={() => setHoveredRider(null)}
            />

            {/* Swap point markers */}
            {pathPoints.map((point, index) => (
                <g key={index}>
                    {/* Swap point circle */}
                    <circle
                        cx={point.x}
                        cy={point.y}
                        r={10}
                        fill="#9C27B0"
                        stroke="white"
                        strokeWidth="2"
                    />

                    {/* Swap order label */}
                    <text
                        x={point.x}
                        y={point.y + 4}
                        textAnchor="middle"
                        fontSize="12"
                        fontWeight="bold"
                        fill="white"
                    >
                        {index + 1}
                    </text>
                </g>
            ))}

            {/* Hero rider info tooltip (always visible) */}
            <foreignObject
                x={10}
                y={500}
                width="250"
                height="90"
            >
                <div style={styles.heroInfo}>
                    <div style={styles.heroTitle}>🎯 Hero Rider: {riderId}</div>
                    <div style={styles.heroRow}>
                        <strong>Total Swaps:</strong> {riderTrace.total_swaps}
                    </div>
                    <div style={styles.heroRow}>
                        <strong>End State:</strong>{' '}
                        <span style={{
                            color: riderTrace.end_state === 'active' ? '#4caf50' : '#f44336'
                        }}>
                            {riderTrace.end_state}
                        </span>
                    </div>
                    {riderTrace.total_distance_km && (
                        <div style={styles.heroRow}>
                            <strong>Distance:</strong> {riderTrace.total_distance_km.toFixed(1)} km
                        </div>
                    )}
                </div>
            </foreignObject>
        </g>
    );
};

const styles = {
    heroInfo: {
        backgroundColor: 'rgba(156, 39, 176, 0.9)',
        color: 'white',
        border: '2px solid #7B1FA2',
        borderRadius: '6px',
        padding: '10px',
        fontSize: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
    },
    heroTitle: {
        fontWeight: 'bold',
        marginBottom: '5px',
        fontSize: '14px'
    },
    heroRow: {
        marginTop: '3px'
    }
};

export default RiderPathLayer;
