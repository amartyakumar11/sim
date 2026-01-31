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
import { SendOutlined, PlusOutlined, DeleteOutlined, CloudDownloadOutlined } from '@ant-design/icons'
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
  console.log("ScenarioSubmission Loaded - v3 (Pricing Included)")

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

      const scenarioData = {
        description: values.description,
        city_config: {
          zones: ['central_lucknow', 'gomti_nagar', 'alambagh', 'hazratganj'],
          stations: stations
        },
        interventions: interventions,
        simulation_duration: values.duration_minutes * 60,
        duration_minutes: values.duration_minutes,
        mode: mode
      }

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

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ marginBottom: 32 }}>
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

      {/* Main Form Card */}
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
            duration_minutes: 60
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

          {/* Duration & Mode */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
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
    </div>
  )
}

export default ScenarioSubmission
