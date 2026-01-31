/**
 * CityMapView: Map-based visualization for the Digital Twin
 * 
 * Uses MapLibre with OpenStreetMap for a real map background.
 * Renders battery swap stations from city_graph_lucknow.json.
 * Integrates with the playback system for time-based visualization.
 * 
 * This is a READ-ONLY visualization - NO simulation logic.
 */

import React, { useState, useEffect, useMemo } from 'react';
import Map, { Marker, Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { BatteryCharging, User, AlertCircle } from 'lucide-react';

// --------------------------------------------------------
// CONFIGURATION - LUCKNOW
// --------------------------------------------------------
const LUCKNOW_CENTER = { lat: 26.85, lon: 80.95 };
const INITIAL_ZOOM = 11.5;

// --------------------------------------------------------
// COMPONENT
// --------------------------------------------------------
const CityMapView = ({
    cityGraph,
    zonePressure = {},
    stationTimelines = {},

    riderTraces = {},
    recommendations = [],
    currentMinute = null
}) => {
    const [viewState, setViewState] = useState({
        longitude: LUCKNOW_CENTER.lon,
        latitude: LUCKNOW_CENTER.lat,
        zoom: INITIAL_ZOOM,
        pitch: 45
    });

    const [hoveredStation, setHoveredStation] = useState(null);
    const [lucknowData, setLucknowData] = useState(null);
    const [loadError, setLoadError] = useState(null);

    // STEP 1: Load Lucknow City Graph
    useEffect(() => {
        fetch('/city_graph_lucknow.json')
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: Failed to load city graph`);
                }
                return res.json();
            })
            .then(data => {
                setLucknowData(data);
                setLoadError(null);
            })
            .catch(err => {
                console.error('Failed to load city_graph_lucknow.json:', err);
                setLoadError(err.message);
            });
    }, []);

    // Get stations from loaded data
    const stations = useMemo(() => {
        if (!lucknowData || !lucknowData.stations) return [];
        return lucknowData.stations;
    }, [lucknowData]);

    // Build a lookup map for station coordinates
    const stationCoordsMap = useMemo(() => {
        const map = {};
        stations.forEach(station => {
            map[station.station_id] = {
                lat: station.latitude,
                lon: station.longitude,
                zone: station.zone_id,
                swap_bays: station.swap_bays,
                chargers_total: station.chargers_total
            };
        });
        return map;
    }, [stations]);

    // Get station state from timelines - includes queue, charging, inventory
    const getStationState = (stationId) => {
        const state = stationTimelines[stationId];
        if (!state) {
            return {
                queue: 0,
                charging: 0,
                inventory: 10,
                chargers: 4,
                activePressure: null
            };
        }
        return state;
    };

    // Determine station color based on state (STEP 4)
    // 🟢 Green → queue === 0
    // 🟡 Yellow → queue > 0 AND inventory > 0
    // 🔴 Red → inventory === 0 OR queue > chargers
    const getStationColor = (state) => {
        const isStockout = state.inventory === 0;
        const isCongested = state.queue > state.chargers;

        if (isStockout) {
            return '#ef4444'; // Red (Stockout)
        }
        if (state.inventory < 3) {
            return '#f59e0b'; // Yellow (Low Inventory / Pressure)
        }
        return '#22c55e'; // Green (Healthy)
    };

    // Build rider path GeoJSON for active riders and redirections (manhattan style)
    const riderPathData = useMemo(() => {
        const features = [];

        Object.entries(riderTraces).forEach(([riderId, trace]) => {
            // 1. Draw Redirections (ACTIVE EVENT)
            if (trace.redirections) {
                trace.redirections.forEach(redir => {
                    // Only show if it happened recently (within last 15 mins)
                    if (currentMinute && redir.minute <= currentMinute && redir.minute > currentMinute - 15) {
                        const fromStation = stationCoordsMap[redir.from_station];
                        const toStation = stationCoordsMap[redir.to_station];

                        if (fromStation && toStation) {
                            // MANHATTAN INTERPOLATION (L-Shape)
                            // Point A -> Corner -> Point B
                            const corner = [toStation.lon, fromStation.lat];

                            features.push({
                                type: 'Feature',
                                properties: {
                                    riderId,
                                    type: 'redirection',
                                    minute: redir.minute
                                },
                                geometry: {
                                    type: 'LineString',
                                    coordinates: [
                                        [fromStation.lon, fromStation.lat],
                                        corner,
                                        [toStation.lon, toStation.lat]
                                    ]
                                }
                            });
                        }
                    }
                });
            }

            // 2. Existing swap paths can be kept simple or removed to reduce clutter
            // (Keeping simpler direct lines for completed swaps history)
            const completedStations = trace.completedStations || trace.swap_stations || [];
            if (completedStations.length >= 2) {
                const coordinates = completedStations
                    .map(sid => stationCoordsMap[sid] ? [stationCoordsMap[sid].lon, stationCoordsMap[sid].lat] : null)
                    .filter(c => c !== null);

                if (coordinates.length >= 2) {
                    features.push({
                        type: 'Feature',
                        properties: { riderId, type: 'history' },
                        geometry: { type: 'LineString', coordinates }
                    });
                }
            }
        });

        return {
            type: 'FeatureCollection',
            features
        };
    }, [riderTraces, stationCoordsMap, currentMinute]);

    // GENERATE ACTIVE RIDER CROWD
    // Since queues are often 0 due to rapid redirection, we visualize ALL active riders
    // to show the scale of the simulation.
    const activeRiderData = useMemo(() => {
        const features = [];

        Object.entries(riderTraces).forEach(([riderId, trace]) => {
            // Check if rider is active in this simulation window
            // Simplified: If they have swapped recently or are about to swap
            const swaps = trace.swap_minutes || [];
            const lastSwap = swaps.filter(m => m <= currentMinute).pop();
            const nextSwap = swaps.find(m => m > currentMinute);

            // If rider has entered the system (lastSwap exists) and hasn't finished forever (nextSwap exists or recently finished)
            // Or if they are currently redirecting
            if (lastSwap || (trace.redirections && trace.redirections.some(r => r.minute <= currentMinute && r.minute > currentMinute - 20))) {

                let lat, lon;

                // If redirecting, interpolate position
                const activeRedir = trace.redirections?.find(r => r.minute <= currentMinute && r.minute > currentMinute - 15);

                if (activeRedir) {
                    const from = stationCoordsMap[activeRedir.from_station];
                    const to = stationCoordsMap[activeRedir.to_station];
                    if (from && to) {
                        // Linear interpolation based on time elapsed in redirection (15 mins duration assumed)
                        const elapsed = currentMinute - activeRedir.minute;
                        const progress = Math.min(elapsed / 15, 1);
                        lat = from.lat + (to.lat - from.lat) * progress;
                        lon = from.lon + (to.lon - from.lon) * progress;
                    }
                } else if (lastSwap) {
                    // Stationary at last station (scattered slightly)
                    const stationId = trace.swap_stations[swaps.indexOf(lastSwap)];
                    const station = stationCoordsMap[stationId];
                    if (station) {
                        // Deterministic scatter based on RiderID hash to keep them stable
                        const hash = riderId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                        const angle = (hash % 360) * (Math.PI / 180);
                        const radius = 0.00015 + ((hash % 10) * 0.00002);
                        lat = station.lat + Math.sin(angle) * radius;
                        lon = station.lon + Math.cos(angle) * radius;
                    }
                }

                if (lat && lon) {
                    features.push({
                        type: 'Feature',
                        properties: {
                            type: 'active_rider',
                            riderId: riderId
                        },
                        geometry: {
                            type: 'Point',
                            coordinates: [lon, lat]
                        }
                    });
                }
            }
        });

        return {
            type: 'FeatureCollection',
            features
        };
    }, [riderTraces, stationCoordsMap, currentMinute]);

    // Get hero rider (most swaps)
    const heroRider = useMemo(() => {
        const riders = Object.entries(riderTraces);
        if (riders.length === 0) return null;

        riders.sort((a, b) => {
            const swapsA = a[1].completedSwaps || a[1].total_swaps || 0;
            const swapsB = b[1].completedSwaps || b[1].total_swaps || 0;
            return swapsB - swapsA;
        });

        return { id: riders[0][0], ...riders[0][1] };
    }, [riderTraces]);

    // Hero rider current position (last completed station)
    const heroPosition = useMemo(() => {
        if (!heroRider) return null;
        const stationsList = heroRider.completedStations || heroRider.swap_stations || [];
        if (stationsList.length === 0) return null;

        const lastStation = stationsList[stationsList.length - 1];
        return stationCoordsMap[lastStation] || null;
    }, [heroRider, stationCoordsMap]);

    // STEP 5: Safety check - show error state if load failed
    if (loadError) {
        return (
            <div style={styles.errorContainer}>
                <div style={styles.errorBox}>
                    <h3 style={styles.errorTitle}>⚠️ Failed to Load Lucknow Map</h3>
                    <p style={styles.errorText}>{loadError}</p>
                    <p style={styles.errorHint}>Make sure city_graph_lucknow.json is in the public folder.</p>
                </div>
            </div>
        );
    }

    // Show loading state
    if (!lucknowData) {
        return (
            <div style={styles.loadingContainer}>
                <div style={styles.loadingSpinner}>Loading Lucknow stations...</div>
            </div>
        );
    }

    return (
        <div style={{ width: '100%', height: '100vh', position: 'relative' }}>
            <Map
                {...viewState}
                onMove={evt => setViewState(evt.viewState)}
                mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
                style={{ width: '100%', height: '100%' }}
            >
                {/* Rider paths (Redirections = Manhattan, History = Straight) */}
                <Source id="rider-paths" type="geojson" data={riderPathData}>
                    {/* History lines (faint) */}
                    <Layer
                        id="rider-history-line"
                        type="line"
                        filter={['==', 'type', 'history']}
                        paint={{
                            'line-color': '#a855f7',
                            'line-width': 1,
                            'line-opacity': 0.3
                        }}
                    />
                    {/* Redirection lines (Bold, Animated look) */}
                    <Layer
                        id="rider-redirect-line"
                        type="line"
                        filter={['==', 'type', 'redirection']}
                        layout={{
                            'line-join': 'round',
                            'line-cap': 'round'
                        }}
                        paint={{
                            'line-color': '#f59e0b',
                            'line-width': 4,
                            'line-dasharray': [2, 1], // MapLibre quirk: this works in paint for some versions but better to be safe
                            'line-opacity': 0.9
                        }}
                    />
                </Source>

                {/* Queue Visualization Source */}
                <Source id="queue-points" type="geojson" data={activeRiderData}>
                    <Layer
                        id="queue-dots"
                        type="circle"
                        paint={{
                            'circle-radius': 3,
                            'circle-color': '#9333ea', // Rider purple
                            'circle-stroke-width': 1,
                            'circle-stroke-color': '#ffffff',
                            // Fade in/out effect could be here but simple is fine
                        }}
                    />
                </Source>

                {/* Ghost Stations (Recommendations) */}
                {recommendations && recommendations.map((rec, idx) => (
                    rec.minute <= currentMinute && (
                        <Marker
                            key={`rec-${idx}`}
                            longitude={rec.lon}
                            latitude={rec.lat}
                            anchor="center"
                        >
                            <div style={styles.ghostMarker}>
                                <div style={styles.ghostIcon}>
                                    <AlertCircle size={14} color="white" />
                                </div>
                                <div style={styles.ghostPulse} />
                            </div>
                        </Marker>
                    )
                ))}

                {/* STEP 3 & 5: Station markers with congestion UI */}
                {stations.map((station) => {
                    const state = getStationState(station.station_id);
                    const stationColor = getStationColor(state);
                    const isStockout = state.inventory === 0;
                    const isCongested = state.queue > state.chargers;

                    return (
                        <Marker
                            key={station.station_id}
                            longitude={station.longitude}
                            latitude={station.latitude}
                            anchor="center"
                        >
                            <div
                                style={styles.stationMarker}
                                onMouseEnter={() => setHoveredStation({
                                    id: station.station_id,
                                    zone_id: station.zone_id,
                                    swap_bays: station.swap_bays,
                                    chargers_total: station.chargers_total,
                                    ...state
                                })}
                                onMouseLeave={() => setHoveredStation(null)}
                            >
                                {/* Pulsing ring for stockout */}
                                {isStockout && (
                                    <div style={styles.stockoutPulse} />
                                )}

                                {/* Station dot */}
                                <div style={{
                                    ...styles.stationIcon,
                                    backgroundColor: stationColor,
                                    transform: (isStockout || isCongested) ? 'scale(1.2)' : 'scale(1)'
                                }}>
                                    <BatteryCharging size={12} color="white" />
                                </div>

                                {/* Queue badge - only show when queue > 0 */}
                                {state.queue > 0 && (
                                    <div style={styles.queueBadge}>
                                        Q:{state.queue}
                                    </div>
                                )}
                            </div>
                        </Marker>
                    );
                })}

                {/* Hero rider marker */}
                {heroPosition && (
                    <Marker
                        longitude={heroPosition.lon}
                        latitude={heroPosition.lat}
                        anchor="center"
                    >
                        <div style={styles.riderMarker}>
                            <div style={styles.riderIcon}>
                                <User size={20} color="white" />
                            </div>
                            <div style={styles.riderPulse} />
                        </div>
                    </Marker>
                )}
            </Map>

            {/* Network Status Overlay */}
            <div style={styles.statusOverlay}>
                <h3 style={styles.statusTitle}>Lucknow Network</h3>
                <p style={styles.statusSubtitle}>
                    {currentMinute !== null ?
                        `Playback at minute ${currentMinute}` :
                        'Battery Smart Swap Network'}
                </p>
                <div style={styles.statusRow}>
                    <span>Total Stations:</span>
                    <span style={{ color: '#6b7280', fontWeight: 'bold' }}>
                        {stations.length}
                    </span>
                </div>
                {/* Dynamic Stockout Counter */}
                <div style={styles.statusRow}>
                    <span>Stockouts:</span>
                    <span style={{ color: '#ef4444', fontWeight: 'bold' }}>
                        {stations.filter(s => getStationState(s.station_id).inventory === 0).length}
                    </span>
                </div>
                {heroRider && (
                    <div style={styles.statusRow}>
                        <span>Hero Rider:</span>
                        <span style={{ color: '#9333ea', fontWeight: 'bold' }}>
                            {heroRider.id} ({heroRider.completedSwaps || 0} swaps)
                        </span>
                    </div>
                )}
            </div>

            {/* STEP 4: Station Tooltip */}
            {hoveredStation && (
                <div style={styles.tooltip}>
                    <div style={styles.tooltipTitle}>
                        <BatteryCharging size={14} /> {hoveredStation.id}
                    </div>
                    <div style={styles.tooltipRow}>
                        Zone: {hoveredStation.zone_id}
                    </div>
                    <div style={styles.tooltipRow}>
                        Swap Bays: {hoveredStation.swap_bays}
                    </div>
                    <div style={styles.tooltipRow}>
                        Queue: <span style={{
                            color: hoveredStation.queue > 0 ? '#f59e0b' : '#22c55e',
                            fontWeight: 'bold'
                        }}>
                            {hoveredStation.queue}
                        </span>
                    </div>
                    <div style={styles.tooltipRow}>
                        Charging: {hoveredStation.charging}/{hoveredStation.chargers}
                    </div>
                    <div style={styles.tooltipRow}>
                        Inventory: <span style={{
                            color: hoveredStation.inventory === 0 ? '#ef4444' :
                                hoveredStation.inventory < 3 ? '#f59e0b' : '#22c55e',
                            fontWeight: 'bold'
                        }}>
                            {hoveredStation.inventory}
                        </span>
                    </div>
                    {hoveredStation.activePressure && (
                        <div style={{ ...styles.tooltipRow, color: '#ef4444', marginTop: 8 }}>
                            ⚠ {hoveredStation.activePressure.reason.replace('_', ' ')}
                        </div>
                    )}
                </div>
            )}

            {/* Legend */}
            <div style={styles.legend}>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#22c55e' }} />
                    <span>Healthy (Has Batteries)</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#f59e0b' }} />
                    <span>Low Inventory (&#60; 3 Batteries)</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#ef4444' }} />
                    <span>Stockout (0 Batteries)</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#f59e0b', border: '1px dashed orange' }} />
                    <span>Redirection Path</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#dc2626', borderRadius: 0, opacity: 0.7 }} />
                    <span>Recommended Spot</span>
                </div>
            </div>
        </div>
    );
};

const styles = {
    stationMarker: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        cursor: 'pointer'
    },
    stationIcon: {
        width: 24,
        height: 24,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
        border: '2px solid white',
        transition: 'transform 0.2s, background-color 0.3s',
        zIndex: 2
    },
    stockoutPulse: {
        position: 'absolute',
        width: 36,
        height: 36,
        borderRadius: '50%',
        border: '3px solid #ef4444',
        animation: 'stockoutPulse 1.5s infinite',
        opacity: 0.8,
        zIndex: 1
    },
    queueBadge: {
        position: 'absolute',
        top: -8,
        right: -12,
        backgroundColor: '#f59e0b',
        color: 'white',
        fontSize: 9,
        fontWeight: 'bold',
        padding: '2px 4px',
        borderRadius: 4,
        boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        zIndex: 3
    },
    chargingBadge: {
        position: 'absolute',
        bottom: -10,
        backgroundColor: 'rgba(55, 65, 81, 0.9)',
        color: 'white',
        fontSize: 8,
        fontWeight: 'bold',
        padding: '1px 3px',
        borderRadius: 3,
        whiteSpace: 'nowrap',
        zIndex: 3
    },
    riderMarker: {
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
    },
    riderIcon: {
        width: 36,
        height: 36,
        borderRadius: '50%',
        backgroundColor: '#9333ea',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 10px rgba(147, 51, 234, 0.5)',
        border: '3px solid white',
        zIndex: 10
    },
    riderPulse: {
        position: 'absolute',
        width: 50,
        height: 50,
        borderRadius: '50%',
        border: '2px solid #9333ea',
        animation: 'pulse 2s infinite',
        opacity: 0.5
    },
    statusOverlay: {
        position: 'absolute',
        top: 80,
        left: 16,
        backgroundColor: 'rgba(255,255,255,0.95)',
        padding: 16,
        borderRadius: 12,
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
        minWidth: 200,
        backdropFilter: 'blur(8px)'
    },
    statusTitle: {
        margin: 0,
        fontSize: 18,
        fontWeight: 'bold',
        color: '#1f2937'
    },
    statusSubtitle: {
        margin: '4px 0 12px 0',
        fontSize: 12,
        color: '#6b7280'
    },
    statusRow: {
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 13,
        marginTop: 6
    },
    tooltip: {
        position: 'absolute',
        top: 80,
        right: 16,
        backgroundColor: 'rgba(255,255,255,0.95)',
        padding: 14,
        borderRadius: 12,
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
        minWidth: 200,
        fontSize: 13,
        backdropFilter: 'blur(8px)'
    },
    tooltipTitle: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        fontWeight: 'bold',
        marginBottom: 8,
        color: '#22c55e',
        fontSize: 15
    },
    tooltipRow: {
        marginTop: 6,
        color: '#374151'
    },
    legend: {
        position: 'absolute',
        bottom: 16,
        bottom: 32,
        right: 32,
        backgroundColor: 'rgba(255,255,255,0.95)',
        padding: 12,
        borderRadius: 12,
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
        display: 'flex',
        gap: 16,
        backdropFilter: 'blur(8px)'
    },
    legendItem: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        fontSize: 12
    },
    legendDot: {
        width: 12,
        height: 12,
        borderRadius: '50%'
    },
    errorContainer: {
        width: '100%',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fef2f2'
    },
    errorBox: {
        backgroundColor: 'white',
        padding: 32,
        borderRadius: 12,
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        textAlign: 'center',
        maxWidth: 400
    },
    errorTitle: {
        color: '#dc2626',
        margin: '0 0 12px 0'
    },
    errorText: {
        color: '#7f1d1d',
        margin: '0 0 8px 0'
    },
    errorHint: {
        color: '#6b7280',
        margin: 0,
        fontSize: 13
    },
    loadingContainer: {
        width: '100%',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f3f4f6'
    },
    loadingSpinner: {
        fontSize: 18,
        color: '#6b7280'
    },
    ghostMarker: {
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
    },
    ghostIcon: {
        width: 20,
        height: 20,
        borderRadius: '50%',
        backgroundColor: '#dc2626',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 8px rgba(220, 38, 38, 0.4)',
        border: '2px solid white',
        zIndex: 10
    },
    ghostPulse: {
        position: 'absolute',
        width: 30,
        height: 30,
        borderRadius: '50%',
        border: '2px solid #dc2626',
        animation: 'pulse 2s infinite',
        opacity: 0.6
    }
};

export default CityMapView;
