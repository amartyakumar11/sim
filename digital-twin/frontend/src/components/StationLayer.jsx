/**
 * StationLayer: Renders stations as dots within zones.
 * 
 * - Positioned relative to parent zone
 * - Tooltip shows station metrics (swaps, lost swaps)
 * - Read-only visualization
 */

import React, { useState } from 'react';

const StationLayer = ({ cityGraph, stationTimelines, currentMinute }) => {
    const [hoveredStation, setHoveredStation] = useState(null);
    const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

    if (!cityGraph || !cityGraph.zones) {
        return null;
    }

    const zones = cityGraph.zones;
    const zoneIds = Object.keys(zones);
    const gridSize = Math.ceil(Math.sqrt(zoneIds.length));
    const zoneWidth = 140;
    const zoneHeight = 100;
    const padding = 20;

    // Build station positions
    const stationPositions = [];

    zoneIds.forEach((zoneId, index) => {
        const row = Math.floor(index / gridSize);
        const col = index % gridSize;
        const zoneX = col * (zoneWidth + padding) + padding;
        const zoneY = row * (zoneHeight + padding) + padding;

        const zoneData = zones[zoneId];
        const stationIds = zoneData.station_ids || [];

        // Position stations within zone (simple grid)
        const stationGridSize = Math.ceil(Math.sqrt(stationIds.length));
        const stationSpacing = Math.min(zoneWidth, zoneHeight) / (stationGridSize + 1);

        stationIds.forEach((stationId, sIndex) => {
            const sRow = Math.floor(sIndex / stationGridSize);
            const sCol = sIndex % stationGridSize;

            const stationX = zoneX + (sCol + 1) * stationSpacing;
            const stationY = zoneY + 50 + (sRow * stationSpacing / 2);

            const timeline = stationTimelines[stationId] || {
                swaps_total: 0,
                lost_swaps: 0,
                activePressure: null
            };

            stationPositions.push({
                id: stationId,
                x: stationX,
                y: stationY,
                zone: zoneId,
                swaps: timeline.swaps_total,
                lostSwaps: timeline.lost_swaps,
                activePressure: timeline.activePressure
            });
        });
    });

    const handleStationHover = (station, event) => {
        setHoveredStation(station);
        setTooltipPos({ x: event.clientX, y: event.clientY });
    };

    const handleStationLeave = () => {
        setHoveredStation(null);
    };

    // Determine station fill color based on state
    const getStationFill = (station) => {
        if (station.activePressure) {
            return '#FF5722'; // Orange for active pressure
        }
        if (station.lostSwaps > 0) {
            return '#f44336'; // Red for lost swaps
        }
        return '#2196F3'; // Blue for normal
    };

    return (
        <g className="station-layer">
            {stationPositions.map(station => (
                <g key={station.id}>
                    {/* Station dot */}
                    <circle
                        cx={station.x}
                        cy={station.y}
                        r={station.activePressure ? 8 : 6}
                        fill={getStationFill(station)}
                        stroke="white"
                        strokeWidth="2"
                        onMouseEnter={(e) => handleStationHover(station, e)}
                        onMouseLeave={handleStationLeave}
                        style={{
                            cursor: 'pointer',
                            transition: 'r 0.2s, fill 0.2s'
                        }}
                    />

                    {/* Station ID label (small) */}
                    <text
                        x={station.x}
                        y={station.y - 10}
                        textAnchor="middle"
                        fontSize="8"
                        fill="#333"
                        style={{ pointerEvents: 'none' }}
                    >
                        {station.id}
                    </text>
                </g>
            ))}

            {/* Tooltip */}
            {hoveredStation && (
                <foreignObject
                    x={tooltipPos.x - 400}
                    y={tooltipPos.y - 500}
                    width="220"
                    height="150"
                >
                    <div style={styles.tooltip}>
                        <div style={styles.tooltipTitle}>{hoveredStation.id}</div>
                        <div style={styles.tooltipRow}>
                            <strong>Zone:</strong> {hoveredStation.zone}
                        </div>
                        <div style={styles.tooltipRow}>
                            <strong>Total Swaps:</strong> {hoveredStation.swaps}
                        </div>
                        <div style={styles.tooltipRow}>
                            <strong>Lost Swaps:</strong>{' '}
                            <span style={{ color: hoveredStation.lostSwaps > 0 ? '#f44336' : '#4caf50' }}>
                                {hoveredStation.lostSwaps}
                            </span>
                        </div>
                        {hoveredStation.activePressure && (
                            <div style={styles.tooltipRow}>
                                <strong>Pressure:</strong>{' '}
                                <span style={{ color: '#FF5722' }}>
                                    {hoveredStation.activePressure.reason}
                                </span>
                            </div>
                        )}
                    </div>
                </foreignObject>
            )}
        </g>
    );
};

const styles = {
    tooltip: {
        backgroundColor: 'white',
        border: '2px solid #333',
        borderRadius: '4px',
        padding: '10px',
        fontSize: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        pointerEvents: 'none'
    },
    tooltipTitle: {
        fontWeight: 'bold',
        marginBottom: '5px',
        fontSize: '13px',
        color: '#2196F3'
    },
    tooltipRow: {
        marginTop: '3px'
    }
};

export default StationLayer;
