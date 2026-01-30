import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Form, 
  Input, 
  InputNumber, 
  Button, 
  message, 
  Switch,
  Divider
} from 'antd'
import { SendOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { simulationAPI } from '../services/api'

const { TextArea } = Input

function ScenarioSubmission() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState("fake")
  const [stations, setStations] = useState([
    {
      station_id: 'st_001',
      lat: 40.7128,
      lon: -74.0060,
      zone_id: 'downtown',
      chargers_total: 4,
      chargers_active: 4
    }
  ])
  const navigate = useNavigate()

  const handleSubmit = async (values) => {
    setLoading(true)
    try {
      const scenarioData = {
        description: values.description,
        city_config: {
          zones: ['downtown', 'suburb_north', 'suburb_south'],
          stations: stations
        },
        interventions: values.interventions ? JSON.parse(values.interventions) : {},
        simulation_duration: values.duration_minutes * 60, // Convert minutes to seconds for backend
        duration_minutes: values.duration_minutes, // Already in minutes
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
      lat: 40.7128 + (Math.random() - 0.5) * 0.1,
      lon: -74.0060 + (Math.random() - 0.5) * 0.1,
      zone_id: 'downtown',
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

          {/* Interventions */}
          <Form.Item
            label={<span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>Interventions (JSON, optional)</span>}
            name="interventions"
            extra={<span style={{ fontSize: 12, color: 'var(--color-text-tertiary)' }}>Define station additions, capacity upgrades, or operational changes</span>}
          >
            <TextArea 
              rows={6}
              placeholder={`{\n  "add_stations": [...],\n  "modify_chargers": {...}\n}`}
              style={{ 
                fontFamily: 'monospace',
                fontSize: 13,
                borderRadius: 'var(--radius-md)',
                background: 'var(--color-bg-subtle)'
              }}
            />
          </Form.Item>

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
