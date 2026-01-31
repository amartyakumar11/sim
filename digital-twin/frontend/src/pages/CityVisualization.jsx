/**
 * CityVisualization Page: Digital Twin City View with Playback
 * 
 * Main orchestration component for the Live City page.
 * Manages playback state and time-filters observability data before
 * passing to CityCanvas for rendering.
 * 
 * Playback Features:
 * - Minute-based discrete time progression
 * - Play/Pause controls
 * - Time slider for seeking
 * - Deterministic filtering of observability data
 */

import React, { useState, useEffect, useCallback } from 'react';
import CityMapView from '../components/CityMapView';
import SimulationLogs from '../components/SimulationLogs';
import {
    getMinuteRange,
    cumulativeZonePressure,
    stationStateAtMinute,
    riderStateAtMinute,
    formatMinuteAsTime
} from '../services/timeSelectors';

const PLAYBACK_INTERVAL_MS = 500; // Advance every 500ms

const CityVisualization = () => {
    // Data state
    const [cityGraph, setCityGraph] = useState(null);
    const [zonePressure, setZonePressure] = useState([]);
    const [stationTimelines, setStationTimelines] = useState({});
    const [riderTraces, setRiderTraces] = useState({});
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Playback state
    const [currentMinute, setCurrentMinute] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [minMinute, setMinMinute] = useState(0);
    const [maxMinute, setMaxMinute] = useState(0);

    // Load data on mount - try Lucknow simulation data first, fallback to sample
    useEffect(() => {
        const loadData = async () => {
            try {
                // Try loading Lucknow simulation data
                const [stationTimelineRes, zonePressureRes, riderTracesRes] = await Promise.all([
                    fetch('/station_timelines_lucknow.json'),
                    fetch('/zone_pressure_lucknow.json'),
                    fetch('/rider_traces_lucknow.json')
                ]);

                if (stationTimelineRes.ok && zonePressureRes.ok && riderTracesRes.ok) {
                    // Use Lucknow simulation data
                    const stationTimelineData = await stationTimelineRes.json();
                    const zonePressureData = await zonePressureRes.json();
                    const riderTraceData = await riderTracesRes.json();

                    // Try fetch recommendations (might fail if not generated)
                    let recData = [];
                    try {
                        const recRes = await fetch('/station_recommendations_lucknow.json');
                        if (recRes.ok) recData = await recRes.json();
                    } catch (e) { console.warn("No recommendations found"); }

                    // City graph is loaded separately by CityMapView
                    setCityGraph(null);
                    setZonePressure(zonePressureData);
                    setStationTimelines(stationTimelineData);
                    setRiderTraces(riderTraceData);
                    setRecommendations(recData);

                    // Calculate minute range from station timeline data
                    const allMinutes = [];
                    Object.values(stationTimelineData).forEach(station => {
                        if (station.timeline) {
                            station.timeline.forEach(entry => allMinutes.push(entry.minute));
                        }
                    });

                    if (allMinutes.length > 0) {
                        const min = Math.min(...allMinutes);
                        const max = Math.max(...allMinutes);
                        setMinMinute(min);
                        setMaxMinute(max);
                        setCurrentMinute(min);
                    }

                    console.log('[CityVisualization] Loaded Lucknow simulation data');
                    setLoading(false);
                } else {
                    throw new Error('Lucknow data not available, falling back to sample data');
                }
            } catch (err) {
                console.warn('Lucknow data not available, using sample data:', err.message);

                // Fallback to sample data
                try {
                    const {
                        getSampleCityGraph,
                        getSampleZonePressure,
                        getSampleStationTimelines,
                        getSampleRiderTraces
                    } = await import('../services/sampleData.js');

                    const cityGraphData = getSampleCityGraph();
                    const zonePressureData = getSampleZonePressure();
                    const stationTimelineData = getSampleStationTimelines();
                    const riderTraceData = getSampleRiderTraces();

                    setCityGraph(cityGraphData);
                    setZonePressure(zonePressureData);
                    setStationTimelines(stationTimelineData);
                    setRiderTraces(riderTraceData);

                    const { minMinute: min, maxMinute: max } = getMinuteRange(zonePressureData);
                    setMinMinute(min);
                    setMaxMinute(max);
                    setCurrentMinute(min);

                    setLoading(false);
                } catch (fallbackErr) {
                    console.error('Failed to load visualization data:', fallbackErr);
                    setError(fallbackErr.message);
                    setLoading(false);
                }
            }
        };

        loadData();
    }, []);

    // Playback loop
    useEffect(() => {
        if (!isPlaying || currentMinute === null) {
            return;
        }

        // Stop if we've reached the end
        if (currentMinute >= maxMinute) {
            setIsPlaying(false);
            return;
        }

        const intervalId = setInterval(() => {
            setCurrentMinute(prev => {
                if (prev >= maxMinute) {
                    setIsPlaying(false);
                    return prev;
                }
                return prev + 1;
            });
        }, PLAYBACK_INTERVAL_MS);

        // Cleanup on unmount or when dependencies change
        return () => clearInterval(intervalId);
    }, [isPlaying, currentMinute, maxMinute]);

    // Playback controls
    const handlePlayPause = useCallback(() => {
        if (currentMinute >= maxMinute) {
            // Reset to start if at end
            setCurrentMinute(minMinute);
            setIsPlaying(true);
        } else {
            setIsPlaying(prev => !prev);
        }
    }, [currentMinute, maxMinute, minMinute]);

    const handleSliderChange = useCallback((e) => {
        const newMinute = parseInt(e.target.value, 10);
        setCurrentMinute(newMinute);
        setIsPlaying(false); // Pause when manually seeking
    }, []);

    const handleReset = useCallback(() => {
        setCurrentMinute(minMinute);
        setIsPlaying(false);
    }, [minMinute]);

    // Compute time-filtered data
    const filteredZonePressure = cumulativeZonePressure(zonePressure, currentMinute);
    const filteredStationTimelines = stationStateAtMinute(stationTimelines, currentMinute);
    const filteredRiderTraces = riderStateAtMinute(riderTraces, currentMinute);

    if (loading) {
        return (
            <div style={styles.page}>
                <div style={styles.loading}>Loading city visualization...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.page}>
                <div style={styles.error}>Error: {error}</div>
            </div>
        );
    }

    return (
        <div style={styles.page}>
            {/* Modern Playback Controls - Floating Panel Style */}
            <div style={styles.controlsContainer}>
                <div style={styles.playbackPanel}>
                    {/* Left: Transport Controls */}
                    <div style={styles.transportControls}>
                        <button
                            style={{
                                ...styles.controlButton,
                                ...(isPlaying ? styles.pauseButton : styles.playButtonStyle)
                            }}
                            onClick={handlePlayPause}
                            aria-label={isPlaying ? 'Pause' : 'Play'}
                        >
                            <span style={styles.buttonIcon}>{isPlaying ? '⏸' : '▶'}</span>
                        </button>
                        <button
                            style={styles.controlButton}
                            onClick={handleReset}
                            aria-label="Reset"
                        >
                            <span style={styles.buttonIcon}>↺</span>
                        </button>
                    </div>

                    {/* Center: Timeline Slider */}
                    <div style={styles.timelineSection}>
                        <span style={styles.timeLabel}>{formatMinuteAsTime(minMinute)}</span>
                        <div style={styles.sliderContainer}>
                            <div
                                style={{
                                    ...styles.sliderTrack,
                                    background: `linear-gradient(to right, #3b82f6 ${((currentMinute - minMinute) / (maxMinute - minMinute)) * 100}%, #e5e7eb ${((currentMinute - minMinute) / (maxMinute - minMinute)) * 100}%)`
                                }}
                            />
                            <input
                                type="range"
                                min={minMinute}
                                max={maxMinute}
                                value={currentMinute ?? minMinute}
                                onChange={handleSliderChange}
                                style={{
                                    ...styles.sliderInput
                                }}
                                aria-label="Time slider"
                            />
                        </div>
                        <span style={styles.timeLabel}>{formatMinuteAsTime(maxMinute)}</span>
                    </div>

                    {/* Right: Time Display */}
                    <div style={styles.timeDisplaySection}>
                        <div style={styles.currentTime}>
                            {formatMinuteAsTime(currentMinute)}
                        </div>
                        <div style={styles.statusBadge}>
                            <span style={{
                                ...styles.statusDot,
                                backgroundColor: isPlaying ? '#22c55e' : '#f59e0b'
                            }} />
                            <span style={styles.statusText}>
                                {isPlaying ? 'Playing' : 'Paused'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Simulation Logs Side Panel */}
            <SimulationLogs
                currentMinute={currentMinute}
                stationTimelines={filteredStationTimelines}
                riderTraces={filteredRiderTraces}
                recommendations={recommendations}
            />

            {/* Map Container */}
            <main style={styles.main}>
                <CityMapView
                    cityGraph={cityGraph}
                    zonePressure={filteredZonePressure}
                    stationTimelines={filteredStationTimelines}
                    riderTraces={filteredRiderTraces}
                    recommendations={recommendations}
                    currentMinute={currentMinute}
                />
            </main>
        </div>
    );
};

