/**
 * CityMapView: Map-based visualization for the Digital Twin
 * 
 * Uses MapLibre with OpenStreetMap for a real map background.
 * Renders battery swap stations and rider journeys on the map.
 * Integrates with the playback system for time-based visualization.
 * 
 * This is a READ-ONLY visualization - NO simulation logic.
 */

import React, { useState, useEffect, useMemo } from 'react';
import Map, { Marker, Source, Layer } from 'react-map-gl/maplibre';
import * as turf from '@turf/turf';
import 'maplibre-gl/dist/maplibre-gl.css';
import { BatteryCharging, Zap, MapPin, User } from 'lucide-react';

// --------------------------------------------------------
// CONFIGURATION
// --------------------------------------------------------
// Using Delhi coordinates (like your friend's example)
const CITY_CENTER = { lat: 28.6276, lon: 77.2156 };

// Zone configuration with approximate center coordinates
const ZONE_CONFIG = {
    'zone_01': {
        name: 'Downtown Core',
        center: { lat: 28.6320, lon: 77.2200 },
        color: '#3b82f6'
    },
    'zone_02': {
        name: 'North Residential',
        center: { lat: 28.6400, lon: 77.2100 },
        color: '#10b981'
    },
    'zone_03': {
        name: 'Business District',
        center: { lat: 28.6250, lon: 77.2300 },
        color: '#f59e0b'
    },
    'zone_04': {
        name: 'Industrial Park',
        center: { lat: 28.6180, lon: 77.2050 },
        color: '#8b5cf6'
    }
};

// Station coordinates - spread around zones
const STATION_COORDS = {
    'ST_01_01': { lat: 28.6320, lon: 77.2180, zone: 'zone_01' },
    'ST_01_02': { lat: 28.6340, lon: 77.2220, zone: 'zone_01' },
    'ST_02_01': { lat: 28.6400, lon: 77.2080, zone: 'zone_02' },
    'ST_02_02': { lat: 28.6420, lon: 77.2120, zone: 'zone_02' },
    'ST_03_01': { lat: 28.6250, lon: 77.2280, zone: 'zone_03' },
    'ST_04_01': { lat: 28.6180, lon: 77.2030, zone: 'zone_04' },
    'ST_04_02': { lat: 28.6200, lon: 77.2070, zone: 'zone_04' }
};

