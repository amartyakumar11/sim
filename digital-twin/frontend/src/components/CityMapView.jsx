/**
 * CityMapView: Map-based visualization for the Digital Twin
 * 
 * Uses MapLibre with OpenStreetMap for a real map background.
 * Renders battery swap stations from city_graph_lucknow.json.
 * Integrates with the playback system for time-based visualization.
 * Uses OSRM for real road routing of rider movements.
 * 
 * This is a READ-ONLY visualization - NO simulation logic.
 */

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import Map, { Marker, Source, Layer, Popup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { BatteryCharging, User, AlertCircle, Layers, Zap, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ReferenceLine, ResponsiveContainer } from 'recharts';
import HeatmapLayer from './HeatmapLayer';
import { simulationAPI } from '../services/api';
import { predictStationDemand } from '../utils/forecasting';
import { getRoute, interpolateAlongRoute, getCacheStats } from '../services/osrmService';
import './CityMapView.css'; // Add CSS import

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
    const [showHeatmap, setShowHeatmap] = useState(false); // Heatmap toggle state

    // OSRM Route Cache State
    const [osrmRoutes, setOsrmRoutes] = useState({}); // key: "fromId->toId", value: route coordinates
    const [routesFetching, setRoutesFetching] = useState(false);
    const fetchedRoutesRef = useRef(new Set()); // Track which routes we've already tried to fetch

    // Forecast State
    const [forecastData, setForecastData] = useState(null);
    const [loadingForecast, setLoadingForecast] = useState(false);

    // Level 2: Optimization
    const [optimizing, setOptimizing] = useState(false);
    const [suggestedStations, setSuggestedStations] = useState([]);

    const handleOptimize = async () => {
        if (suggestedStations.length > 0) {
            // Toggle off if already showing
            setSuggestedStations([]);
            return;
        }

        setOptimizing(true);
        try {
            const result = await simulationAPI.getRecommendations({
                description: "optimize_request",
                city_config: lucknowData
            });
            setSuggestedStations(result);
        } catch (err) {
            console.error("Optimization failed:", err);
            // Fallback for demo if API fails (or if running static)
            // setSuggestedStations(recommendations); 
        } finally {
            setOptimizing(false);
        }
    };

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

    // Debug: Log stationTimelines structure
    useEffect(() => {
        if (Object.keys(stationTimelines).length > 0) {
            const firstStation = Object.keys(stationTimelines)[0];
            console.log('[CityMapView] stationTimelines sample:', firstStation, stationTimelines[firstStation]);
            console.log('[CityMapView] currentMinute:', currentMinute);
            console.log('[CityMapView] Total stations with timelines:', Object.keys(stationTimelines).length);
        }
    }, [stationTimelines, currentMinute]);

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

    // OSRM Route Fetching: Collect all unique route pairs needed and fetch them
    useEffect(() => {
        if (!stationCoordsMap || Object.keys(stationCoordsMap).length === 0) return;
        if (!riderTraces || Object.keys(riderTraces).length === 0) return;

        // Collect all unique route pairs needed
        const routePairs = new Set();

        Object.values(riderTraces).forEach(trace => {
            // Redirections
            if (trace.redirections) {
                trace.redirections.forEach(redir => {
                    if (redir.from_station && redir.to_station) {
                        const key = `${redir.from_station}->${redir.to_station}`;
                        if (!fetchedRoutesRef.current.has(key) && !osrmRoutes[key]) {
                            routePairs.add({ from: redir.from_station, to: redir.to_station, key });
                        }
                    }
                });
            }

            // Swap station paths
            const swapStations = trace.completedStations || trace.swap_stations || [];
            for (let i = 0; i < swapStations.length - 1; i++) {
                const fromId = swapStations[i];
                const toId = swapStations[i + 1];
                const key = `${fromId}->${toId}`;
                if (!fetchedRoutesRef.current.has(key) && !osrmRoutes[key]) {
                    routePairs.add({ from: fromId, to: toId, key });
                }
            }
        });

        // Fetch routes that we haven't tried yet
        const pairsToFetch = Array.from(routePairs);
        if (pairsToFetch.length === 0) return;

        // Mark as fetching to prevent duplicate requests
        pairsToFetch.forEach(pair => fetchedRoutesRef.current.add(pair.key));

        const fetchRoutes = async () => {
            setRoutesFetching(true);
            const newRoutes = {};

            for (const { from, to, key } of pairsToFetch) {
                const fromCoords = stationCoordsMap[from];
                const toCoords = stationCoordsMap[to];

                if (!fromCoords || !toCoords) continue;

                try {
                    const route = await getRoute(
                        { lat: fromCoords.lat, lon: fromCoords.lon },
                        { lat: toCoords.lat, lon: toCoords.lon }
                    );
                    newRoutes[key] = route;
                } catch (error) {
                    console.warn(`Failed to fetch OSRM route for ${key}:`, error);
                    // Fallback to straight line stored in osrmRoutes
                    newRoutes[key] = {
                        geoJsonCoordinates: [
                            [fromCoords.lon, fromCoords.lat],
                            [toCoords.lon, toCoords.lat]
                        ],
                        coordinates: [[fromCoords.lat, fromCoords.lon], [toCoords.lat, toCoords.lon]],
                        isFallback: true
                    };
                }
            }

            // Merge new routes with existing
            setOsrmRoutes(prev => ({ ...prev, ...newRoutes }));
            setRoutesFetching(false);

            // Log cache stats
            console.log('[OSRM] Route cache stats:', getCacheStats());
        };

        fetchRoutes();
    }, [riderTraces, stationCoordsMap, osrmRoutes]);

    // Level 3: Pre-calculate Risks for all stations
    const stationRisks = useMemo(() => {
        if (!stationTimelines || Object.keys(stationTimelines).length === 0) return {};

        const risks = {};
        Object.keys(stationTimelines).forEach(sid => {
            const timeline = stationTimelines[sid];
            if (timeline && timeline.states && currentMinute > 30) {
                const result = predictStationDemand(sid, timeline, currentMinute);
                if (result.risk_level === 'critical' || result.risk_level === 'high') {
                    risks[sid] = result.risk_level;
                }
            }
        });
        return risks;
    }, [stationTimelines, currentMinute]);

    // Get station state from timelines - includes queue, charging, inventory
    const getStationState = (stationId) => {
        const stationData = stationTimelines[stationId];

        if (!stationData) {
            return {
                queue: 0,
                charging: 0,
                inventory: 10,
                chargers: 4,
                activePressure: null
            };
        }

        // stationData IS the current state (flat structure from API)
        return {
            queue: stationData.queue || 0,
            charging: stationData.charging || 0,
            inventory: stationData.inventory !== undefined ? stationData.inventory : 10,
            chargers: stationData.chargers || 4,
            activePressure: null
        };
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

    // Build rider path GeoJSON for active riders and redirections (using OSRM real roads)
    const riderPathData = useMemo(() => {
        const features = [];

        Object.entries(riderTraces).forEach(([riderId, trace]) => {
            // 1. Draw Redirections (ACTIVE EVENT) - using OSRM routes
            if (trace.redirections) {
                trace.redirections.forEach(redir => {
                    // Only show if it happened recently (within last 15 mins)
                    if (currentMinute && redir.minute <= currentMinute && redir.minute > currentMinute - 15) {
                        const routeKey = `${redir.from_station}->${redir.to_station}`;
                        const osrmRoute = osrmRoutes[routeKey];

                        if (osrmRoute && osrmRoute.geoJsonCoordinates) {
                            // Use real road route from OSRM
                            features.push({
                                type: 'Feature',
                                properties: {
                                    riderId,
                                    type: 'redirection',
                                    minute: redir.minute,
                                    isRealRoute: !osrmRoute.isFallback
                                },
                                geometry: {
                                    type: 'LineString',
                                    coordinates: osrmRoute.geoJsonCoordinates
                                }
                            });
                        } else {
                            // Fallback to Manhattan L-shape while route loads
                            const fromStation = stationCoordsMap[redir.from_station];
                            const toStation = stationCoordsMap[redir.to_station];

                            if (fromStation && toStation) {
                                const corner = [toStation.lon, fromStation.lat];
                                features.push({
                                    type: 'Feature',
                                    properties: {
                                        riderId,
                                        type: 'redirection',
                                        minute: redir.minute,
                                        isRealRoute: false
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
                    }
                });
            }

            // 2. Draw completed swap paths using OSRM routes
            const completedStations = trace.completedStations || trace.swap_stations || [];
            if (completedStations.length >= 2) {
                // Build path segment by segment using OSRM routes
                for (let i = 0; i < completedStations.length - 1; i++) {
                    const fromId = completedStations[i];
                    const toId = completedStations[i + 1];
                    const routeKey = `${fromId}->${toId}`;
                    const osrmRoute = osrmRoutes[routeKey];

                    if (osrmRoute && osrmRoute.geoJsonCoordinates) {
                        // Use real road route from OSRM
                        features.push({
                            type: 'Feature',
                            properties: { 
                                riderId, 
                                type: 'history',
                                segmentIndex: i,
                                isRealRoute: !osrmRoute.isFallback
                            },
                            geometry: { 
                                type: 'LineString', 
                                coordinates: osrmRoute.geoJsonCoordinates 
                            }
                        });
                    } else {
                        // Fallback to straight line while route loads
                        const fromStation = stationCoordsMap[fromId];
                        const toStation = stationCoordsMap[toId];
                        if (fromStation && toStation) {
                            features.push({
                                type: 'Feature',
                                properties: { 
                                    riderId, 
                                    type: 'history',
                                    segmentIndex: i,
                                    isRealRoute: false
                                },
                                geometry: { 
                                    type: 'LineString', 
                                    coordinates: [
                                        [fromStation.lon, fromStation.lat],
                                        [toStation.lon, toStation.lat]
                                    ]
                                }
                            });
                        }
                    }
                }
            }
        });

        return {
            type: 'FeatureCollection',
            features
        };
    }, [riderTraces, stationCoordsMap, currentMinute, osrmRoutes]);

    // GENERATE ACTIVE RIDER CROWD
    // Since queues are often 0 due to rapid redirection, we visualize ALL active riders
    // to show the scale of the simulation. Uses OSRM routes for realistic road animation.
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
                let isOnRoute = false;

                // If redirecting, interpolate position along OSRM route
                const activeRedir = trace.redirections?.find(r => r.minute <= currentMinute && r.minute > currentMinute - 15);

                if (activeRedir) {
                    const routeKey = `${activeRedir.from_station}->${activeRedir.to_station}`;
                    const osrmRoute = osrmRoutes[routeKey];
                    
                    // Calculate progress (0-1) based on time elapsed
                    const elapsed = currentMinute - activeRedir.minute;
                    const progress = Math.min(elapsed / 15, 1); // 15 min duration assumed
                    
                    if (osrmRoute && osrmRoute.coordinates && osrmRoute.coordinates.length > 0) {
                        // Use OSRM route for realistic road animation
                        const position = interpolateAlongRoute(osrmRoute.coordinates, progress);
                        if (position) {
                            lat = position.lat;
                            lon = position.lon;
                            isOnRoute = true;
                        }
                    } else {
                        // Fallback to linear interpolation while route loads
                        const from = stationCoordsMap[activeRedir.from_station];
                        const to = stationCoordsMap[activeRedir.to_station];
                        if (from && to) {
                            lat = from.lat + (to.lat - from.lat) * progress;
                            lon = from.lon + (to.lon - from.lon) * progress;
                        }
                    }
                } else if (lastSwap) {
                    // Stationary at last station (scattered slightly)
                    const swapStations = trace.swap_stations || [];
                    const lastSwapIndex = swaps.indexOf(lastSwap);
                    const stationId = swapStations[lastSwapIndex] || swapStations[swapStations.length - 1];
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
                            riderId: riderId,
                            isOnRoute: isOnRoute
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
    }, [riderTraces, stationCoordsMap, currentMinute, osrmRoutes]);

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
                {/* Heatmap Layer - Rendered underneath stations but above base map */}
                <HeatmapLayer
                    visible={showHeatmap}
                    scenarioConfig={{
                        // Pass current city config and implicit interventions (could be refined)
                        description: "visualization_layer_request",
                        city_config: lucknowData,
                        interventions: {
                            // Default to current simulation context if available, or just use base
                            // For now, visualization assumes 1.0 multipliers unless passed explicitly
                            // In a real app, we'd pass the full scenario context here
                            demand_multiplier: 1.0
                        }
                    }}
                />

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
                {/* Ghost Stations (Recommendations) - Merging static and dynamic */}
                {(suggestedStations.length > 0 ? suggestedStations : recommendations).map((rec, idx) => (
                    (!rec.minute || (currentMinute && rec.minute <= currentMinute)) && (
                        <Marker
                            key={`rec-${idx}`}
                            longitude={rec.longitude || rec.lon}
                            latitude={rec.latitude || rec.lat}
                            anchor="center"
                        >
                            <div style={styles.ghostMarker}>
                                <div style={{ ...styles.ghostIcon, backgroundColor: rec.score ? '#f59e0b' : '#ef4444' }}>
                                    <Zap size={14} color="white" fill="white" />
                                </div>
                                <div style={{ ...styles.ghostPulse, borderColor: rec.score ? '#f59e0b' : '#ef4444' }} />
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

                    // Debug first 3 stations
                    if (station.station_id === 'LKO_ST_001' || station.station_id === 'LKO_ST_002' || station.station_id === 'LKO_ST_003') {
                        console.log(`[${station.station_id}] State:`, state, 'Color:', stationColor, 'Stockout:', isStockout);
                    }

                    return (
                        <Marker
                            key={station.station_id}
                            longitude={station.longitude}
                            latitude={station.latitude}
                            anchor="center"
                            style={{ zIndex: 100 }}
                        >
                            <div
                                style={styles.stationMarker}
                                onMouseEnter={() => {
                                    console.log('Hover triggered for station:', station.station_id);

                                    // Get station logs/events from timeline for tooltip
                                    const timeline = stationTimelines[station.station_id];
                                    const stEvents = timeline?.states
                                        ?.filter(e => e.minute <= currentMinute && e.minute > currentMinute - 60) // Last 60 mins
                                        ?.slice(-5) // Last 5 events
                                        ?.reverse() || [];

                                    setHoveredStation({
                                        id: station.station_id,
                                        zone_id: station.zone_id,
                                        swap_bays: station.swap_bays,
                                        chargers_total: station.chargers_total,
                                        recentEvents: stEvents,
                                        ...state
                                    });

                                    // Reset forecast when switching stations
                                    setForecastData(null);
                                }}
                                onMouseLeave={() => {
                                    setHoveredStation(null);
                                    setForecastData(null);
                                }}
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
                                    {/* Show Zap if high risk forecast (mock logic or if we pre-fetched) */}
                                    {/* simplified: just battery icon for now */}
                                    <BatteryCharging size={12} color="white" />
                                </div>

                                {/* Queue badge - only show when queue > 0 */}
                                {state.queue > 0 && (
                                    <div style={styles.queueBadge}>
                                        Q:{state.queue}
                                    </div>
                                )}

                                {/* Level 3: Predictive Risk Badge */}
                                {stationRisks[station.station_id] && (
                                    <div style={styles.riskBadge}>
                                        🔮
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

                {/* Station Status Popup (appears on map near hovered station) */}
                {hoveredStation && (
                    <Popup
                        longitude={stations.find(s => s.station_id === hoveredStation.id)?.longitude || 0}
                        latitude={stations.find(s => s.station_id === hoveredStation.id)?.latitude || 0}
                        anchor="left"
                        offset={15}
                        onClose={() => setHoveredStation(null)}
                        closeButton={false}
                        closeOnClick={false}
                        className="station-popup"
                    >
                        <div style={{ padding: 8, minWidth: 180 }}>
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
                                    color: hoveredStation.inventory < 3 ? '#ef4444' : '#22c55e',
                                    fontWeight: 'bold'
                                }}>
                                    {hoveredStation.inventory}
                                </span>
                            </div>

                            {/* Forecast Section */}
                            <div style={{ marginTop: 8, borderTop: '1px solid #e5e7eb', paddingTop: 8 }}>
                                {!forecastData ? (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setLoadingForecast(true);
                                            // Use local utility instead of API
                                            setTimeout(() => {
                                                const timeline = stationTimelines[hoveredStation.id];
                                                const result = predictStationDemand(
                                                    hoveredStation.id,
                                                    timeline,
                                                    currentMinute || 0
                                                );
                                                setForecastData(result);
                                                setLoadingForecast(false);
                                            }, 500);
                                        }}
                                        style={{
                                            width: '100%',
                                            padding: '4px',
                                            backgroundColor: '#f3f4f6',
                                            border: '1px solid #d1d5db',
                                            borderRadius: '4px',
                                            cursor: 'pointer',
                                            fontSize: '11px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            gap: 4
                                        }}
                                    >
                                        {loadingForecast ? 'Analysing...' : <><TrendingUp size={12} /> Predict Stockouts</>}
                                    </button>
                                ) : (
                                    <div style={{ width: 220, height: 120 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                            <span style={{ fontSize: 10, fontWeight: 'bold' }}>Future Inventory (1h)</span>
                                            {forecastData.risk_level === 'critical' &&
                                                <span style={{ fontSize: 10, color: '#ef4444', fontWeight: 'bold' }}>⚠️ HIGH RISK</span>
                                            }
                                        </div>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={forecastData.forecast}>
                                                <ReferenceLine y={0} stroke="red" strokeDasharray="3 3" />
                                                <XAxis dataKey="minute" hide />
                                                <YAxis domain={[0, 20]} hide />
                                                <RechartsTooltip
                                                    contentStyle={{ fontSize: '10px', padding: '2px' }}
                                                    itemStyle={{ padding: 0 }}
                                                    labelStyle={{ display: 'none' }}
                                                />
                                                <Line
                                                    type="monotone"
                                                    dataKey="predicted_inventory"
                                                    stroke={forecastData.risk_level === 'critical' ? '#ef4444' : '#10b981'}
                                                    strokeWidth={2}
                                                    dot={false}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </div>

                            {/* Recent Events Log (Existing) */}
                            {hoveredStation.recentEvents && hoveredStation.recentEvents.length > 0 && (
                                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: 8, marginTop: 8 }}>
                                    <div style={{ fontSize: 10, fontWeight: 'bold', color: '#6b7280', marginBottom: 4 }}>RECENT ACTIVITY</div>
                                    {hoveredStation.recentEvents.map((evt, i) => (
                                        <div key={i} style={{ fontSize: 10, display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                                            <span style={{ color: '#9ca3af' }}>{Math.floor(evt.minute / 60)}:{String(evt.minute % 60).padStart(2, '0')}</span>
                                            <span style={{
                                                color: evt.inventory === 0 ? '#ef4444' : evt.event === 'redirection' ? '#f59e0b' : '#374151',
                                                fontWeight: (evt.inventory === 0 || evt.event === 'redirection') ? 'bold' : 'normal'
                                            }}>
                                                {evt.inventory === 0 ? 'STOCKOUT' : evt.event === 'redirection' ? 'Redirect' : `Q: ${evt.queue} | Inv: ${evt.inventory}`}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {hoveredStation.activePressure && (
                                <div style={{ ...styles.tooltipRow, color: '#ef4444', marginTop: 8 }}>
                                    ⚠ {hoveredStation.activePressure.reason.replace('_', ' ')}
                                </div>
                            )}
                        </div>
                    </Popup>
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



            {/* Map Controls Overlay */}
            <div className="map-controls-overlay">
                <div className="control-group">
                    <label className="control-label">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Layers size={16} />
                            <span>Demand Heatmap</span>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                className="toggle-input"
                                checked={showHeatmap}
                                onChange={(e) => setShowHeatmap(e.target.checked)}
                            />
                            <span className="toggle-slider">
                                <span className="toggle-knob"></span>
                            </span>
                        </label>
                    </label>
                </div>

                <div className="control-group">
                    <button
                        onClick={handleOptimize}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            width: '100%',
                            padding: '8px 0',
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: optimizing ? '#f59e0b' : suggestedStations.length > 0 ? '#10b981' : '#1f2937',
                            fontWeight: 600,
                            fontSize: 14
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Zap size={16} fill={suggestedStations.length > 0 ? "currentColor" : "none"} />
                            <span>{optimizing ? 'Analyzing...' : suggestedStations.length > 0 ? 'Clear Suggestions' : 'Optimize Network'}</span>
                        </div>
                    </button>
                    {suggestedStations.length > 0 && (
                        <div style={{ fontSize: 11, color: '#6b7280', marginTop: -4, paddingLeft: 24 }}>
                            {suggestedStations.length} stations proposed
                        </div>
                    )}
                </div>
            </div>

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
                {/* OSRM Route Status */}
                <div style={{ ...styles.legendItem, borderTop: '1px solid #e5e7eb', paddingTop: 8, marginTop: 4 }}>
                    <div style={{ 
                        width: 10, 
                        height: 10, 
                        borderRadius: '50%', 
                        backgroundColor: routesFetching ? '#f59e0b' : Object.keys(osrmRoutes).length > 0 ? '#22c55e' : '#9ca3af'
                    }} />
                    <span style={{ fontSize: 11, color: '#6b7280' }}>
                        {routesFetching 
                            ? 'Loading routes...' 
                            : Object.keys(osrmRoutes).length > 0 
                                ? `${Object.keys(osrmRoutes).length} road routes loaded`
                                : 'No routes loaded'}
                    </span>
                </div>
            </div>
        </div >
    );
};

const styles = {
    stationMarker: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        pointerEvents: 'auto',
        touchAction: 'none',
        width: 48,
        height: 48,
        zIndex: 100
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
    riskBadge: {
        position: 'absolute',
        top: -8,
        left: -12,
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        fontSize: 12,
        padding: '2px',
        borderRadius: '50%',
        boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
        zIndex: 4,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
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