const styles = {
    page: {
        minHeight: '100vh',
        backgroundColor: '#0f172a',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative'
    },
    controlsContainer: {
        position: 'absolute',
        top: 16,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        width: '60%',
        maxWidth: '600px'
    },
    playbackPanel: {
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        padding: '12px 20px',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(12px)',
        borderRadius: 16,
        boxShadow: '0 4px 24px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.08)',
        border: '1px solid rgba(255, 255, 255, 0.2)'
    },
    transportControls: {
        display: 'flex',
        gap: 8
    },
    controlButton: {
        width: 44,
        height: 44,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: 'none',
        borderRadius: 12,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        backgroundColor: '#f1f5f9',
        color: '#475569'
    },
    playButtonStyle: {
        backgroundColor: '#3b82f6',
        color: 'white',
        boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)'
    },
    pauseButton: {
        backgroundColor: '#ef4444',
        color: 'white',
        boxShadow: '0 2px 8px rgba(239, 68, 68, 0.4)'
    },
    buttonIcon: {
        fontSize: 18,
        fontWeight: 'bold'
    },
    timelineSection: {
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flex: 1
    },
    timeLabel: {
        fontSize: 12,
        fontWeight: 600,
        color: '#64748b',
        fontFamily: "'SF Mono', 'Monaco', 'Inconsolata', monospace",
        minWidth: 45
    },
    sliderContainer: {
        flex: 1,
        position: 'relative',
        height: 6,
        display: 'flex',
        alignItems: 'center'
    },
    sliderTrack: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 6,
        borderRadius: 3,
        pointerEvents: 'none'
    },
    sliderInput: {
        width: '100%',
        height: 6,
        appearance: 'none',
        background: 'transparent',
        cursor: 'pointer',
        position: 'relative',
        zIndex: 1,
        margin: 0
    },
    timeDisplaySection: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: 2
    },
    currentTime: {
        fontSize: 28,
        fontWeight: 700,
        color: '#1e293b',
        fontFamily: "'SF Mono', 'Monaco', 'Inconsolata', monospace",
        letterSpacing: '-0.02em',
        lineHeight: 1
    },
    statusBadge: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '2px 8px',
        backgroundColor: '#f8fafc',
        borderRadius: 12
    },
    statusDot: {
        width: 8,
        height: 8,
        borderRadius: '50%',
        animation: 'pulse 2s infinite'
    },
    statusText: {
        fontSize: 11,
        fontWeight: 600,
        color: '#64748b',
        textTransform: 'uppercase',
        letterSpacing: '0.05em'
    },
    main: {
        flex: 1,
        position: 'relative'
    },
    loading: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontSize: 18,
        color: '#94a3b8'
    },
    error: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontSize: 16,
        color: '#ef4444'
    }
};

export default CityVisualization;
