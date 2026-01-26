import React, { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Alert,
  Spin,
  Typography,
  Divider,
  Tag,
  Empty
} from 'antd'
import { 
  ClockCircleOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { simulationAPI } from '../services/api'

const { Title, Text, Paragraph } = Typography

function ResultsDashboard() {
  const { runId } = useParams()
  const [searchParams] = useSearchParams()
  const runIdFromParams = runId || searchParams.get('runId')
  
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (runIdFromParams) {
      fetchResults()
    }
  }, [runIdFromParams])

  const fetchResults = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await simulationAPI.getJobResult(runIdFromParams)
      setResult(data)
    } catch (err) {
      if (err.response?.status === 202) {
        setError('Simulation is still running. Please wait...')
        // Retry after 3 seconds
        setTimeout(fetchResults, 3000)
      } else {
        setError(err.response?.data?.detail || err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  if (!runIdFromParams) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Card>
          <Empty description="No run ID provided. Please submit a scenario or select a job from the monitor." />
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
        <Paragraph style={{ marginTop: 16 }}>Loading results...</Paragraph>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Alert
          message="Error Loading Results"
          description={error}
          type="warning"
          showIcon
        />
      </div>
    )
  }

  if (!result) {
    return null
  }

  const { summary } = result

  // Generate mock timeseries data for charts (replace with real data when available)
  const timeseriesData = Array.from({ length: 20 }, (_, i) => ({
    time: i * 3,
    wait_time: 5 + Math.random() * 10,
    utilization: 0.4 + Math.random() * 0.3
  }))

  const stationData = [
    { name: 'Station 1', swaps: 45, lost: 5 },
    { name: 'Station 2', swaps: 38, lost: 3 },
    { name: 'Station 3', swaps: 52, lost: 7 },
    { name: 'Station 4', swaps: 41, lost: 4 }
  ]

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>📈 Simulation Results</Title>
            <Text type="secondary">Run ID: <Text code>{runIdFromParams.substring(0, 8)}...</Text></Text>
          </div>
          <Tag color="success" icon={<CheckCircleOutlined />}>COMPLETED</Tag>
        </div>
      </Card>

      {/* KPI Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Wait Time"
              value={summary.avg_wait_time?.toFixed(2) || 0}
              suffix="min"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: summary.avg_wait_time > 10 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Lost Swaps"
              value={summary.lost_swaps || 0}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Charger Utilization"
              value={(summary.charger_utilization * 100)?.toFixed(1) || 0}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="City Throughput"
              value={summary.city_throughput || 0}
              suffix="swaps"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Idle Inventory"
              value={summary.idle_inventory?.toFixed(1) || 0}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Cost Impact"
              value={summary.total_cost_impact?.toFixed(2) || 0}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="ROI"
              value={(summary.roi * 100)?.toFixed(1) || 0}
              suffix="%"
              valueStyle={{ color: summary.roi > 0.2 ? '#3f8600' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Events Logged"
              value={result.events_count || 0}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Wait Time Over Time">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeseriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" label={{ value: 'Time (min)', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Wait Time (min)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="wait_time" stroke="#8884d8" name="Wait Time" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Charger Utilization Over Time">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={timeseriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" label={{ value: 'Time (min)', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Utilization', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="utilization" stroke="#82ca9d" name="Utilization" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24}>
          <Card title="Station Performance">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stationData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="swaps" fill="#52c41a" name="Completed Swaps" />
                <Bar dataKey="lost" fill="#ff4d4f" name="Lost Swaps" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Artifacts Information */}
      <Card style={{ marginTop: 24 }}>
        <Title level={4}>📁 Simulation Artifacts</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Text strong>Events:</Text> <Text code>{result.artifacts.events}</Text>
          </Col>
          <Col xs={24} md={8}>
            <Text strong>Frames:</Text> <Text code>{result.artifacts.frames}</Text>
          </Col>
          <Col xs={24} md={8}>
            <Text strong>Summary:</Text> <Text code>{result.artifacts.summary}</Text>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default ResultsDashboard
