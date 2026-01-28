import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Card, 
  Form, 
  Input, 
  InputNumber, 
  Button, 
  message, 
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Tag
} from 'antd'
import { SendOutlined, PlusOutlined } from '@ant-design/icons'
import { simulationAPI } from '../services/api'

const { Title, Paragraph } = Typography
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
        simulation_duration: values.simulation_duration,
        mode: mode
      }

      const response = await simulationAPI.submitScenario(scenarioData)
      message.success(`Scenario submitted! Run ID: ${response.run_id}`)
      
      // Navigate to monitor page
      setTimeout(() => {
        navigate(`/monitor?runId=${response.run_id}`)
      }, 1500)
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message
      message.error(`Failed to submit scenario: ${errorMsg}`)
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
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <Card>
        <Title level={2}>🚀 Submit New Scenario</Title>
        <Paragraph>
          Configure your simulation scenario with city layout, stations, and interventions.
        </Paragraph>
        
        <Divider />

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            description: 'Test scenario',
            simulation_duration: 3600
          }}
        >
          <Form.Item
            label="Scenario Description"
            name="description"
            rules={[
              { required: true, message: 'Please enter a description' },
              { min: 1, max: 500, message: 'Description must be 1-500 characters' }
            ]}
          >
            <Input.TextArea 
              rows={3} 
              placeholder="e.g., Add 5 charging stations to downtown area"
            />
          </Form.Item>

          <Form.Item
            label="Simulation Duration (seconds)"
            name="simulation_duration"
            rules={[{ required: true }]}
          >
            <InputNumber 
              min={60} 
              max={86400} 
              style={{ width: '100%' }}
              addonAfter="seconds"
            />
          </Form.Item>

          <Form.Item
            label="Simulation Mode"
            help="Fake mode is fast and UI-safe. Real mode uses full SimPy simulation (slower, accurate)."
          >
            <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={mode === "real"}
                onChange={(e) => setMode(e.target.checked ? "real" : "fake")}
                style={{ marginRight: 4 }}
              />
              Use Real Simulation (slower, accurate)
            </label>
            {mode === "fake" && (
              <Tag color="green" style={{ marginTop: 8 }}>Fast Mode (UI-safe)</Tag>
            )}
            {mode === "real" && (
              <Tag color="blue" style={{ marginTop: 8 }}>Real Mode (Full SimPy)</Tag>
            )}
          </Form.Item>

          <Divider orientation="left">Stations Configuration</Divider>
          
          <div style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {stations.map((station, index) => (
                <Card 
                  key={index} 
                  size="small"
                  extra={
                    stations.length > 1 && (
                      <Button 
                        type="text" 
                        danger 
                        size="small"
                        onClick={() => removeStation(index)}
                      >
                        Remove
                      </Button>
                    )
                  }
                >
                  <Row gutter={16}>
                    <Col span={8}>
                      <strong>ID:</strong> {station.station_id}
                    </Col>
                    <Col span={8}>
                      <strong>Lat:</strong> {station.lat.toFixed(4)}
                    </Col>
                    <Col span={8}>
                      <strong>Lon:</strong> {station.lon.toFixed(4)}
                    </Col>
                  </Row>
                  <Row gutter={16} style={{ marginTop: 8 }}>
                    <Col span={8}>
                      <Tag color="blue">{station.zone_id}</Tag>
                    </Col>
                    <Col span={8}>
                      <strong>Chargers:</strong> {station.chargers_total}
                    </Col>
                    <Col span={8}>
                      <strong>Active:</strong> {station.chargers_active}
                    </Col>
                  </Row>
                </Card>
              ))}
            </Space>
            <Button 
              type="dashed" 
              icon={<PlusOutlined />} 
              onClick={addStation}
              style={{ width: '100%', marginTop: 16 }}
            >
              Add Station
            </Button>
          </div>

          <Form.Item
            label="Interventions (JSON, optional)"
            name="interventions"
          >
            <TextArea 
              rows={6}
              placeholder={`{\n  "add_stations": [...],\n  "modify_chargers": {...}\n}`}
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              icon={<SendOutlined />}
              size="large"
              block
            >
              Submit Scenario
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default ScenarioSubmission
