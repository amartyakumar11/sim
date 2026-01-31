/**
 * CityCanvas: Main visualization component for digital twin city view.
 * 
 * Renders three layers:
 * 1. City baseline (zones + stations)
 * 2. Zone pressure overlay
 * 3. Hero rider journey
 * 
 * Read-only visualization - NO simulation, NO backend calls.
 */

import React, { useState, useEffect } from 'react';
import ZoneLayer from './ZoneLayer';
import StationLayer from './StationLayer';
import RiderPathLayer from './RiderPathLayer';

const CityCanvas = () => {
  const [cityGraph, setCityGraph] = useState(null);
  const [zonePressure, setZonePressure] = useState([]);
  const [stationTimelines, setStationTimelines] = useState({});
  const [riderTraces, setRiderTraces] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Layer toggles
  const [showZones, setShowZones] = useState(true);
  const [showStations, setShowStations] = useState(true);
  const [showRider, setShowRider] = useState(true);

  // Load JSON artifacts on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load sample data for testing
        // In production, replace with API calls to load actual observability artifacts
        const { getSampleCityGraph, getSampleZonePressure, getSampleStationTimelines, getSampleRiderTraces } =
          await import('../services/sampleData.js');

        setCityGraph(getSampleCityGraph());
        setZonePressure(getSampleZonePressure());
        setStationTimelines(getSampleStationTimelines());
        setRiderTraces(getSampleRiderTraces());

        setLoading(false);
      } catch (err) {
        console.error('Failed to load visualization data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading city visualization...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>Error: {error}</div>
      </div>
    );
  }

  if (!cityGraph) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>No city data available</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.title}>Digital Twin City View</h2>
        <div style={styles.controls}>
          <label style={styles.toggle}>
            <input
              type="checkbox"
              checked={showZones}
              onChange={(e) => setShowZones(e.target.checked)}
            />
            <span style={styles.toggleLabel}>Zones</span>
          </label>
          <label style={styles.toggle}>
            <input
              type="checkbox"
              checked={showStations}
              onChange={(e) => setShowStations(e.target.checked)}
            />
            <span style={styles.toggleLabel}>Stations</span>
          </label>
          <label style={styles.toggle}>
            <input
              type="checkbox"
              checked={showRider}
              onChange={(e) => setShowRider(e.target.checked)}
            />
            <span style={styles.toggleLabel}>Rider Journey</span>
          </label>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        width={800}
        height={600}
        style={styles.canvas}
        viewBox="0 0 800 600"
      >
        {/* Layer 1: Zones with pressure overlay */}
        {showZones && (
          <ZoneLayer
            cityGraph={cityGraph}
            zonePressure={zonePressure}
          />
        )}

        {/* Layer 2: Stations */}
        {showStations && (
          <StationLayer
            cityGraph={cityGraph}
            stationTimelines={stationTimelines}
          />
        )}

        {/* Layer 3: Hero Rider Path */}
        {showRider && (
          <RiderPathLayer
            cityGraph={cityGraph}
            riderTraces={riderTraces}
          />
        )}
      </svg>

      {/* Legend */}
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendColor, backgroundColor: '#e0e0e0' }}></div>
          <span>Zone (Low Pressure)</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendColor, backgroundColor: 'rgba(255, 255, 0, 0.3)' }}></div>
          <span>Zone (Medium Pressure)</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendColor, backgroundColor: 'rgba(255, 0, 0, 0.3)' }}></div>
          <span>Zone (High Pressure)</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendColor, backgroundColor: '#2196F3', borderRadius: '50%' }}></div>
          <span>Station</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendColor, backgroundColor: 'transparent', border: '2px solid #9C27B0' }}></div>
          <span>Rider Journey</span>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
    maxWidth: '900px',
    margin: '0 auto'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    borderBottom: '2px solid #ddd',
    paddingBottom: '10px'
  },
  title: {
    margin: 0,
    color: '#333',
    fontSize: '24px'
  },
  controls: {
    display: 'flex',
    gap: '15px'
  },
  toggle: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    cursor: 'pointer'
  },
  toggleLabel: {
    fontSize: '14px',
    userSelect: 'none'
  },
  canvas: {
    border: '1px solid #ccc',
    borderRadius: '4px',
    backgroundColor: '#fafafa',
    display: 'block'
  },
  legend: {
    marginTop: '20px',
    padding: '15px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '15px'
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px'
  },
  legendColor: {
    width: '20px',
    height: '20px',
    border: '1px solid #999'
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

export default CityCanvas;
