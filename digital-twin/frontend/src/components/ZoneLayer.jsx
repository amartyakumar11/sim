/**
 * ZoneLayer: Renders city zones with pressure overlay.
 * 
 * - Baseline: gray rectangles for zones
 * - Overlay: color-coded pressure (green/yellow/red)
 * - Tooltip: zone info on hover
 * 
 * Read-only - NO computation, just visual mapping.
 */

import React, { useState } from 'react';

const ZoneLayer = ({ cityGraph, zonePressure }) => {
    const [hoveredZone, setHoveredZone] = useState(null);
    const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

    if (!cityGraph || !cityGraph.zones) {
        return null;
    }

    const zones = cityGraph.zones;

    // Compute zone layout (simple grid for now)
    const zoneIds = Object.keys(zones);
    const gridSize = Math.ceil(Math.sqrt(zoneIds.length));
    const zoneWidth = 140;
    const zoneHeight = 100;
    const padding = 20;

    // Compute peak pressure per zone
    const zonePeakPressure = {};
    zonePressure.forEach(record => {
        const zone = record.zone;
        if (!zonePeakPressure[zone]) {
            zonePeakPressure[zone] = { score: 0, drivers: [] };
        }
        if (record.pressure_score > zonePeakPressure[zone].score) {
            zonePeakPressure[zone] = {
                score: record.pressure_score,
                drivers: record.drivers
            };
        }
    });

    // Determine pressure color (deterministic thresholds)
    const getPressureColor = (score) => {
        if (score === 0) return '#e0e0e0'; // Gray (no pressure)
        if (score < 5) return 'rgba(76, 175, 80, 0.3)'; // Green (low)
        if (score < 10) return 'rgba(255, 235, 59, 0.4)'; // Yellow (medium)
        return 'rgba(244, 67, 54, 0.4)'; // Red (high)
    };

    const handleZoneHover = (zoneId, event) => {
        setHoveredZone(zoneId);
        setTooltipPos({ x: event.clientX, y: event.clientY });
    };

    const handleZoneLeave = () => {
        setHoveredZone(null);
    };

    return (
        <g className="zone-layer">
            {zoneIds.map((zoneId, index) => {
                const row = Math.floor(index / gridSize);
                const col = index % gridSize;
                const x = col * (zoneWidth + padding) + padding;
                const y = row * (zoneHeight + padding) + padding;

                const zoneData = zones[zoneId];
                const pressure = zonePeakPressure[zoneId] || { score: 0, drivers: [] };
                const color = getPressureColor(pressure.score);

                return (
                    <g key={zoneId}>
                        {/* Zone rectangle with pressure color */}
                        <rect
                            x={x}
                            y={y}
                            width={zoneWidth}
                            height={zoneHeight}
                            fill={color}
                            stroke="#666"
                            strokeWidth="2"
                            rx="4"
                            onMouseEnter={(e) => handleZoneHover(zoneId, e)}
                            onMouseLeave={handleZoneLeave}
                            style={{ cursor: 'pointer' }}
                        />

                        {/* Zone label */}
                        <text
                            x={x + zoneWidth / 2}
                            y={y + 20}
                            textAnchor="middle"
                            fontSize="12"
                            fontWeight="bold"
                            fill="#333"
                        >
                            {zoneId}
                        </text>

                        {/* Zone type */}
                        <text
                            x={x + zoneWidth / 2}
                            y={y + 35}
                            textAnchor="middle"
                            fontSize="10"
                            fill="#666"
                        >
                            {zoneData.type}
                        </text>

                        {/* Pressure indicator */}
                        {pressure.score > 0 && (
                            <text
                                x={x + zoneWidth / 2}
                                y={y + zoneHeight - 10}
                                textAnchor="middle"
                                fontSize="11"
                                fontWeight="bold"
                                fill="#d32f2f"
                            >
                                ⚠️ Peak: {pressure.score}
                            </text>
                        )}
                    </g>
                );
            })}

            {/* Tooltip */}
            {hoveredZone && zonePeakPressure[hoveredZone] && (
                <foreignObject
                    x={tooltipPos.x - 400}
                    y={tooltipPos.y - 500}
                    width="200"
                    height="100"
                >
                    <div style={styles.tooltip}>
                        <div style={styles.tooltipTitle}>{hoveredZone}</div>
                        <div style={styles.tooltipRow}>
                            <strong>Peak Pressure:</strong> {zonePeakPressure[hoveredZone].score}
                        </div>
                        <div style={styles.tooltipRow}>
                            <strong>Drivers:</strong> {zonePeakPressure[hoveredZone].drivers.join(', ') || 'None'}
                        </div>
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
        fontSize: '13px'
    },
    tooltipRow: {
        marginTop: '3px'
    }
};

export default ZoneLayer;
