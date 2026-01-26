import React, { useRef, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { Card } from 'antd'

// Set your Mapbox token (use environment variable in production)
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || 'pk.YOUR_MAPBOX_TOKEN'

function StationMap({ stations = [], center = [-74.0060, 40.7128], zoom = 11 }) {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  useEffect(() => {
    if (map.current) return // Initialize map only once

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: center,
      zoom: zoom
    })

    map.current.on('load', () => {
      setMapLoaded(true)
    })

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right')

    return () => {
      if (map.current) {
        map.current.remove()
      }
    }
  }, [])

  useEffect(() => {
    if (!mapLoaded || !map.current) return

    // Remove existing markers
    const markers = document.querySelectorAll('.station-marker')
    markers.forEach(marker => marker.remove())

    // Add markers for each station
    stations.forEach((station) => {
      // Create marker element
      const el = document.createElement('div')
      el.className = 'station-marker'
      el.style.cssText = `
        width: 30px;
        height: 30px;
        background-color: #1890ff;
        border: 2px solid white;
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      `

      // Create popup
      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="padding: 8px;">
          <strong>${station.station_id}</strong><br/>
          Zone: ${station.zone_id}<br/>
          Chargers: ${station.chargers_active || station.chargers_total || 'N/A'}
        </div>
      `)

      // Add marker to map
      new mapboxgl.Marker(el)
        .setLngLat([station.lon, station.lat])
        .setPopup(popup)
        .addTo(map.current)
    })

    // Fit map to show all stations
    if (stations.length > 0) {
      const bounds = new mapboxgl.LngLatBounds()
      stations.forEach(station => {
        bounds.extend([station.lon, station.lat])
      })
      map.current.fitBounds(bounds, { padding: 50 })
    }
  }, [stations, mapLoaded])

  return (
    <Card>
      <div 
        ref={mapContainer} 
        style={{ 
          width: '100%', 
          height: '400px',
          borderRadius: '8px'
        }} 
      />
    </Card>
  )
}

export default StationMap