// --------------------------------------------------------
// COMPONENT
// --------------------------------------------------------
const CityMapView = ({
    cityGraph,
    zonePressure = {},
    stationTimelines = {},
    riderTraces = {},
    currentMinute = null
}) => {
    const [viewState, setViewState] = useState({
        longitude: CITY_CENTER.lon,
        latitude: CITY_CENTER.lat,
        zoom: 14,
        pitch: 45
    });

    const [hoveredStation, setHoveredStation] = useState(null);

    // Get pressure level for zone
    const getZonePressure = (zoneId) => {
        const entry = zonePressure[zoneId];
        if (!entry) return 0;
        return entry.pressure_score || 0;
    };

    // Get station state
    const getStationState = (stationId) => {
        return stationTimelines[stationId] || {
            swaps_total: 0,
            lost_swaps: 0,
            activePressure: null
        };
    };

    // Build rider path GeoJSON for completed swaps
    const riderPathData = useMemo(() => {
        const features = [];

        Object.entries(riderTraces).forEach(([riderId, trace]) => {
            const completedStations = trace.completedStations || trace.swap_stations || [];
            if (completedStations.length < 2) return;

            const coordinates = completedStations
                .map(stationId => {
                    const coord = STATION_COORDS[stationId];
                    return coord ? [coord.lon, coord.lat] : null;
                })
                .filter(c => c !== null);

            if (coordinates.length >= 2) {
                features.push({
                    type: 'Feature',
                    properties: {
                        riderId,
                        status: trace.isActiveAtMinute ? 'active' : 'inactive'
                    },
                    geometry: {
                        type: 'LineString',
                        coordinates
                    }
                });
            }
        });

        return {
            type: 'FeatureCollection',
            features
        };
    }, [riderTraces]);

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
        const stations = heroRider.completedStations || heroRider.swap_stations || [];
        if (stations.length === 0) return null;

        const lastStation = stations[stations.length - 1];
        return STATION_COORDS[lastStation] || null;
    }, [heroRider]);

    return (
        <div style={{ width: '100%', height: '600px', position: 'relative', borderRadius: '8px', overflow: 'hidden' }}>
            <Map
                {...viewState}
                onMove={evt => setViewState(evt.viewState)}
                mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
                style={{ width: '100%', height: '100%' }}
            >
                {/* Rider paths as lines */}
                <Source id="rider-paths" type="geojson" data={riderPathData}>
                    <Layer
                        id="rider-paths-line"
                        type="line"
                        paint={{
                            'line-color': '#9333ea',
                            'line-width': 4,
                            'line-opacity': 0.8
                        }}
                    />
                </Source>

                {/* Station markers */}
                {Object.entries(STATION_COORDS).map(([stationId, coord]) => {
                    const state = getStationState(stationId);
                    const isUnderPressure = state.activePressure !== null;
                    const hasLostSwaps = state.lost_swaps > 0;

                    return (
                        <Marker
                            key={stationId}
                            longitude={coord.lon}
                            latitude={coord.lat}
                            anchor="bottom"
                        >
                            <div
                                style={styles.stationMarker}
                                onMouseEnter={() => setHoveredStation({ id: stationId, ...state, coord })}
                                onMouseLeave={() => setHoveredStation(null)}
                            >
                                <div style={{
                                    ...styles.stationIcon,
                                    backgroundColor: isUnderPressure ? '#ef4444' :
                                        hasLostSwaps ? '#f59e0b' : '#22c55e',
                                    transform: isUnderPressure ? 'scale(1.2)' : 'scale(1)'
                                }}>
                                    <BatteryCharging size={16} color="white" />
                                </div>
                                <div style={styles.stationLabel}>
                                    {stationId.replace('ST_', '')}
                                </div>
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
                <h3 style={styles.statusTitle}>Network Status</h3>
                <p style={styles.statusSubtitle}>
                    {currentMinute !== null ?
                        `Playback at minute ${currentMinute}` :
                        'Simulating autonomous swapping loop'}
                </p>
                <div style={styles.statusRow}>
                    <span>Active Stations:</span>
                    <span style={{ color: '#22c55e', fontWeight: 'bold' }}>
                        {Object.keys(STATION_COORDS).length}
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

            {/* Station Tooltip */}
            {hoveredStation && (
                <div style={styles.tooltip}>
                    <div style={styles.tooltipTitle}>
                        <BatteryCharging size={14} /> {hoveredStation.id}
                    </div>
                    <div style={styles.tooltipRow}>
                        Zone: {hoveredStation.coord.zone}
                    </div>
                    <div style={styles.tooltipRow}>
                        Total Swaps: {hoveredStation.swaps_total}
                    </div>
                    <div style={styles.tooltipRow}>
                        Lost Swaps: <span style={{ color: hoveredStation.lost_swaps > 0 ? '#ef4444' : '#22c55e' }}>
                            {hoveredStation.lost_swaps}
                        </span>
                    </div>
                    {hoveredStation.activePressure && (
                        <div style={{ ...styles.tooltipRow, color: '#ef4444' }}>
                            ⚠ Under Pressure: {hoveredStation.activePressure.reason}
                        </div>
                    )}
                </div>
            )}

            {/* Legend */}
            <div style={styles.legend}>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#22c55e' }} />
                    <span>Station OK</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#f59e0b' }} />
                    <span>Lost Swaps</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#ef4444' }} />
                    <span>Under Pressure</span>
                </div>
                <div style={styles.legendItem}>
                    <div style={{ ...styles.legendDot, backgroundColor: '#9333ea' }} />
                    <span>Rider Path</span>
                </div>
            </div>
        </div>
    );
};

const styles = {
    stationMarker: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        cursor: 'pointer'
    },
    stationIcon: {
        width: 32,
        height: 32,
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        border: '2px solid white',
        transition: 'transform 0.2s'
    },
    stationLabel: {
        marginTop: 4,
        fontSize: 10,
        fontWeight: 'bold',
        color: '#333',
        backgroundColor: 'white',
        padding: '2px 4px',
        borderRadius: 4,
        boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
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
        top: 16,
        left: 16,
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 8,
        boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
        minWidth: 200
    },
    statusTitle: {
        margin: 0,
        fontSize: 16,
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
        top: 16,
        right: 16,
        backgroundColor: 'white',
        padding: 12,
        borderRadius: 8,
        boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
        minWidth: 180,
        fontSize: 13
    },
    tooltipTitle: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        fontWeight: 'bold',
        marginBottom: 8,
        color: '#22c55e'
    },
    tooltipRow: {
        marginTop: 4
    },
    legend: {
        position: 'absolute',
        bottom: 16,
        left: 16,
        backgroundColor: 'white',
        padding: 12,
        borderRadius: 8,
        boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
        display: 'flex',
        gap: 16
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
    }
};

export default CityMapView;
