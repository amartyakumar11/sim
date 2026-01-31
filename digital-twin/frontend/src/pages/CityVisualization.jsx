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
import CityCanvas from '../components/CityCanvas';
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
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Playback state
    const [currentMinute, setCurrentMinute] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [minMinute, setMinMinute] = useState(0);
    const [maxMinute, setMaxMinute] = useState(0);

    // Load data on mount
    useEffect(() => {
        const loadData = async () => {
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

                // Initialize playback range from zone pressure data
                const { minMinute: min, maxMinute: max } = getMinuteRange(zonePressureData);
                setMinMinute(min);
                setMaxMinute(max);
                setCurrentMinute(min); // Start at earliest minute

                setLoading(false);
            } catch (err) {
                console.error('Failed to load visualization data:', err);
                setError(err.message);
                setLoading(false);
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
            <header style={styles.header}>
                <h1 style={styles.title}>Digital Twin Visualization</h1>
                <p style={styles.subtitle}>
                    City view with zone pressure analysis and rider journeys
                </p>
            </header>

            {/* Playback Controls */}
            <div style={styles.playbackControls}>
                <div style={styles.playbackRow}>
                    <button
                        style={styles.playButton}
                        onClick={handlePlayPause}
                        aria-label={isPlaying ? 'Pause' : 'Play'}
                    >
                        {isPlaying ? '⏸ Pause' : '▶ Play'}
                    </button>
                    <button
                        style={styles.resetButton}
                        onClick={handleReset}
                        aria-label="Reset"
                    >
                        ↺ Reset
                    </button>
                    <div style={styles.timeDisplay}>
                        <span style={styles.timeLabel}>Time:</span>
                        <span style={styles.timeValue}>{formatMinuteAsTime(currentMinute)}</span>
                        <span style={styles.minuteLabel}>(minute {currentMinute})</span>
                    </div>
                </div>
                <div style={styles.sliderRow}>
                    <span style={styles.sliderLabel}>{formatMinuteAsTime(minMinute)}</span>
                    <input
                        type="range"
                        min={minMinute}
                        max={maxMinute}
                        value={currentMinute ?? minMinute}
                        onChange={handleSliderChange}
                        style={styles.slider}
                        aria-label="Time slider"
                    />
                    <span style={styles.sliderLabel}>{formatMinuteAsTime(maxMinute)}</span>
                </div>
                <div style={styles.playbackStatus}>
                    {isPlaying ? (
                        <span style={styles.statusPlaying}>● Playing</span>
                    ) : (
                        <span style={styles.statusPaused}>○ Paused</span>
                    )}
                </div>
            </div>

            <main style={styles.main}>
                <CityCanvas
                    cityGraph={cityGraph}
                    zonePressure={filteredZonePressure}
                    stationTimelines={filteredStationTimelines}
                    riderTraces={filteredRiderTraces}
                    currentMinute={currentMinute}
                />
            </main>

            <footer style={styles.footer}>
                <p style={styles.footerText}>
                    Read-only visualization • Data from simulation observability artifacts
                </p>
            </footer>
        </div>
    );
};

const styles = {
    page: {
        minHeight: '100vh',
        backgroundColor: '#f5f5f5',
        display: 'flex',
        flexDirection: 'column'
    },
    header: {
        backgroundColor: 'white',
        borderBottom: '1px solid #e0e0e0',
        padding: '20px',
        textAlign: 'center'
    },
    title: {
        margin: '0 0 10px 0',
        color: '#1976D2',
        fontSize: '32px'
    },
    subtitle: {
        margin: 0,
        color: '#666',
        fontSize: '16px'
    },
    playbackControls: {
        backgroundColor: 'white',
        borderBottom: '1px solid #e0e0e0',
        padding: '15px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
    },
    playbackRow: {
        display: 'flex',
        alignItems: 'center',
        gap: '15px',
        flexWrap: 'wrap'
    },
    playButton: {
        padding: '10px 24px',
        fontSize: '16px',
        fontWeight: 'bold',
        backgroundColor: '#1976D2',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'background-color 0.2s'
    },
    resetButton: {
        padding: '10px 18px',
        fontSize: '14px',
        backgroundColor: '#757575',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer'
    },
    timeDisplay: {
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginLeft: 'auto'
    },
    timeLabel: {
        color: '#666',
        fontSize: '14px'
    },
    timeValue: {
        fontSize: '24px',
        fontWeight: 'bold',
        fontFamily: 'monospace',
        color: '#1976D2'
    },
    minuteLabel: {
        color: '#999',
        fontSize: '12px'
    },
    sliderRow: {
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
    },
    slider: {
        flex: 1,
        height: '6px',
        cursor: 'pointer'
    },
    sliderLabel: {
        fontSize: '12px',
        color: '#666',
        fontFamily: 'monospace',
        minWidth: '50px'
    },
    playbackStatus: {
        textAlign: 'center'
    },
    statusPlaying: {
        color: '#4CAF50',
        fontWeight: 'bold',
        fontSize: '14px'
    },
    statusPaused: {
        color: '#FF9800',
        fontWeight: 'bold',
        fontSize: '14px'
    },
    main: {
        flex: 1,
        padding: '20px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start'
    },
    footer: {
        backgroundColor: 'white',
        borderTop: '1px solid #e0e0e0',
        padding: '15px',
        textAlign: 'center'
    },
    footerText: {
        margin: 0,
        color: '#999',
        fontSize: '13px'
    },
    loading: {
        textAlign: 'center',
        padding: '50px',
        fontSize: '18px',
        color: '#666'
    },
    error: {
        textAlign: 'center',
        padding: '50px',
        fontSize: '16px',
        color: '#f44336'
    }
};

export default CityVisualization;
