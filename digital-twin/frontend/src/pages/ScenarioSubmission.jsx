import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Form,
  Input,
  InputNumber,
  Button,
  message,
  Switch,
  Divider,
  Card,
  Slider,
  Space,
  Select,
  Typography,
  Alert
} from 'antd'
import { SendOutlined, PlusOutlined, DeleteOutlined, CloudDownloadOutlined, CodeOutlined, FormOutlined } from '@ant-design/icons'
import { simulationAPI } from '../services/api'

const { TextArea } = Input
const { Text } = Typography
const { Option } = Select

function ScenarioSubmission() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState("fake")
  const [stations, setStations] = useState([
    {
      station_id: 'st_001',
      lat: 26.8467,
      lon: 80.9462,
      zone_id: 'central_lucknow',
      chargers_total: 4,
      chargers_active: 4
    }
  ])
  const navigate = useNavigate()

  // Demand multiplier states
  const [demandMultiplier, setDemandMultiplier] = useState(1.0)
  const [zoneDemandMultipliers, setZoneDemandMultipliers] = useState({
    central_lucknow: 1.0,
    gomti_nagar: 1.0,
    alambagh: 1.0,
    hazratganj: 1.0
  })

  // Verify component version
  console.log("ScenarioSubmission Loaded - v4 (Presets Added)")

  // JSON Editor Mode
  const [jsonMode, setJsonMode] = useState(false)
  
  // Preset Scenarios
  const presetScenarios = {
    baseline: {
      name: "🎯 Baseline",
      description: "Normal operations - 1x demand, standard pricing",
      config: {
        "description": "Baseline scenario - normal operations",
        "city_config": {
          "zones": ["central_lucknow", "gomti_nagar"],
          "stations": [
            {"station_id": "S1", "lat": 26.86, "lon": 80.92, "zone_id": "central_lucknow", "chargers_total": 4},
            {"station_id": "S2", "lat": 26.87, "lon": 81.00, "zone_id": "gomti_nagar", "chargers_total": 4}
          ]
        },
        "interventions": {
          "demand_multiplier": 1.0,
          "pricing": {"primary_price": 170, "secondary_price": 70, "service_charge": 40}
        },
        "simulation_duration": 3600,
        "mode": "real",
        "seed": 42
      }
    },
    stressTest: {
      name: "🔥 Stress Test",
      description: "5x demand surge - tests system limits",
      config: {
        "description": "Stress test - 5x demand surge",
        "city_config": {
          "zones": ["central_lucknow", "gomti_nagar"],
          "stations": [
            {"station_id": "S1", "lat": 26.86, "lon": 80.92, "zone_id": "central_lucknow", "chargers_total": 4},
            {"station_id": "S2", "lat": 26.87, "lon": 81.00, "zone_id": "gomti_nagar", "chargers_total": 4}
          ]
        },
        "interventions": {
          "demand_multiplier": 5.0,
          "pricing": {"primary_price": 170, "secondary_price": 70, "service_charge": 40}
        },
        "simulation_duration": 3600,
        "mode": "real",
        "seed": 42
      }
    },
    premiumPricing: {
      name: "💰 Premium Pricing",
      description: "High pricing model - ₹250 base price",
      config: {
        "description": "Premium pricing experiment",
        "city_config": {
          "zones": ["central_lucknow", "gomti_nagar"],
          "stations": [
            {"station_id": "S1", "lat": 26.86, "lon": 80.92, "zone_id": "central_lucknow", "chargers_total": 4},
            {"station_id": "S2", "lat": 26.87, "lon": 81.00, "zone_id": "gomti_nagar", "chargers_total": 4}
          ]
        },
        "interventions": {
          "demand_multiplier": 1.5,
          "pricing": {"primary_price": 250, "secondary_price": 100, "service_charge": 50}
        },
        "simulation_duration": 3600,
        "mode": "real",
        "seed": 42
      }
    },
    capacityExpansion: {
      name: "🔋 Capacity Expansion",
      description: "10 chargers per station - tests scaling",
      config: {
        "description": "Capacity expansion - 10 chargers per station",
        "city_config": {
          "zones": ["central_lucknow", "gomti_nagar"],
          "stations": [
            {"station_id": "S1", "lat": 26.86, "lon": 80.92, "zone_id": "central_lucknow", "chargers_total": 10},
            {"station_id": "S2", "lat": 26.87, "lon": 81.00, "zone_id": "gomti_nagar", "chargers_total": 10}
          ]
        },
        "interventions": {
          "demand_multiplier": 3.0,
          "pricing": {"primary_price": 170, "secondary_price": 70, "service_charge": 40}
        },
        "simulation_duration": 3600,
        "mode": "real",
        "seed": 42
      }
    },
    peakHourCrunch: {
      name: "⚡ Peak Hour Crunch",
      description: "High demand + limited capacity = realistic stress",
      config: {
        "description": "Peak hour scenario - high demand, limited capacity",
        "city_config": {
          "zones": ["central_lucknow", "gomti_nagar", "hazratganj"],
          "stations": [
            {"station_id": "S1", "lat": 26.86, "lon": 80.92, "zone_id": "central_lucknow", "chargers_total": 2},
            {"station_id": "S2", "lat": 26.87, "lon": 81.00, "zone_id": "gomti_nagar", "chargers_total": 2},
            {"station_id": "S3", "lat": 26.85, "lon": 80.95, "zone_id": "hazratganj", "chargers_total": 2}
          ]
        },
        "interventions": {
          "demand_multiplier": 4.0,
          "pricing": {"primary_price": 200, "secondary_price": 80, "service_charge": 40}
        },
        "simulation_duration": 3600,
        "mode": "real",
        "seed": 42
      }
    },
    congestionTest: {
      name: "🚨 Congestion Test",
      description: "1 bay per station + 20x demand = shows wait times",
      config: {
        "description": "Congestion test - extreme demand on minimal infrastructure",
        "city_config": {
          "zones": ["central_lucknow", "gomti_nagar"],
          "stations": [
            {"station_id": "S1", "lat": 26.86, "lon": 80.92, "zone_id": "central_lucknow", "chargers_total": 1, "swap_bays": 1, "inventory_capacity": 50, "inventory_current": 50},
            {"station_id": "S2", "lat": 26.87, "lon": 81.00, "zone_id": "gomti_nagar", "chargers_total": 1, "swap_bays": 1, "inventory_capacity": 50, "inventory_current": 50}
          ]
        },
        "interventions": {
          "demand_multiplier": 20.0,
          "pricing": {"primary_price": 170, "secondary_price": 70, "service_charge": 40}
        },
        "simulation_duration": 3600,
        "mode": "real",
        "seed": 42
      }
    }
  }
  
  const [selectedPreset, setSelectedPreset] = useState(null)
  const [jsonInput, setJsonInput] = useState(JSON.stringify(presetScenarios.baseline.config, null, 2))
  const [jsonError, setJsonError] = useState(null)

  // Pricing State
  const [primaryPrice, setPrimaryPrice] = useState(170)
  const [secondaryPrice, setSecondaryPrice] = useState(70)
  const [secondaryProb, setSecondaryProb] = useState(0.3)
  const [penaltyPrice, setPenaltyPrice] = useState(60)
  const [penaltyProb, setPenaltyProb] = useState(0.05)
  const [serviceCharge, setServiceCharge] = useState(40)

  // Load full Lucknow network (371 stations)
  const loadFullNetwork = async () => {
    try {
      const response = await fetch('/data/lucknow_stations.json?v=3')
      const data = await response.json()

      // Robustly handle data format
      const stationsArray = (data && Array.isArray(data)) ? data : ((data && data.stations) || [])

      const determineZone = (lat, lon) => {
        // Centroids for major zones
        const zones = {
          gomti_nagar: { lat: 26.870, lon: 81.000 },
          alambagh: { lat: 26.810, lon: 80.900 },
          hazratganj: { lat: 26.850, lon: 80.945 },
          central_lucknow: { lat: 26.840, lon: 80.920 } // Bias towards Charbagh/Central
        }

        let closestZone = 'central_lucknow'
        let minDist = Infinity

        Object.entries(zones).forEach(([zone, coords]) => {
          const d = Math.sqrt(Math.pow(lat - coords.lat, 2) + Math.pow(lon - coords.lon, 2))
          if (d < minDist) {
            minDist = d
            closestZone = zone
          }
        })

        return closestZone
      }

      const formattedStations = (stationsArray || []).map((s, index) => {
        const lat = parseFloat(s.latitude || s.lat)
        const lon = parseFloat(s.longitude || s.lon)

        // Safety check for invalid coordinates
        if (isNaN(lat) || isNaN(lon)) {
          console.warn(`Invalid coordinates for station ${s.id}`, s)
          return { ...s, zone_id: 'central_lucknow' }
        }

        // FORCE geographic zone assignment (ignore bad data in JSON)
        const zone = determineZone(lat, lon)

        // Debug first 3 stations
        if (index < 3) console.log(`Station ${s.id} (${lat}, ${lon}) -> ${zone}`)

        return {
          station_id: s.station_id || s.id || `st_${String(index + 1).padStart(3, '0')}`,
          lat: lat,
          lon: lon,
          zone_id: zone,
          chargers_total: s.chargers_total || 4,
          chargers_active: s.chargers_total || 4
        }
      })

      setStations(formattedStations)

      // Calculate zone distribution for feedback
      const counts = formattedStations.reduce((acc, s) => {
        acc[s.zone_id] = (acc[s.zone_id] || 0) + 1
        return acc
      }, {})

      console.log("Zone Counts:", counts) // Debug full counts

      message.success(
        <span>
          Loaded {formattedStations.length} stations<br />
          <span style={{ fontSize: 12 }}>
            (Gomti: {counts.gomti_nagar || 0},
            Alambagh: {counts.alambagh || 0},
            Haz: {counts.hazratganj || 0},
            Central: {counts.central_lucknow || 0})
          </span>
        </span>,
        4
      )
    } catch (error) {
      console.error(error)
      message.error('Failed to load network: ' + error.message)
    }
  }

  const handleSubmit = async (values) => {
    setLoading(true)
    try {
      // Auto-build interventions from UI state
      const interventions = {}

      // Global demand multiplier
      if (demandMultiplier !== 1.0) {
        interventions.demand_multiplier = demandMultiplier
      }

      // Zone-specific multipliers (only if different from 1.0)
      const zoneMultipliers = {}
      Object.entries(zoneDemandMultipliers).forEach(([zone, mult]) => {
        if (mult !== 1.0) {
          zoneMultipliers[zone] = mult
        }
      })

      if (Object.keys(zoneMultipliers).length > 0) {
        interventions.zone_demand_multipliers = zoneMultipliers
      }

      // Add pricing configuration
      interventions.pricing = {
        primary_price: primaryPrice,
        secondary_price: secondaryPrice,
        secondary_prob: secondaryProb,
        penalty_price: penaltyPrice,
        penalty_prob: penaltyProb,
        service_charge: serviceCharge
      }

      const scenarioData = {
        description: values.description,
        city_config: {
          zones: ['central_lucknow', 'gomti_nagar', 'alambagh', 'hazratganj'],
          stations: stations
        },
        interventions: interventions,
        simulation_duration: values.duration_minutes * 60,
        duration_minutes: values.duration_minutes,
        seed: values.seed || 42,  // Include seed for determinism
        mode: mode
      }

      // DEBUG: Log what's being sent
      console.log('=== SCENARIO SUBMISSION DEBUG ===')
      console.log('demandMultiplier state:', demandMultiplier)
      console.log('interventions:', JSON.stringify(interventions, null, 2))
      console.log('Full scenarioData:', JSON.stringify(scenarioData, null, 2))
      console.log('=================================')

      const response = await simulationAPI.submitScenario(scenarioData)
      message.success(`Scenario submitted successfully`)

      setTimeout(() => {
        navigate(`/monitor?runId=${response.run_id}`)
      }, 1200)
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message
      message.error(`Failed to submit: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const addStation = () => {
    const newStation = {
      station_id: `st_${String(stations.length + 1).padStart(3, '0')}`,
      lat: 26.8467 + (Math.random() - 0.5) * 0.1, // Lucknow city center ± ~5km
      lon: 80.9462 + (Math.random() - 0.5) * 0.1,
      zone_id: 'central_lucknow',
      chargers_total: 4,
      chargers_active: 4
    }
    setStations([...stations, newStation])
  }

  const removeStation = (index) => {
    setStations(stations.filter((_, i) => i !== index))
  }

  // JSON Mode Submit Handler
  const handleJsonSubmit = async () => {
    setLoading(true)
    setJsonError(null)
    try {
      const scenarioData = JSON.parse(jsonInput)
      console.log('=== JSON SUBMISSION ===')
      console.log(JSON.stringify(scenarioData, null, 2))
      console.log('=======================')
      
      const response = await simulationAPI.submitScenario(scenarioData)
      message.success(`Scenario submitted successfully! Run ID: ${response.run_id}`)
      
      setTimeout(() => {
        navigate(`/monitor?runId=${response.run_id}`)
      }, 1200)
    } catch (error) {
      if (error instanceof SyntaxError) {
        setJsonError(`Invalid JSON: ${error.message}`)
        message.error('Invalid JSON syntax')
      } else {
        const errorMsg = error.response?.data?.detail || error.message
        setJsonError(errorMsg)
        message.error(`Failed to submit: ${errorMsg}`)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ marginBottom: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{
            fontSize: 32,
            fontWeight: 700,
            color: 'var(--color-text-primary)',
            marginBottom: 8,
            letterSpacing: '-0.02em'
          }}>
            New Scenario
          </h1>
          <p style={{
            fontSize: 15,
            color: 'var(--color-text-secondary)',
            margin: 0
          }}>
            Configure your simulation with city layout, stations, and operational interventions.
          </p>
        </div>
        <Button.Group>
          <Button 
            type={!jsonMode ? 'primary' : 'default'}
            icon={<FormOutlined />}
            onClick={() => setJsonMode(false)}
          >
            Form
          </Button>
          <Button 
            type={jsonMode ? 'primary' : 'default'}
            icon={<CodeOutlined />}
            onClick={() => setJsonMode(true)}
          >
            JSON
          </Button>
        </Button.Group>
      </div>

      {/* JSON Editor Mode */}
      {jsonMode ? (
        <div style={{
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border-light)',
          borderRadius: 'var(--radius-xl)',
          padding: 32,
          boxShadow: 'var(--shadow-sm)'
        }}>
          <h3 style={{ marginBottom: 16, color: 'var(--color-text-primary)' }}>
            <CodeOutlined /> Direct JSON Input
          </h3>
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            Select a preset or customize your own scenario configuration.
          </p>
          
          {/* Preset Buttons */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 8, fontWeight: 500 }}>
              Quick Presets:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {Object.entries(presetScenarios).map(([key, preset]) => (
                <Button
                  key={key}
                  type={selectedPreset === key ? 'primary' : 'default'}
                  size="small"
                  onClick={() => {
                    setSelectedPreset(key)
                    setJsonInput(JSON.stringify(preset.config, null, 2))
                    setJsonError(null)
                    message.success(`Loaded: ${preset.name}`)
                  }}
                  title={preset.description}
                  style={{
                    borderRadius: 16,
                    fontSize: 13
                  }}
                >
                  {preset.name}
                </Button>
              ))}
            </div>
            {selectedPreset && (
              <div style={{ 
                marginTop: 8, 
                fontSize: 12, 
                color: 'var(--color-text-secondary)',
                fontStyle: 'italic'
              }}>
                {presetScenarios[selectedPreset].description}
              </div>
            )}
          </div>
          
          {jsonError && (
            <Alert 
              type="error" 
              message="Validation Error" 
              description={jsonError}
              showIcon 
              style={{ marginBottom: 16 }}
              closable
              onClose={() => setJsonError(null)}
            />
          )}
          
          <TextArea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            rows={25}
            style={{
              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
              fontSize: 13,
              background: '#1a1a2e',
              color: '#00ff88',
              border: '1px solid #333',
              borderRadius: 8
            }}
            placeholder="Enter JSON scenario..."
          />
          
          <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
            <Button 
              type="primary" 
              icon={<SendOutlined />}
              onClick={handleJsonSubmit}
              loading={loading}
              size="large"
            >
              Submit JSON Scenario
            </Button>
            <Button 
              onClick={() => {
                try {
                  const formatted = JSON.stringify(JSON.parse(jsonInput), null, 2)
                  setJsonInput(formatted)
                  setJsonError(null)
                  message.success('JSON formatted')
                } catch (e) {
                  setJsonError(`Invalid JSON: ${e.message}`)
                }
              }}
            >
              Format JSON
            </Button>
          </div>
        </div>
      ) : (
      /* Main Form Card */
      <div style={{
        background: 'var(--color-bg-elevated)',
        border: '1px solid var(--color-border-light)',
        borderRadius: 'var(--radius-xl)',
        padding: 32,
        boxShadow: 'var(--shadow-sm)'
      }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            description: 'Test scenario',
            duration_minutes: 60,
            seed: 42
          }}
        >
          {/* Description */}
          <Form.Item
            label={<span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>Scenario Description</span>}
            name="description"
            rules={[
              { required: true, message: 'Please enter a description' },
              { min: 1, max: 500, message: 'Description must be 1-500 characters' }
            ]}
          >
            <TextArea
              rows={3}
              placeholder="e.g., Add 5 charging stations to downtown area to reduce wait times"
              style={{
                borderRadius: 'var(--radius-md)',
                fontSize: 14
              }}
            />
          </Form.Item>

          {/* Duration, Mode & Seed */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <Form.Item
              label={<span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>Duration (minutes)</span>}
              name="duration_minutes"
              rules={[{ required: true, message: 'Please enter duration' }]}
              tooltip="Simulation time: 60 = 1 hour, 1440 = 1 day, 10080 = 1 week"
            >
              <InputNumber
                min={1}
                max={43200}
                style={{
                  width: '100%',
                  borderRadius: 'var(--radius-md)'
                }}
              />
            </Form.Item>

            <Form.Item
              label={<span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>Random Seed</span>}
              name="seed"
              tooltip="Same seed + same config = identical results (for reproducibility)"
              initialValue={42}
            >
              <InputNumber
                min={1}
                max={999999}
                style={{
                  width: '100%',
                  borderRadius: 'var(--radius-md)'
                }}
                placeholder="42"
              />
            </Form.Item>

            <div>
              <label style={{
                display: 'block',
                marginBottom: 8,
                fontWeight: 600,
                color: 'var(--color-text-primary)',
                fontSize: 14
              }}>
                Simulation Mode
              </label>
              <div style={{
                padding: 16,
                background: 'var(--color-bg-subtle)',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                border: '1px solid var(--color-border-light)'
              }}>
                <div>
                  <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--color-text-primary)' }}>
                    {mode === 'real' ? 'Real Simulation' : 'Fast Mode'}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-tertiary)', marginTop: 2 }}>
                    {mode === 'real' ? 'Full SimPy engine' : 'Instant results'}
                  </div>
                </div>
                <Switch
                  checked={mode === "real"}
                  onChange={(checked) => setMode(checked ? "real" : "fake")}
                />
              </div>
            </div>
          </div>

          <Divider style={{ margin: '32px 0', borderColor: 'var(--color-border-light)' }} />

          {/* Demand Scenarios Section */}
          <Card
            title="Demand Scenarios"
            style={{ marginBottom: 24 }}
            extra={
              <Select
                placeholder="Load preset"
                style={{ width: 180 }}
                onChange={(preset) => {
                  const presets = {
                    normal: { global: 1.0, zones: { central_lucknow: 1.0, gomti_nagar: 1.0, alambagh: 1.0, hazratganj: 1.0 } },
                    peak: { global: 3.0, zones: { central_lucknow: 3.0, gomti_nagar: 3.0, alambagh: 3.0, hazratganj: 3.0 } },
                    gomti_growth: { global: 1.0, zones: { central_lucknow: 1.0, gomti_nagar: 2.0, alambagh: 1.0, hazratganj: 1.0 } },
                    festival: { global: 5.0, zones: { central_lucknow: 5.0, gomti_nagar: 5.0, alambagh: 5.0, hazratganj: 5.0 } }
                  }
                  const p = presets[preset]
                  setDemandMultiplier(p.global)
                  setZoneDemandMultipliers(p.zones)
                }}
              >
                <Option value="normal">Normal Operations</Option>
                <Option value="peak">Peak Hour (3x)</Option>
                <Option value="gomti_growth">Gomti Nagar Doubles</Option>
                <Option value="festival">Festival (5x)</Option>
              </Select>
            }
          >
            <Form.Item label="Global Demand Multiplier">
              <Slider
                min={0.5}
                max={5.0}
                step={0.1}
                value={demandMultiplier}
                onChange={setDemandMultiplier}
                marks={{
                  0.5: '0.5x',
                  1.0: 'Normal',
                  2.0: '2x',
                  3.0: '3x',
                  5.0: '5x'
                }}
              />
              <Text type="secondary">
                {demandMultiplier}x demand citywide
                {demandMultiplier >= 3 && ' 🔥 High Load'}
              </Text>
            </Form.Item>

            <Divider style={{ margin: '16px 0' }} />

            <Form.Item label="Zone-Specific Multipliers">
              <Space direction="vertical" style={{ width: '100%' }}>
                {Object.keys(zoneDemandMultipliers).map(zone => (
                  <div key={zone} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Text style={{ width: 140, fontWeight: 500 }}>
                      {zone.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Text>
                    <Slider
                      style={{ flex: 1 }}
                      min={0.5}
                      max={5.0}
                      step={0.1}
                      value={zoneDemandMultipliers[zone]}
                      onChange={(val) => setZoneDemandMultipliers({
                        ...zoneDemandMultipliers,
                        [zone]: val
                      })}
                    />
                    <Text style={{ width: 50, textAlign: 'right' }}>
                      {zoneDemandMultipliers[zone]}x
                    </Text>
                  </div>
                ))}
              </Space>
            </Form.Item>

            <Alert
              message="Effective Demand"
              description={
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                  {Object.entries(zoneDemandMultipliers).map(([zone, zoneMult]) => {
                    const effective = (demandMultiplier * zoneMult).toFixed(1)
                    return (
                      <span key={zone}>
                        <strong>{zone.split('_')[0]}:</strong> {effective}x
                        {effective >= 3 && ' 🔥'}
                      </span>
                    )
                  })}
                </div>
              }
              type="info"
              showIcon
            />
          </Card>

          {/* Pricing Model Section */}
          <Card title="Pricing Structure (BatterySmart)" style={{ marginBottom: 24 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
              <Form.Item label="Primary Swap Price (₹)">
                <InputNumber value={primaryPrice} onChange={setPrimaryPrice} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item label="Secondary Swap Price (₹)">
                <InputNumber value={secondaryPrice} onChange={setSecondaryPrice} style={{ width: '100%' }} />
              </Form.Item>
            </div>

            <Form.Item label={`Secondary Usage: ${Math.round(secondaryProb * 100)}% of swaps`}>
              <Slider
                min={0} max={1} step={0.05}
                value={secondaryProb}
                onChange={setSecondaryProb}
                tooltip={{ formatter: val => `${Math.round(val * 100)}%` }}
              />
            </Form.Item>

            <Divider />

            <div style={{ display: 'flex', gap: 24 }}>
              <Form.Item label="Service Charge (₹)" style={{ flex: 1 }}>
                <InputNumber value={serviceCharge} onChange={setServiceCharge} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item label="Penalty Recovery (₹)" style={{ flex: 1 }}>
                <InputNumber value={penaltyPrice} onChange={setPenaltyPrice} style={{ width: '100%' }} />
              </Form.Item>
            </div>

            <Form.Item label={`Penalty Occurrence: ${Math.round(penaltyProb * 100)}% of swaps`}>
              <Slider
                min={0} max={0.5} step={0.01}
                value={penaltyProb}
                onChange={setPenaltyProb}
                tooltip={{ formatter: val => `${Math.round(val * 100)}%` }}
              />
              <Text type="secondary">Probability of recovering a leave penalty during a swap</Text>
            </Form.Item>
          </Card>

          {/* Stations Section */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{
              fontSize: 16,
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              marginBottom: 16,
              letterSpacing: '-0.01em'
            }}>
              Station Configuration
              <span style={{
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--color-text-tertiary)',
                marginLeft: 8
              }}>
                ({stations.length} station{stations.length !== 1 ? 's' : ''})
              </span>
            </h3>

            {/* Load Full Network Button */}
            <Button
              type="primary"
              icon={<CloudDownloadOutlined />}
              onClick={loadFullNetwork}
              size="large"
              block
              style={{ marginBottom: 16 }}
            >
              Load Full Lucknow Network (371 Stations)
            </Button>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {stations.map((station, index) => (
                <div
                  key={index}
                  style={{
                    padding: 16,
                    background: 'var(--color-bg-subtle)',
                    border: '1px solid var(--color-border-light)',
                    borderRadius: 'var(--radius-lg)',
                    display: 'grid',
                    gridTemplateColumns: '1fr auto',
                    gap: 16,
                    alignItems: 'start'
                  }}
                >
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: 12
                  }}>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                        Station ID
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 600, fontFamily: 'monospace', color: 'var(--color-text-primary)' }}>
                        {station.station_id}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                        Location
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                        {station.lat.toFixed(4)}, {station.lon.toFixed(4)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                        Zone
                      </div>
                      <div style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        background: 'rgba(59, 130, 246, 0.1)',
                        color: 'var(--color-accent-primary)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 12,
                        fontWeight: 500
                      }}>
                        {station.zone_id}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                        Chargers
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--color-text-primary)', fontWeight: 600 }}>
                        {station.chargers_active} / {station.chargers_total}
                      </div>
                    </div>
                  </div>

                  {stations.length > 1 && (
                    <Button
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => removeStation(index)}
                      style={{
                        borderRadius: 'var(--radius-md)'
                      }}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ))}
            </div>

            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={addStation}
              style={{
                width: '100%',
                marginTop: 12,
                height: 40,
                borderRadius: 'var(--radius-md)',
                borderStyle: 'dashed',
                borderColor: 'var(--color-border-medium)'
              }}
            >
              Add Station
            </Button>
          </div>

          {/* Submit Button */}
          <Form.Item style={{ marginBottom: 0, marginTop: 32 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SendOutlined />}
              size="large"
              block
              style={{
                height: 48,
                fontSize: 15,
                fontWeight: 600,
                borderRadius: 'var(--radius-lg)'
              }}
            >
              {loading ? 'Submitting Scenario...' : 'Submit Scenario'}
            </Button>
          </Form.Item>
        </Form>
      </div>
      )}
    </div>
  )
}

export default ScenarioSubmission
