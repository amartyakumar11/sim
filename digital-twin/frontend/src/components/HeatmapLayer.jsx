
import React, { useEffect, useState } from 'react';
import { Source, Layer } from 'react-map-gl/maplibre';
import { simulationAPI } from '../services/api';

const HeatmapLayer = ({ visible, scenarioConfig }) => {
    const [heatmapData, setHeatmapData] = useState(null);

    useEffect(() => {
        if (visible && !heatmapData && scenarioConfig) {
            // Fetch heatmap data if visible and not loaded
            const fetchHeatmap = async () => {
                try {
                    // We need to construct a pseudo-request object for the API
                    // This assumes scenarioConfig has the structure { city_config, interventions }
                    // If scenarioConfig is just the form values, we might need to adapt it

                    // Ideally, we fetch this from a robust endpoint, but for phase 1
                    // we can assume we have access to the current config context
                    // Or we mock it for the visualization if running live

                    const response = await simulationAPI.getDemandHeatmap(scenarioConfig);
                    setHeatmapData(response);
                } catch (err) {
                    console.error("Failed to load heatmap data:", err);
                }
            };
            fetchHeatmap();
        }
    }, [visible, heatmapData, scenarioConfig]);

    if (!visible || !heatmapData) return null;

    return (
        <Source id="demand-heatmap" type="geojson" data={heatmapData}>
            <Layer
                id="heatmap-layer"
                type="heatmap"
                paint={{
                    // Increase weight based on 'intensity' property
                    'heatmap-weight': [
                        'interpolate',
                        ['linear'],
                        ['get', 'intensity'],
                        0, 0,
                        1, 0.8,  // Increased base weight
                        2, 1
                    ],
                    // Increase intensity based on zoom level
                    'heatmap-intensity': [
                        'interpolate',
                        ['linear'],
                        ['zoom'],
                        0, 1,
                        15, 3
                    ],
                    // Color ramp: Transparent -> Green -> Yellow -> Red
                    'heatmap-color': [
                        'interpolate',
                        ['linear'],
                        ['heatmap-density'],
                        0, 'rgba(0, 255, 0, 0)',
                        0.2, 'rgba(0, 255, 0, 0.5)',   // Green
                        0.4, 'rgba(255, 255, 0, 0.6)', // Yellow
                        0.6, 'rgba(255, 165, 0, 0.7)', // Orange
                        0.8, 'rgba(255, 69, 0, 0.8)',  // Red-Orange
                        1, 'rgba(255, 0, 0, 0.9)'     // Red
                    ],
                    // Adjust radius based on zoom - Increased for better coverage
                    'heatmap-radius': [
                        'interpolate',
                        ['linear'],
                        ['zoom'],
                        0, 2,
                        9, 25,  // Increased from 20
                        15, 40  // Added higher zoom breakpoint
                    ],
                    // Transition from heatmap to circle layer by zoom level
                    'heatmap-opacity': [
                        'interpolate',
                        ['linear'],
                        ['zoom'],
                        7, 0.8, // Slightly more opaque
                        18, 0.5
                    ]
                }}
            />
        </Source>
    );
};

export default HeatmapLayer;
