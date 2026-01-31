/**
 * RiderPathLayer: Renders hero rider journey with playback support.
 * 
 * - Selects ONE rider deterministically (most swaps, longest journey)
 * - Draws polyline through swap stations UP TO current minute
 * - Marks swap points with numbered labels
 * - Highlights latest completed swap station
 * - Tooltip shows rider details with playback state
 * 
 * NO animation, NO physics, NO interpolation - discrete minute steps only.
 */

import React, { useState } from 'react';

const RiderPathLayer = ({ cityGraph, riderTraces, currentMinute }) => {
    const [hoveredRider, setHoveredRider] = useState(null);

    if (!cityGraph || !cityGraph.zones || !riderTraces || Object.keys(riderTraces).length === 0) {
        return null;
    }

    // Select hero rider deterministically
    const selectHeroRider = () => {
        const riders = Object.entries(riderTraces);

        if (riders.length === 0) return null;

        // Sort by: completedSwaps (desc), then total_swaps (desc), then rider_id (asc)
        riders.sort((a, b) => {
            const [idA, traceA] = a;
            const [idB, traceB] = b;

            // Primary: completed swaps (for playback visibility)
            const completedA = traceA.completedSwaps || traceA.total_swaps || 0;
            const completedB = traceB.completedSwaps || traceB.total_swaps || 0;
            if (completedB !== completedA) {
                return completedB - completedA;
            }

            // Secondary: total swaps
            if (traceB.total_swaps !== traceA.total_swaps) {
                return traceB.total_swaps - traceA.total_swaps;
            }

            // Tertiary: rider_id (deterministic tiebreak)
            return idA.localeCompare(idB);
        });

        return riders[0];
    };

    const heroRider = selectHeroRider();

    if (!heroRider) return null;

    const [riderId, riderTrace] = heroRider;

    // Use completedStations from time-filtered data, or fall back to all swaps
    const completedStations = riderTrace.completedStations || riderTrace.swap_stations || [];
    const completedSwaps = riderTrace.completedSwaps ?? riderTrace.total_swaps ?? 0;
    const isActiveAtMinute = riderTrace.isActiveAtMinute !== undefined
        ? riderTrace.isActiveAtMinute
        : riderTrace.end_state === 'active';

    if (completedStations.length === 0) {
        // Rider hasn't made any swaps yet at this minute - show spawn indicator only
        return (
            <g className="rider-path-layer">
                <foreignObject x={10} y={500} width="250" height="90">
                    <div style={styles.heroInfo}>
                        <div style={styles.heroTitle}>🎯 Hero Rider: {riderId}</div>
                        <div style={styles.heroRow}>
                            <strong>Status:</strong>{' '}
                            <span style={{ color: '#FF9800' }}>Waiting for first swap...</span>
                        </div>
                        <div style={styles.heroRow}>
                            <strong>Spawn Zone:</strong> {riderTrace.spawn_zone}
                        </div>
                    </div>
                </foreignObject>
            </g>
        );
    }

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

    // Build path points for COMPLETED swaps only
    const pathPoints = completedStations
        .map(stationId => stationPositions[stationId])
        .filter(pos => pos !== undefined);

    if (pathPoints.length === 0) return null;

    // Create polyline path
    const pathData = pathPoints
        .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
        .join(' ');

    // Determine last completed station (for highlighting)
    const lastIndex = pathPoints.length - 1;

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
            {pathPoints.map((point, index) => {
                const isLatest = index === lastIndex;

                return (
                    <g key={index}>
                        {/* Highlight ring for latest swap */}
                        {isLatest && (
                            <circle
                                cx={point.x}
                                cy={point.y}
                                r={14}
                                fill="none"
                                stroke="#E91E63"
                                strokeWidth="2"
                                style={{
                                    animation: 'none' // Discrete, no pulse
                                }}
                            />
                        )}

                        {/* Swap point circle */}
                        <circle
                            cx={point.x}
                            cy={point.y}
                            r={isLatest ? 12 : 10}
                            fill={isLatest ? '#E91E63' : '#9C27B0'}
                            stroke="white"
                            strokeWidth="2"
                        />

                        {/* Swap order label */}
                        <text
                            x={point.x}
                            y={point.y + 4}
                            textAnchor="middle"
                            fontSize={isLatest ? '14' : '12'}
                            fontWeight="bold"
                            fill="white"
                        >
                            {index + 1}
                        </text>
                    </g>
                );
            })}

            {/* Hero rider info tooltip (always visible) */}
            <foreignObject
                x={10}
                y={500}
                width="280"
                height="110"
            >
                <div style={styles.heroInfo}>
                    <div style={styles.heroTitle}>🎯 Hero Rider: {riderId}</div>
                    <div style={styles.heroRow}>
                        <strong>Swaps:</strong> {completedSwaps} / {riderTrace.total_swaps}
                    </div>
                    <div style={styles.heroRow}>
                        <strong>Status:</strong>{' '}
                        <span style={{
                            color: isActiveAtMinute ? '#4caf50' : '#f44336'
                        }}>
                            {isActiveAtMinute ? 'Active' : (riderTrace.end_state || 'Inactive')}
                        </span>
                    </div>
                    {riderTrace.total_distance_km && (
                        <div style={styles.heroRow}>
                            <strong>Distance:</strong> {riderTrace.total_distance_km.toFixed(1)} km
                        </div>
                    )}
                    {completedStations.length > 0 && (
                        <div style={styles.heroRow}>
                            <strong>Last Station:</strong>{' '}
                            <span style={{ color: '#E91E63' }}>
                                {completedStations[completedStations.length - 1]}
                            </span>
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
